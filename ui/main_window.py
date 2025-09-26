"""
Main Window for Matriarch Controller
"""

import sys
import logging
from typing import Dict, Any, Optional, List
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QTabWidget, QVBoxLayout, QHBoxLayout, 
    QMenuBar, QMenu, QAction, QStatusBar, QMessageBox, QProgressBar,
    QLabel, QDialog, QDialogButtonBox, QComboBox, QSpinBox, QGroupBox,
    QApplication, QPushButton, QTextEdit
)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal, QSettings
from PyQt5.QtGui import QIcon, QFont

from midi.connection import MIDIConnectionManager
from data.parameter_definitions import (
    ParameterCategory, get_parameters_by_category, get_parameter_by_id,
    get_all_parameter_defaults, Parameter
)
from ui.parameter_widgets import ParameterWidget, ParameterWidgetFactory
from ui.midi_settings_dialog import MIDISettingsDialog
from ui.midi_log_window import MIDILogWindow

logger = logging.getLogger(__name__)

class ParameterQueryWorker(QThread):
    """Worker thread for querying all parameters without blocking UI"""
    
    progress_updated = pyqtSignal(int, int)  # current, total
    parameter_received = pyqtSignal(int, int)  # param_id, value
    query_completed = pyqtSignal(dict)  # results
    error_occurred = pyqtSignal(str)  # error message
    
    def __init__(self, midi_manager: MIDIConnectionManager, parameter_ids: List[int]):
        super().__init__()
        self.midi_manager = midi_manager
        self.parameter_ids = parameter_ids
        self.results = {}
        
    def run(self):
        """Query all parameters in background thread"""
        try:
            self.results = self.midi_manager.query_all_parameters(
                self.parameter_ids,
                progress_callback=self.progress_updated.emit
            )
            self.query_completed.emit(self.results)
        except Exception as e:
            logger.exception("Error in parameter query worker")
            self.error_occurred.emit(str(e))

class MatriarchMainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.midi_manager = MIDIConnectionManager()
        self.parameter_widgets: Dict[int, ParameterWidget] = {}
        self.current_values: Dict[int, int] = {}
        self.settings = QSettings()
        
        # UI Components
        self.central_widget: Optional[QWidget] = None
        self.tab_widget: Optional[QTabWidget] = None
        self.status_bar: Optional[QStatusBar] = None
        self.progress_bar: Optional[QProgressBar] = None
        self.connection_label: Optional[QLabel] = None
        
        # Dialogs
        self.midi_settings_dialog: Optional[MIDISettingsDialog] = None
        self.midi_log_window: Optional[MIDILogWindow] = None
        
        # Worker thread
        self.query_worker: Optional[ParameterQueryWorker] = None
        self.last_failed_parameters: List[int] = []  # Track failed parameters for retry
        
        # Setup
        self.init_ui()
        self.setup_midi_callbacks()
        self.load_settings()
        # Auto-reconnect if enabled and ports are available
        self.attempt_auto_reconnect()
        self.setup_periodic_updates()
        
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Matriarch Controller v1.0")
        self.setMinimumSize(1000, 700)
        self.resize(1200, 800)
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create central widget with tabs
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(self.central_widget)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.North)
        self.tab_widget.setUsesScrollButtons(True)  # Enable scroll buttons for many tabs
        main_layout.addWidget(self.tab_widget)
        
        # Create parameter tabs
        self.create_parameter_tabs()
        
        # Create status bar
        self.create_status_bar()
        
        # Apply dark theme
        self.apply_dark_theme()
        
    def create_menu_bar(self):
        """Create application menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('&File')
        
        query_action = QAction('&Query All Parameters', self)
        query_action.setShortcut('Ctrl+Q')
        query_action.setStatusTip('Query all parameters from Matriarch')
        query_action.triggered.connect(self.query_all_parameters)
        file_menu.addAction(query_action)
        
        retry_action = QAction('&Retry Failed Parameters', self)
        retry_action.setShortcut('Ctrl+R')
        retry_action.setStatusTip('Retry previously failed parameter queries')
        retry_action.triggered.connect(self.retry_last_failed_parameters)
        file_menu.addAction(retry_action)
        
        file_menu.addSeparator()
        
        # Preset submenu
        preset_menu = file_menu.addMenu('&Presets')
        
        save_preset_action = QAction('&Save Preset...', self)
        save_preset_action.setShortcut('Ctrl+S')
        save_preset_action.triggered.connect(self.save_preset)
        preset_menu.addAction(save_preset_action)
        
        load_preset_action = QAction('&Load Preset...', self)
        load_preset_action.setShortcut('Ctrl+L')
        load_preset_action.triggered.connect(self.load_preset)
        preset_menu.addAction(load_preset_action)
        
        preset_menu.addSeparator()
        
        reset_defaults_action = QAction('&Reset to Defaults', self)
        reset_defaults_action.triggered.connect(self.reset_to_defaults)
        preset_menu.addAction(reset_defaults_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction('E&xit', self)
        exit_action.setShortcut('Ctrl+X')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Connection menu
        connection_menu = menubar.addMenu('&Connection')
        
        midi_settings_action = QAction('&MIDI Settings...', self)
        midi_settings_action.setShortcut('Ctrl+M')
        midi_settings_action.triggered.connect(self.show_midi_settings)
        connection_menu.addAction(midi_settings_action)
        
        connection_menu.addSeparator()
        
        connect_action = QAction('&Connect', self)
        connect_action.triggered.connect(self.connect_midi)
        connection_menu.addAction(connect_action)
        
        disconnect_action = QAction('&Disconnect', self)
        disconnect_action.triggered.connect(self.disconnect_midi)
        connection_menu.addAction(disconnect_action)
        
        # View menu
        view_menu = menubar.addMenu('&View')
        
        midi_log_action = QAction('&MIDI Log...', self)
        midi_log_action.setShortcut('Ctrl+L')
        midi_log_action.triggered.connect(self.show_midi_log)
        view_menu.addAction(midi_log_action)
        
        # Help menu
        help_menu = menubar.addMenu('&Help')
        
        about_action = QAction('&About', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
    def create_parameter_tabs(self):
        """Create tabs for each parameter category"""
        categories = get_parameters_by_category()
        widget_factory = ParameterWidgetFactory()
        
        for category, parameters in categories.items():
            # Create tab
            tab_widget = QWidget()
            self.tab_widget.addTab(tab_widget, category.value)
            
            # Create scroll area for parameters
            from PyQt5.QtWidgets import QScrollArea
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            
            # Create content widget
            content_widget = QWidget()
            layout = QVBoxLayout(content_widget)
            layout.setSpacing(10)
            
            # Group parameters logically within each category
            current_group = None
            group_widget = None
            group_layout = None
            
            for param in parameters:
                # Create parameter widget
                param_widget = widget_factory.create_widget(param)
                param_widget.value_changed.connect(self.on_parameter_changed)
                self.parameter_widgets[param.param_id] = param_widget
                
                # Add to layout
                if group_layout is None:
                    # Create first group
                    group_widget = QGroupBox("Settings")
                    group_layout = QVBoxLayout(group_widget)
                    group_layout.setSpacing(5)
                    layout.addWidget(group_widget)
                
                group_layout.addWidget(param_widget)
            
            # Add stretch to push everything to top
            layout.addStretch()
            
            # Set content widget to scroll area
            scroll.setWidget(content_widget)
            
            # Set tab layout
            tab_layout = QVBoxLayout(tab_widget)
            tab_layout.addWidget(scroll)
    
    def create_status_bar(self):
        """Create status bar with connection info and progress"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Connection status
        self.connection_label = QLabel("Disconnected")
        self.status_bar.addWidget(self.connection_label)
        
        # Progress bar (hidden by default)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.status_bar.addPermanentWidget(self.progress_bar)
        
        # Initial status
        self.update_connection_status()
    
    def apply_dark_theme(self):
        """Apply dark theme similar to Matriarch colors"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QTabWidget::pane {
                border: 1px solid #555555;
                background-color: #3c3c3c;
            }
            QTabWidget::tab-bar {
                alignment: center;
            }
            QTabBar::tab {
                background-color: #4a4a4a;
                color: #ffffff;
                padding: 8px 16px;
                margin: 2px;
                border: 1px solid #666666;
                min-width: 160px;
                max-width: 300px;
            }
            QTabBar::tab:selected {
                background-color: #ff6b35;
                color: #ffffff;
                border: 1px solid #ff6b35;
            }
            QTabBar::tab:hover {
                background-color: #5a5a5a;
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
            QPushButton {
                background-color: #4a4a4a;
                color: #ffffff;
                border: 1px solid #666666;
                padding: 5px 15px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #5a5a5a;
            }
            QPushButton:pressed {
                background-color: #ff6b35;
            }
            QStatusBar {
                background-color: #2b2b2b;
                color: #ffffff;
                border-top: 1px solid #555555;
            }
            QMenuBar {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QMenuBar::item:selected {
                background-color: #ff6b35;
            }
            QMenu {
                background-color: #3c3c3c;
                color: #ffffff;
                border: 1px solid #555555;
            }
            QMenu::item:selected {
                background-color: #ff6b35;
            }
        """)
    
    def setup_midi_callbacks(self):
        """Setup MIDI event callbacks"""
        self.midi_manager.set_callbacks(
            parameter_callback=self.on_parameter_received,
            error_callback=self.on_midi_error,
            midi_log_callback=self.on_midi_log
        )
    
    def setup_periodic_updates(self):
        """Setup periodic UI updates"""
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_connection_status)
        self.update_timer.start(5000)  # Update every 5 seconds
    
    # MIDI Event Handlers
    def on_parameter_received(self, param_id: int, value: int):
        """Handle parameter updates from Matriarch"""
        self.current_values[param_id] = value
        
        if param_id in self.parameter_widgets:
            # Update widget without triggering change signal
            widget = self.parameter_widgets[param_id]
            widget.set_value_silently(value)
            
        logger.debug(f"Parameter {param_id} updated to {value}")
    
    def on_parameter_changed(self, param_id: int, value: int):
        """Handle parameter changes from UI"""
        # Validate parameter
        param = get_parameter_by_id(param_id)
        if param:
            validated_value = param.validate_value(value)
            
            # Send to Matriarch
            if self.midi_manager.set_parameter(param_id, validated_value):
                self.current_values[param_id] = validated_value
                logger.debug(f"Sent parameter {param_id} = {validated_value}")
            else:
                logger.warning(f"Failed to send parameter {param_id} = {validated_value}")
                # Revert widget to previous value
                if param_id in self.current_values:
                    widget = self.parameter_widgets[param_id]
                    widget.set_value_silently(self.current_values[param_id])
    
    def on_midi_error(self, error_message: str):
        """Handle MIDI errors"""
        logger.error(f"MIDI Error: {error_message}")
        QMessageBox.warning(self, "MIDI Error", error_message)
    
    def on_midi_log(self, message: str, is_incoming: bool):
        """Handle MIDI log messages"""
        if self.midi_log_window:
            self.midi_log_window.add_message(message, is_incoming)
    
    # UI Actions
    def query_all_parameters(self):
        """Query all parameters from Matriarch"""
        if not self.midi_manager.is_connected:
            QMessageBox.warning(self, "Not Connected", 
                              "Please connect to Matriarch first.")
            return
        
        # Get all parameter IDs
        from data.parameter_definitions import PARAMETERS
        parameter_ids = list(PARAMETERS.keys())
        
        # Show progress
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, len(parameter_ids))
        self.progress_bar.setValue(0)
        self.status_bar.showMessage("Querying parameters...")
        
        # Start worker thread
        self.query_worker = ParameterQueryWorker(self.midi_manager, parameter_ids)
        self.query_worker.progress_updated.connect(self.on_query_progress)
        self.query_worker.query_completed.connect(self.on_query_completed)
        self.query_worker.error_occurred.connect(self.on_query_error)
        self.query_worker.start()
    
    def on_query_progress(self, current: int, total: int):
        """Handle query progress updates"""
        self.progress_bar.setValue(current)
        self.status_bar.showMessage(f"Querying parameters... {current}/{total}")
    
    def on_query_completed(self, results: Dict[int, Optional[int]]):
        """Handle query completion"""
        self.progress_bar.setVisible(False)
        
        successful = sum(1 for v in results.values() if v is not None)
        total = len(results)
        failed_params = [pid for pid, value in results.items() if value is None]
        
        self.status_bar.showMessage(f"Query completed: {successful}/{total} parameters retrieved", 5000)
        
        # Update UI with successful results
        for param_id, value in results.items():
            if value is not None:
                self.on_parameter_received(param_id, value)
        
        if failed_params:
            # Create detailed error message with parameter names
            failed_details = []
            for param_id in failed_params:
                param = get_parameter_by_id(param_id)
                param_name = param.name if param else f"Unknown Parameter {param_id}"
                failed_details.append(f"  • {param_name} (ID: {param_id})")
            
            failed_list = "\n".join(failed_details)
            
            # Create custom message box with retry option
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("Parameter Query Issues")
            msg.setText(f"Failed to retrieve {len(failed_params)} parameter(s):")
            msg.setDetailedText(f"Failed Parameters:\n{failed_list}\n\n"
                              f"This may indicate:\n"
                              f"• Parameter not supported by this firmware version\n"
                              f"• MIDI communication issues\n"
                              f"• Parameter query timeout\n\n"
                              f"You can retry just the failed parameters or continue with the current values.")
            
            # Add custom buttons
            retry_button = msg.addButton("Retry Failed Only", QMessageBox.ActionRole)
            retry_all_button = msg.addButton("Retry All Parameters", QMessageBox.ActionRole)
            continue_button = msg.addButton("Continue", QMessageBox.AcceptRole)
            
            msg.setDefaultButton(retry_button)
            msg.exec_()
            
            if msg.clickedButton() == retry_button:
                self.retry_failed_parameters(failed_params)
            elif msg.clickedButton() == retry_all_button:
                self.query_all_parameters()
            # Otherwise just continue with current values
        
        # Store failed parameters for potential retry
        self.last_failed_parameters = failed_params if failed_params else []
    
    def retry_failed_parameters(self, failed_param_ids: List[int]):
        """Retry querying only the failed parameters"""
        if not self.midi_manager.is_connected:
            QMessageBox.warning(self, "Not Connected", 
                              "Please connect to Matriarch first.")
            return
        
        if not failed_param_ids:
            QMessageBox.information(self, "No Failed Parameters", 
                                  "No failed parameters to retry.")
            return
        
        # Show progress
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, len(failed_param_ids))
        self.progress_bar.setValue(0)
        self.status_bar.showMessage(f"Retrying {len(failed_param_ids)} failed parameters...")
        
        # Start worker thread for retry
        self.query_worker = ParameterQueryWorker(self.midi_manager, failed_param_ids)
        self.query_worker.progress_updated.connect(self.on_retry_progress)
        self.query_worker.query_completed.connect(self.on_retry_completed)
        self.query_worker.error_occurred.connect(self.on_query_error)
        self.query_worker.start()
    
    def on_retry_progress(self, current: int, total: int):
        """Handle retry progress updates"""
        self.progress_bar.setValue(current)
        self.status_bar.showMessage(f"Retrying failed parameters... {current}/{total}")
    
    def on_retry_completed(self, results: Dict[int, Optional[int]]):
        """Handle retry completion"""
        self.progress_bar.setVisible(False)
        
        successful = sum(1 for v in results.values() if v is not None)
        total = len(results)
        still_failed = [pid for pid, value in results.items() if value is None]
        
        # Update UI with successful retry results
        for param_id, value in results.items():
            if value is not None:
                self.on_parameter_received(param_id, value)
        
        # Clear the status message properly
        if successful > 0:
            self.status_bar.showMessage(f"Retry completed: {successful}/{total} parameters retrieved", 3000)
        else:
            self.status_bar.showMessage("Retry completed - no additional parameters retrieved", 3000)
        
        if still_failed:
            # Show which parameters are still failing
            failed_details = []
            for param_id in still_failed:
                param = get_parameter_by_id(param_id)
                param_name = param.name if param else f"Unknown Parameter {param_id}"
                failed_details.append(f"  • {param_name} (ID: {param_id})")
            
            failed_list = "\n".join(failed_details)
            
            QMessageBox.warning(self, "Parameters Still Failing", 
                               f"The following {len(still_failed)} parameter(s) are still not responding:\n\n"
                               f"{failed_list}\n\n"
                               f"These parameters may not be supported by your Matriarch firmware version "
                               f"or may require different query timing.")
        else:
            QMessageBox.information(self, "Retry Successful", 
                                  "All previously failed parameters have been successfully retrieved!")
        
        # Update stored failed parameters
        self.last_failed_parameters = still_failed
    
    def retry_last_failed_parameters(self):
        """Retry the last set of failed parameters"""
        if not self.last_failed_parameters:
            QMessageBox.information(self, "No Failed Parameters", 
                                  "No failed parameters from the last query to retry.\n"
                                  "Run 'Query All Parameters' first.")
            return
        
        self.retry_failed_parameters(self.last_failed_parameters)
    
    def on_query_error(self, error_message: str):
        """Handle query errors"""
        self.progress_bar.setVisible(False)
        self.status_bar.showMessage("Query failed", 5000)
        QMessageBox.critical(self, "Query Error", 
                           f"Failed to query parameters:\n{error_message}")
    
    def save_preset(self):
        """Save current settings as preset"""
        # TODO: Implement preset saving
        QMessageBox.information(self, "Coming Soon", 
                              "Preset saving will be implemented in Phase 4")
    
    def load_preset(self):
        """Load preset"""
        # TODO: Implement preset loading
        QMessageBox.information(self, "Coming Soon", 
                              "Preset loading will be implemented in Phase 4")
    
    def reset_to_defaults(self):
        """Reset all parameters to default values"""
        reply = QMessageBox.question(self, "Reset to Defaults",
                                   "This will reset ALL parameters to their default values.\n"
                                   "Are you sure you want to continue?",
                                   QMessageBox.Yes | QMessageBox.No,
                                   QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            defaults = get_all_parameter_defaults()
            
            for param_id, default_value in defaults.items():
                if self.midi_manager.set_parameter(param_id, default_value):
                    self.on_parameter_received(param_id, default_value)
            
            self.status_bar.showMessage("Reset to defaults completed", 3000)
    
    def show_midi_settings(self):
        """Show MIDI settings dialog"""
        if not self.midi_settings_dialog:
            self.midi_settings_dialog = MIDISettingsDialog(self.midi_manager, self)
        
        if self.midi_settings_dialog.exec_() == QDialog.Accepted:
            self.save_settings()
            self.update_connection_status()
    
    def connect_midi(self):
        """Connect to MIDI"""
        if not self.midi_settings_dialog:
            self.show_midi_settings()
        else:
            # Use saved settings
            input_port = self.settings.value('midi/input_port')
            output_port = self.settings.value('midi/output_port')
            
            if input_port and output_port:
                if self.midi_manager.connect(input_port, output_port):
                    self.update_connection_status()
                    self.query_all_parameters()  # Auto-query on connect
            else:
                self.show_midi_settings()
    
    def disconnect_midi(self):
        """Disconnect from MIDI"""
        self.midi_manager.disconnect()
        self.update_connection_status()
    
    def show_midi_log(self):
        """Show MIDI log window"""
        if not self.midi_log_window:
            self.midi_log_window = MIDILogWindow()  # No parent to avoid embedding
        
        if self.midi_log_window.isHidden():
            self.midi_log_window.show()
        
        self.midi_log_window.raise_()
        self.midi_log_window.activateWindow()
    
    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(self, "About Matriarch Controller",
                         "Matriarch Controller v1.0\n\n"
                         "Real-time MIDI controller for Moog Matriarch synthesizer\n\n"
                         "Built with Python and PyQt5\n"
                         "© 2024 Matriarch Controller Project")
    
    def update_connection_status(self):
        """Update connection status display"""
        if self.midi_manager.is_connected:
            info = self.midi_manager.get_connection_info()
            status_text = f"Connected: {info['input_port']} ↔ {info['output_port']}"
            self.connection_label.setText(status_text)
            self.connection_label.setStyleSheet("color: #00ff00;")  # Green
        else:
            self.connection_label.setText("Disconnected")
            self.connection_label.setStyleSheet("color: #ff6666;")  # Red
    
    # Settings Management
    def load_settings(self):
        """Load application settings"""
        # Window geometry
        geometry = self.settings.value('window/geometry')
        if geometry:
            self.restoreGeometry(geometry)
        
        # Window state
        state = self.settings.value('window/state')
        if state:
            self.restoreState(state)
        
        # MIDI settings
        unit_id = self.settings.value('midi/unit_id', 0, type=int)
        midi_channel = self.settings.value('midi/midi_channel', 0, type=int)
        
        self.midi_manager.update_settings(unit_id, midi_channel)
    
    def save_settings(self):
        """Save application settings"""
        # Window geometry and state
        self.settings.setValue('window/geometry', self.saveGeometry())
        self.settings.setValue('window/state', self.saveState())
        
        # MIDI settings are saved by the dialog
    
    def closeEvent(self, event):
        """Handle application close"""
        self.save_settings()
        
        # Disconnect MIDI
        if self.midi_manager.is_connected:
            self.midi_manager.disconnect()
        
        # Close worker thread
        if self.query_worker and self.query_worker.isRunning():
            self.query_worker.terminate()
            self.query_worker.wait(1000)
        
        event.accept()