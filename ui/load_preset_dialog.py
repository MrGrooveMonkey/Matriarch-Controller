"""
Load Preset Dialog for Matriarch Controller.
Provides a custom load dialog with recent presets and verification.
"""

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QFileDialog, QLabel, QProgressDialog, QMessageBox,
                             QListWidget, QListWidgetItem, QGroupBox)
from PyQt5.QtCore import Qt
from pathlib import Path
from typing import Optional, Dict
from data.parameter_definitions import PARAMETERS


class LoadPresetDialog:
    """Custom load preset dialog with recent presets"""
    
    def __init__(self, parent, preset_manager, midi_handler, settings, default_dir: str):
        """
        Initialize load preset dialog
        
        Args:
            parent: Parent widget
            preset_manager: PresetManager instance
            midi_handler: MIDIHandler instance
            settings: AppSettings instance
            default_dir: Default directory for loading
        """
        self.parent = parent
        self.preset_manager = preset_manager
        self.midi_handler = midi_handler
        self.settings = settings
        self.default_dir = default_dir
    
    def show(self):
        """
        Show load preset dialog
        
        Returns:
            Tuple of (success: bool, filepath: str or None, parameters: dict or None)
        """
        # Check MIDI connection
        if not self.midi_handler.is_connected:
            QMessageBox.warning(
                self.parent,
                "MIDI Not Connected",
                "Please connect to the Matriarch before loading a preset."
            )
            return False, None, None
        
        # Validate recent presets (remove non-existent files)
        self.settings.validate_recent_presets()
        recent_presets = self.settings.get_recent_presets()
        
        # Create dialog
        dialog = QDialog(self.parent)
        dialog.setWindowTitle("Load Preset")
        dialog.setModal(True)
        dialog.resize(600, 400)
        
        layout = QVBoxLayout()
        
        # Recent presets section
        if recent_presets:
            recent_group = QGroupBox("Recent Presets")
            recent_layout = QVBoxLayout()
            
            recent_list = QListWidget()
            recent_list.setToolTip("Double-click to load preset")
            
            for preset_path in recent_presets:
                if Path(preset_path).exists():
                    display_name = self.preset_manager.get_preset_display_name(preset_path)
                    item = QListWidgetItem(display_name)
                    item.setData(Qt.UserRole, preset_path)  # Store full path
                    recent_list.addItem(item)
            
            recent_layout.addWidget(recent_list)
            recent_group.setLayout(recent_layout)
            layout.addWidget(recent_group)
            
            # Double-click to load
            selected_from_recent = [None]  # Use list to allow modification in nested function
            
            def on_recent_double_click(item):
                selected_from_recent[0] = item.data(Qt.UserRole)
                dialog.accept()
            
            recent_list.itemDoubleClicked.connect(on_recent_double_click)
        
        # Browse button
        browse_button = QPushButton("Browse for Preset File...")
        browse_button.setToolTip("Open file browser to select a preset")
        layout.addWidget(browse_button)
        
        selected_from_browse = [None]  # Use list to allow modification in nested function
        
        def on_browse():
            filepath, _ = QFileDialog.getOpenFileName(
                dialog,
                "Load Preset",
                self.default_dir,
                f"Matriarch Presets (*{self.preset_manager.PRESET_EXTENSION})"
            )
            if filepath:
                selected_from_browse[0] = filepath
                dialog.accept()
        
        browse_button.clicked.connect(on_browse)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        if recent_presets:
            load_button = QPushButton("Load Selected")
            load_button.setToolTip("Load the selected recent preset")
            
            def on_load_selected():
                if recent_list.currentItem():
                    selected_from_recent[0] = recent_list.currentItem().data(Qt.UserRole)
                    dialog.accept()
                else:
                    QMessageBox.warning(dialog, "No Selection", "Please select a preset from the list.")
            
            load_button.clicked.connect(on_load_selected)
            button_layout.addWidget(load_button)
        
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(dialog.reject)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)
        dialog.setLayout(layout)
        
        # Show dialog
        if dialog.exec_() != QDialog.Accepted:
            return False, None, None
        
        # Determine which file was selected
        filepath = selected_from_recent[0] or selected_from_browse[0]
        
        if not filepath:
            return False, None, None
        
        # Load and apply preset
        return self._load_and_apply_preset(filepath)
    
    def _load_and_apply_preset(self, filepath: str):
        """
        Load preset file and apply to Matriarch
        
        Args:
            filepath: Full path to preset file
            
        Returns:
            Tuple of (success: bool, filepath: str or None, parameters: dict or None)
        """
        # Load preset file
        preset_data = self.preset_manager.load_preset(filepath)
        
        if preset_data is None:
            QMessageBox.critical(
                self.parent,
                "Load Failed",
                f"Failed to load preset from:\n{filepath}\n\n"
                "The file may be corrupted or in an invalid format."
            )
            return False, None, None
        
        parameters = preset_data["parameters"]
        parameter_types = preset_data.get("parameter_types", {})
        
        # Validate parameters
        validation = self.preset_manager.validate_preset_parameters(parameters, parameter_types)
        
        # Handle missing SysEx parameters (critical)
        if validation["missing_sysex"]:
            missing_names = [PARAMETERS[pid].name for pid in validation["missing_sysex"] if pid in PARAMETERS]
            # Build warning message
            warning_parts = []
            warning_parts.append(f"This preset is missing {len(validation['missing_sysex'])} SysEx parameters:\n")
            warning_parts.append(f"{', '.join(missing_names[:5])}")
            if len(missing_names) > 5:
                warning_parts.append("...")
            
            # Add CC parameter info if missing
            if validation["missing_cc"]:
                missing_cc_names = [PARAMETERS[pid].name for pid in validation["missing_cc"][:3] if pid in PARAMETERS]
                warning_parts.append(f"\n\nAlso missing {len(validation['missing_cc'])} CC parameters:")
                warning_parts.append(f"{', '.join(missing_cc_names)}")
                if len(validation["missing_cc"]) > 3:
                    warning_parts.append(f"... and {len(validation['missing_cc']) - 3} more")
                warning_parts.append("\n(CC parameters are optional)")
            
            response = QMessageBox.warning(
                self.parent,
                "Incomplete Preset",
                "".join(warning_parts) + "\n\nDo you want to load the preset anyway?\n"
                "Missing parameters will not be changed.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if response != QMessageBox.Yes:
                return False, None, None
        
        # Separate parameters by type for sending
        # Don't send cc_inactive parameters
        params_to_send = {
            pid: value for pid, value in parameters.items()
            if parameter_types.get(pid) != 'cc_inactive'
        }
        
        # Send parameters to Matriarch
        success = self._send_parameters(params_to_send)
        
        if not success:
            return False, None, None
        
        # Verify parameters
        verify_success = self._verify_parameters(parameters, parameter_types)
        
        if verify_success:
            # Add to recent presets
            self.settings.add_recent_preset(filepath)
            
            QMessageBox.information(
                self.parent,
                "Preset Loaded",
                f"Preset loaded successfully from:\n{filepath}"
            )
            return True, filepath, parameters
        else:
            # Verification failed, but parameters were sent
            # User already had option to retry in _verify_parameters
            self.settings.add_recent_preset(filepath)
            return True, filepath, parameters
    
    def _send_parameters(self, parameters: Dict[int, int]) -> bool:
        """
        Send parameters to Matriarch with progress dialog
        
        Args:
            parameters: Dictionary of parameter_id: value
            
        Returns:
            True if successful, False otherwise
        """
        # Create progress dialog
        progress = QProgressDialog(
            "Loading preset to Matriarch...",
            None,  # No cancel button
            0, len(parameters),
            self.parent
        )
        progress.setWindowTitle("Loading Preset")
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(0)
        progress.setValue(0)
        
        # Progress callback
        def update_progress(current, total):
            progress.setValue(current)
            progress.setLabelText(f"Loading preset to Matriarch...\n{current} of {total} parameters")
        
        # Send parameters
        try:
            self.midi_handler.load_preset_parameters(
                parameters,
                progress_callback=update_progress
            )
            
            progress.close()
            return True
            
        except Exception as e:
            progress.close()
            QMessageBox.critical(
                self.parent,
                "Load Error",
                f"Error loading preset to Matriarch:\n{str(e)}"
            )
            return False
    
    def _verify_parameters(self, parameters: Dict[int, int], parameter_types: Dict[int, str] = None) -> bool:
        """
        Verify parameters were loaded correctly, with retry option
        
        Args:
            parameters: Dictionary of parameter_id: value that were sent
            
        Returns:
            True if verification successful or user skipped, False if failed
        """
        # Create progress dialog
        progress = QProgressDialog(
            "Verifying preset...",
            None,  # No cancel button
            0, len(parameters),
            self.parent
        )
        progress.setWindowTitle("Verifying Preset")
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(0)
        progress.setValue(0)
        
        # Progress callback
        def update_progress(current, total):
            progress.setValue(current)
            progress.setLabelText(f"Verifying preset...\n{current} of {total} parameters")
        
        # Verify parameters (only SysEx params, CC params can't be verified)
        try:
            result = self.midi_handler.verify_preset_loaded(
                parameters,
                parameter_types=parameter_types,
                progress_callback=update_progress
            )
            
            progress.close()
            
            if result["success"]:
                return True
            else:
                # Show failure details
                failed_names = []
                for param_id in result["failed_params"][:10]:  # Show first 10
                    if param_id in PARAMETERS:
                        param_name = PARAMETERS[param_id].name
                        expected = result["failures"][param_id]["expected"]
                        actual = result["failures"][param_id]["actual"]
                        failed_names.append(f"  • {param_name}: expected {expected}, got {actual}")
                
                failure_text = "\n".join(failed_names)
                if len(result["failed_params"]) > 10:
                    failure_text += f"\n  ... and {len(result['failed_params']) - 10} more"
                
                response = QMessageBox.warning(
                    self.parent,
                    "Verification Failed",
                    f"{len(result['failed_params'])} parameter(s) did not load correctly:\n\n"
                    f"{failure_text}\n\n"
                    f"Would you like to retry loading the failed parameters?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.Yes
                )
                
                if response == QMessageBox.Yes:
                    # Retry failed parameters
                    failed_params = {
                        pid: parameters[pid] 
                        for pid in result["failed_params"]
                    }
                    return self._retry_failed_parameters(failed_params, parameter_types)
                else:
                    return False
            
        except Exception as e:
            progress.close()
            QMessageBox.critical(
                self.parent,
                "Verification Error",
                f"Error verifying preset:\n{str(e)}"
            )
            return False
    
    def _retry_failed_parameters(self, failed_params: Dict[int, int], parameter_types: Dict[int, str] = None) -> bool:
        """
        Retry sending failed parameters
        
        Args:
            failed_params: Dictionary of failed parameter_id: value
            
        Returns:
            True if retry successful, False otherwise
        """
        send_success = self._send_parameters(failed_params)
        if not send_success:
            return False
        
        # Verify again
        progress = QProgressDialog(
            "Re-verifying parameters...",
            None,
            0, len(failed_params),
            self.parent
        )
        progress.setWindowTitle("Re-verifying")
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(0)
        progress.setValue(0)
        
        def update_progress(current, total):
            progress.setValue(current)
        
        try:
            # Only verify SysEx params in retry
            result = self.midi_handler.verify_preset_loaded(
                failed_params,
                parameter_types=parameter_types,
                progress_callback=update_progress
            )
            
            progress.close()
            
            if result["success"]:
                QMessageBox.information(
                    self.parent,
                    "Retry Successful",
                    "All parameters verified successfully after retry."
                )
                return True
            else:
                QMessageBox.warning(
                    self.parent,
                    "Retry Failed",
                    f"{len(result['failed_params'])} parameter(s) still failed after retry.\n\n"
                    f"The preset has been loaded but some parameters may not be correct."
                )
                return False
                
        except Exception as e:
            progress.close()
            QMessageBox.critical(
                self.parent,
                "Re-verification Error",
                f"Error re-verifying parameters:\n{str(e)}"
            )
            return False