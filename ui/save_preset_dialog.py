"""
Save Preset Dialog for Matriarch Controller.
Provides a custom save dialog with query option.
"""

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QCheckBox, 
                             QPushButton, QFileDialog, QLabel, QProgressDialog,
                             QMessageBox)
from PyQt5.QtCore import Qt, QTimer
from pathlib import Path


class SavePresetDialog:
    """Custom save preset dialog with query option"""
    
    def __init__(self, parent, preset_manager, midi_handler, default_dir: str):
        """
        Initialize save preset dialog
        
        Args:
            parent: Parent widget
            preset_manager: PresetManager instance
            midi_handler: MIDIHandler instance
            default_dir: Default directory for saving
        """
        self.parent = parent
        self.preset_manager = preset_manager
        self.midi_handler = midi_handler
        self.default_dir = default_dir
    
    def show(self, current_parameters: dict = None):
        """
        Show save preset dialog
        
        Args:
            current_parameters: Current UI parameter values (used if not querying)
            
        Returns:
            Tuple of (success: bool, filepath: str or None)
        """
        # Check MIDI connection
        if not self.midi_handler.is_connected:
            QMessageBox.warning(
                self.parent,
                "MIDI Not Connected",
                "Please connect to the Matriarch before saving a preset."
            )
            return False, None
        
        # Create options dialog
        options_dialog = QDialog(self.parent)
        options_dialog.setWindowTitle("Save Preset Options")
        options_dialog.setModal(True)
        
        layout = QVBoxLayout()
        
        # Query checkbox
        query_checkbox = QCheckBox("Query Matriarch before saving")
        query_checkbox.setChecked(True)
        query_checkbox.setToolTip(
            "Query all parameters from the Matriarch to ensure accuracy.\n"
            "Uncheck to save based on current UI values (faster)."
        )
        layout.addWidget(query_checkbox)
        
        # Info label
        info_label = QLabel(
            "You will be prompted to choose a location and filename after clicking OK."
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        ok_button = QPushButton("OK")
        cancel_button = QPushButton("Cancel")
        button_layout.addStretch()
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)
        
        options_dialog.setLayout(layout)
        
        # Connect buttons
        ok_button.clicked.connect(options_dialog.accept)
        cancel_button.clicked.connect(options_dialog.reject)
        
        # Show dialog
        if options_dialog.exec_() != QDialog.Accepted:
            return False, None
        
        # Get parameters
        should_query = query_checkbox.isChecked()
        
        if should_query:
            parameters = self._query_parameters()
            if parameters is None:
                return False, None
        else:
            if current_parameters is None:
                QMessageBox.warning(
                    self.parent,
                    "No Parameters",
                    "No current parameters available to save."
                )
                return False, None
            parameters = current_parameters
        
        # Show file save dialog
        filepath, _ = QFileDialog.getSaveFileName(
            self.parent,
            "Save Preset As",
            self.default_dir,
            f"Matriarch Presets (*{self.preset_manager.PRESET_EXTENSION})"
        )
        
        if not filepath:
            return False, None
        
        # Save preset
        success = self.preset_manager.save_preset(filepath, parameters)
        
        if success:
            QMessageBox.information(
                self.parent,
                "Preset Saved",
                f"Preset saved successfully to:\n{filepath}"
            )
            return True, filepath
        else:
            QMessageBox.critical(
                self.parent,
                "Save Failed",
                f"Failed to save preset to:\n{filepath}\n\nCheck file permissions and try again."
            )
            return False, None
    
    def _query_parameters(self):
        """
        Query parameters from Matriarch with progress dialog
        
        Returns:
            Dictionary of parameter values, or None if failed/cancelled
        """
        # Create progress dialog
        progress = QProgressDialog(
            "Querying parameters from Matriarch...",
            None,  # No cancel button
            0, 75,  # 0-75 parameters (excluding 76)
            self.parent
        )
        progress.setWindowTitle("Querying Matriarch")
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(0)
        progress.setValue(0)
        
        # Progress callback
        def update_progress(current, total):
            progress.setValue(current)
            progress.setLabelText(f"Querying parameters from Matriarch...\n{current} of {total}")
        
        # Query parameters
        try:
            parameters = self.midi_handler.query_parameters_for_save(
                progress_callback=update_progress
            )
            
            progress.close()
            
            # Check if we got all parameters
            expected_count = 75  # 0-75 excluding 76
            actual_count = len(parameters)
            
            if actual_count < expected_count:
                response = QMessageBox.warning(
                    self.parent,
                    "Incomplete Query",
                    f"Only {actual_count} of {expected_count} parameters were successfully queried.\n\n"
                    f"Do you want to save the preset with incomplete data?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                
                if response != QMessageBox.Yes:
                    return None
            
            return parameters
            
        except Exception as e:
            progress.close()
            QMessageBox.critical(
                self.parent,
                "Query Error",
                f"Error querying parameters from Matriarch:\n{str(e)}"
            )
            return None