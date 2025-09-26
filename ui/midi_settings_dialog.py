"""
MIDI Settings Dialog for port selection and configuration
"""

import logging
from typing import Dict, List, Optional
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, 
    QComboBox, QSpinBox, QPushButton, QGroupBox, QMessageBox,
    QDialogButtonBox, QProgressBar, QTextEdit, QCheckBox
)
from PyQt5.QtCore import Qt, QSettings, QTimer, pyqtSignal
from PyQt5.QtGui import QFont

from midi.connection import MIDIConnectionManager

logger = logging.getLogger(__name__)

class MIDISettingsDialog(QDialog):
    """Dialog for MIDI port selection and settings"""
    
    def __init__(self, midi_manager: MIDIConnectionManager, parent=None):
        super().__init__(parent)
        self.midi_manager = midi_manager
        self.settings = QSettings()
        
        # UI components
        self.input_combo: Optional[QComboBox] = None
        self.output_combo: Optional[QComboBox] = None
        self.unit_id_spin: Optional[QSpinBox] = None
        self.midi_channel_spin: Optional[QSpinBox] = None
        self.query_delay_spin: Optional[QSpinBox] = None
        self.test_button: Optional[QPushButton] = None
        self.refresh_button: Optional[QPushButton] = None
        self.connection_status: Optional[QLabel] = None
        
        self.available_ports = {'inputs': [], 'outputs': []}
        
        self.init_ui()
        self.load_settings()
        self.refresh_ports()
    
    def init_ui(self):
        """Initialize the dialog UI"""
        self.setWindowTitle("MIDI Settings")
        self.setModal(True)
        self.resize(500, 400)
        
        layout = QVBoxLayout(self)
        
        # Port Selection Group
        port_group = QGroupBox("MIDI Ports")
        port_layout = QFormLayout(port_group)
        
        # Input port selection
        input_layout = QHBoxLayout()
        self.input_combo = QComboBox()
        self.input_combo.setMinimumWidth(250)
        input_layout.addWidget(self.input_combo)
        
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.refresh_ports)
        input_layout.addWidget(self.refresh_button)
        
        port_layout.addRow("Input Port:", input_layout)
        
        # Output port selection
        self.output_combo = QComboBox()
        self.output_combo.setMinimumWidth(250)
        port_layout.addRow("Output Port:", self.output_combo)
        
        layout.addWidget(port_group)
        
        # MIDI Configuration Group
        config_group = QGroupBox("MIDI Configuration")
        config_layout = QFormLayout(config_group)
        
        # Unit ID
        self.unit_id_spin = QSpinBox()
        self.unit_id_spin.setRange(0, 15)
        self.unit_id_spin.setValue(0)
        self.unit_id_spin.setToolTip("MIDI Unit ID for SysEx communication (usually 0)")
        config_layout.addRow("Unit ID:", self.unit_id_spin)
        
        # MIDI Channel
        self.midi_channel_spin = QSpinBox()
        self.midi_channel_spin.setRange(1, 16)
        self.midi_channel_spin.setValue(1)
        self.midi_channel_spin.setToolTip("MIDI Channel (1-16)")
        config_layout.addRow("MIDI Channel:", self.midi_channel_spin)
        
        # Query delay
        query_layout = QHBoxLayout()
        self.query_delay_spin = QSpinBox()
        self.query_delay_spin.setRange(100, 5000)
        self.query_delay_spin.setValue(400)
        self.query_delay_spin.setSuffix(" ms")
        self.query_delay_spin.setToolTip("Delay between parameter queries (adjust if communication is unreliable)")
        query_layout.addWidget(self.query_delay_spin)
        
        query_help = QLabel("(Increase if queries fail)")
        query_help.setStyleSheet("color: #888888; font-size: 10px;")
        query_layout.addWidget(query_help)
        query_layout.addStretch()
        
        config_layout.addRow("Query Delay:", query_layout)
        
        # Auto-reconnect options
        auto_reconnect_layout = QHBoxLayout()
        self.auto_reconnect_check = QCheckBox("Auto-reconnect on startup")
        self.auto_reconnect_check.setToolTip("Automatically reconnect to these MIDI ports when the application starts")
        auto_reconnect_layout.addWidget(self.auto_reconnect_check)
        
        self.auto_query_check = QCheckBox("Auto-query parameters on connect")
        self.auto_query_check.setToolTip("Automatically query all parameters when connection is established")
        auto_reconnect_layout.addWidget(self.auto_query_check)
        auto_reconnect_layout.addStretch()
        
        config_layout.addRow("Startup:", auto_reconnect_layout)
        
        layout.addWidget(config_group)
        
        # Connection Test Group
        test_group = QGroupBox("Connection Test")
        test_layout = QVBoxLayout(test_group)
        
        # Test button and status
        test_button_layout = QHBoxLayout()
        self.test_button = QPushButton("Test Connection")
        self.test_button.clicked.connect(self.test_connection)
        test_button_layout.addWidget(self.test_button)
        
        self.connection_status = QLabel("Not tested")
        self.connection_status.setStyleSheet("color: #888888;")
        test_button_layout.addWidget(self.connection_status)
        test_button_layout.addStretch()
        
        test_layout.addLayout(test_button_layout)
        
        # Test results area
        self.test_results = QTextEdit()
        self.test_results.setMaximumHeight(100)
        self.test_results.setReadOnly(True)
        self.test_results.setStyleSheet("""
            QTextEdit {
                background-color: #2a2a2a;
                border: 1px solid #555555;
                font-family: monospace;
                font-size: 10px;
                color: #ffffff;
            }
        """)
        test_layout.addWidget(self.test_results)
        
        layout.addWidget(test_group)
        
        # Button box
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel | QDialogButtonBox.Apply,
            Qt.Horizontal
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        button_box.button(QDialogButtonBox.Apply).clicked.connect(self.apply_settings)
        layout.addWidget(button_box)
        
        # Apply dark theme
        self.apply_theme()
    
    def apply_theme(self):
        """Apply dark theme to dialog"""
        self.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #666666;
                border-radius: 5px;
                margin: 5px 0px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #ff6b35;
            }
            QLabel {
                color: #ffffff;
            }
            QComboBox {
                background-color: #4a4a4a;
                border: 1px solid #666666;
                padding: 4px;
                border-radius: 3px;
                color: #ffffff;
                min-height: 20px;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 4px solid #ffffff;
            }
            QComboBox QAbstractItemView {
                background-color: #3c3c3c;
                border: 1px solid #666666;
                selection-background-color: #ff6b35;
                color: #ffffff;
            }
            QSpinBox {
                background-color: #4a4a4a;
                border: 1px solid #666666;
                padding: 4px;
                border-radius: 3px;
                color: #ffffff;
                min-height: 20px;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                background-color: #5a5a5a;
                border: 1px solid #666666;
                width: 16px;
            }
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {
                background-color: #6a6a6a;
            }
            QPushButton {
                background-color: #4a4a4a;
                color: #ffffff;
                border: 1px solid #666666;
                padding: 6px 16px;
                border-radius: 3px;
                min-height: 20px;
            }
            QPushButton:hover {
                background-color: #5a5a5a;
                border-color: #777777;
            }
            QPushButton:pressed {
                background-color: #ff6b35;
            }
            QDialogButtonBox QPushButton {
                min-width: 80px;
            }
        """)
    
    def refresh_ports(self):
        """Refresh available MIDI ports"""
        self.test_results.append("Scanning MIDI ports...")
        
        try:
            self.available_ports = self.midi_manager.get_available_ports()
            
            # Update input combo
            current_input = self.input_combo.currentText()
            self.input_combo.clear()
            self.input_combo.addItem("-- Select Input Port --", None)
            
            for port in self.available_ports['inputs']:
                self.input_combo.addItem(port, port)
            
            # Restore selection if still available
            input_index = self.input_combo.findText(current_input)
            if input_index >= 0:
                self.input_combo.setCurrentIndex(input_index)
            
            # Update output combo
            current_output = self.output_combo.currentText()
            self.output_combo.clear()
            self.output_combo.addItem("-- Select Output Port --", None)
            
            for port in self.available_ports['outputs']:
                self.output_combo.addItem(port, port)
            
            # Restore selection if still available
            output_index = self.output_combo.findText(current_output)
            if output_index >= 0:
                self.output_combo.setCurrentIndex(output_index)
            
            # Update test results
            input_count = len(self.available_ports['inputs'])
            output_count = len(self.available_ports['outputs'])
            self.test_results.append(f"Found {input_count} input ports, {output_count} output ports")
            
            if input_count == 0 or output_count == 0:
                self.test_results.append("WARNING: No MIDI ports found. Check your MIDI setup.")
            
        except Exception as e:
            logger.error(f"Error scanning MIDI ports: {e}")
            self.test_results.append(f"ERROR: Failed to scan ports - {e}")
            QMessageBox.warning(self, "MIDI Error", f"Failed to scan MIDI ports:\n{e}")
    
    def test_connection(self):
        """Test MIDI connection with selected ports"""
        input_port = self.input_combo.currentData()
        output_port = self.output_combo.currentData()
        
        if not input_port or not output_port:
            QMessageBox.warning(self, "Invalid Selection", 
                              "Please select both input and output ports.")
            return
        
        self.test_results.clear()
        self.test_results.append("Testing MIDI connection...")
        self.test_results.append(f"Input:  {input_port}")
        self.test_results.append(f"Output: {output_port}")
        
        self.test_button.setEnabled(False)
        self.connection_status.setText("Testing...")
        self.connection_status.setStyleSheet("color: #ffaa00;")
        
        try:
            # Temporarily update MIDI manager settings
            old_unit_id = self.midi_manager.unit_id
            old_channel = self.midi_manager.midi_channel
            old_delay = self.midi_manager.query_delay
            
            self.midi_manager.update_settings(
                self.unit_id_spin.value(),
                self.midi_channel_spin.value() - 1  # Convert to 0-15
            )
            self.midi_manager.query_delay = self.query_delay_spin.value() / 1000.0
            
            # Test connection
            was_connected = self.midi_manager.is_connected
            if was_connected:
                self.midi_manager.disconnect()
            
            if self.midi_manager.connect(input_port, output_port):
                self.test_results.append("✓ MIDI connection established")
                
                # Test communication
                self.test_results.append("Testing communication...")
                if self.midi_manager.test_connection():
                    self.test_results.append("✓ Communication test PASSED")
                    self.connection_status.setText("✓ Connection OK")
                    self.connection_status.setStyleSheet("color: #00ff00;")
                    
                    # Try querying a few parameters
                    self.test_results.append("Querying sample parameters...")
                    test_params = [0, 10, 37]  # Unit ID, MIDI Channel, Pitch Bend Range
                    
                    for param_id in test_params:
                        try:
                            value = self.midi_manager.query_parameter_sync(param_id)
                            if value is not None:
                                self.test_results.append(f"  Parameter {param_id}: {value}")
                            else:
                                self.test_results.append(f"  Parameter {param_id}: timeout")
                        except Exception as e:
                            self.test_results.append(f"  Parameter {param_id}: error - {e}")
                    
                else:
                    self.test_results.append("✗ Communication test FAILED")
                    self.connection_status.setText("✗ No Response")
                    self.connection_status.setStyleSheet("color: #ff6666;")
                    self.test_results.append("Check:")
                    self.test_results.append("  - Matriarch is powered on")
                    self.test_results.append("  - MIDI cables connected properly")
                    self.test_results.append("  - Matriarch MIDI channel settings")
                
                # Restore previous connection state
                self.midi_manager.disconnect()
                if was_connected:
                    # Try to reconnect with original settings
                    self.midi_manager.update_settings(old_unit_id, old_channel)
                    self.midi_manager.query_delay = old_delay
                    
            else:
                self.test_results.append("✗ Failed to establish MIDI connection")
                self.connection_status.setText("✗ Connection Failed")
                self.connection_status.setStyleSheet("color: #ff6666;")
                self.test_results.append("Check port availability and permissions")
            
        except Exception as e:
            logger.exception("Error during connection test")
            self.test_results.append(f"✗ Test failed: {e}")
            self.connection_status.setText("✗ Test Error")
            self.connection_status.setStyleSheet("color: #ff6666;")
        
        finally:
            self.test_button.setEnabled(True)
    
    def apply_settings(self):
        """Apply current settings without closing dialog"""
        self.save_settings()
        
        # Update MIDI manager settings
        self.midi_manager.update_settings(
            self.unit_id_spin.value(),
            self.midi_channel_spin.value() - 1  # Convert to 0-15
        )
        self.midi_manager.query_delay = self.query_delay_spin.value() / 1000.0
        
        self.test_results.append("Settings applied")
    
    def load_settings(self):
        """Load settings from QSettings"""
        # MIDI ports
        input_port = self.settings.value('midi/input_port', '')
        output_port = self.settings.value('midi/output_port', '')
        
        # Set port selections after ports are loaded
        QTimer.singleShot(100, lambda: self._restore_port_selections(input_port, output_port))
        
        # Configuration
        self.unit_id_spin.setValue(self.settings.value('midi/unit_id', 0, type=int))
        self.midi_channel_spin.setValue(self.settings.value('midi/midi_channel', 1, type=int))
        self.query_delay_spin.setValue(self.settings.value('midi/query_delay', 400, type=int))
        
        # Auto-reconnect options
        self.auto_reconnect_check.setChecked(self.settings.value('midi/auto_reconnect', False, type=bool))
        self.auto_query_check.setChecked(self.settings.value('midi/auto_query_on_connect', True, type=bool))
    
    def _restore_port_selections(self, input_port: str, output_port: str):
        """Restore port selections after combo boxes are populated"""
        if input_port:
            input_index = self.input_combo.findText(input_port)
            if input_index >= 0:
                self.input_combo.setCurrentIndex(input_index)
        
        if output_port:
            output_index = self.output_combo.findText(output_port)
            if output_index >= 0:
                self.output_combo.setCurrentIndex(output_index)
    
    def save_settings(self):
        """Save settings to QSettings"""
        # MIDI ports
        input_port = self.input_combo.currentData()
        output_port = self.output_combo.currentData()
        
        if input_port:
            self.settings.setValue('midi/input_port', input_port)
        if output_port:
            self.settings.setValue('midi/output_port', output_port)
        
        # Configuration
        self.settings.setValue('midi/unit_id', self.unit_id_spin.value())
        self.settings.setValue('midi/midi_channel', self.midi_channel_spin.value())
        self.settings.setValue('midi/query_delay', self.query_delay_spin.value())
        
        # Auto-reconnect options
        self.settings.setValue('midi/auto_reconnect', self.auto_reconnect_check.isChecked())
        self.settings.setValue('midi/auto_query_on_connect', self.auto_query_check.isChecked())
    
    def accept(self):
        """Handle OK button click"""
        input_port = self.input_combo.currentData()
        output_port = self.output_combo.currentData()
        
        if not input_port or not output_port:
            reply = QMessageBox.question(
                self, "Incomplete Settings",
                "MIDI ports are not selected. Continue anyway?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.No:
                return
        
        self.save_settings()
        super().accept()
    
    def get_selected_ports(self) -> tuple:
        """Get currently selected ports"""
        return (self.input_combo.currentData(), self.output_combo.currentData())
    
    def get_midi_settings(self) -> Dict:
        """Get current MIDI settings as dictionary"""
        return {
            'input_port': self.input_combo.currentData(),
            'output_port': self.output_combo.currentData(),
            'unit_id': self.unit_id_spin.value(),
            'midi_channel': self.midi_channel_spin.value() - 1,  # Convert to 0-15
            'query_delay': self.query_delay_spin.value() / 1000.0  # Convert to seconds
        }