"""
MIDI Log Window for monitoring MIDI communication
"""

import logging
import os
from datetime import datetime
from typing import List, Dict, Any
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton,
    QCheckBox, QGroupBox, QLabel, QFileDialog, QMessageBox,
    QComboBox, QSpinBox
)
from PyQt5.QtCore import Qt, QTimer, QSettings
from PyQt5.QtGui import QFont, QTextCursor, QColor

logger = logging.getLogger(__name__)

class MIDILogWindow(QWidget):
    """Window for displaying and filtering MIDI log messages"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings = QSettings()
        self.log_messages: List[Dict[str, Any]] = []
        self.max_messages = 1000  # Limit memory usage
        
        # UI components
        self.log_display: QTextEdit = None
        self.auto_scroll_check: QCheckBox = None
        self.show_incoming_check: QCheckBox = None
        self.show_outgoing_check: QCheckBox = None
        self.show_sysex_check: QCheckBox = None
        self.show_cc_check: QCheckBox = None
        self.message_count_label: QLabel = None
        
        # Filtering
        self.filter_settings = {
            'show_incoming': True,
            'show_outgoing': True,
            'show_sysex': True,
            'show_cc': True,
            'auto_scroll': True
        }
        
        self.init_ui()
        self.load_settings()
        
        # Auto-refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_display)
        self.refresh_timer.start(100)  # Refresh every 100ms
    
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("MIDI Log")
        self.resize(800, 600)
        
        layout = QVBoxLayout(self)
        
        # Filter controls
        filter_group = QGroupBox("Filters")
        filter_layout = QHBoxLayout(filter_group)
        
        # Message type filters
        self.show_incoming_check = QCheckBox("Incoming")
        self.show_incoming_check.setChecked(True)
        self.show_incoming_check.toggled.connect(self.on_filter_changed)
        filter_layout.addWidget(self.show_incoming_check)
        
        self.show_outgoing_check = QCheckBox("Outgoing")
        self.show_outgoing_check.setChecked(True)
        self.show_outgoing_check.toggled.connect(self.on_filter_changed)
        filter_layout.addWidget(self.show_outgoing_check)
        
        filter_layout.addWidget(QLabel("|"))
        
        self.show_sysex_check = QCheckBox("SysEx")
        self.show_sysex_check.setChecked(True)
        self.show_sysex_check.toggled.connect(self.on_filter_changed)
        filter_layout.addWidget(self.show_sysex_check)
        
        self.show_cc_check = QCheckBox("Control Change")
        self.show_cc_check.setChecked(True)
        self.show_cc_check.toggled.connect(self.on_filter_changed)
        filter_layout.addWidget(self.show_cc_check)
        
        filter_layout.addWidget(QLabel("|"))
        
        # Auto-scroll option
        self.auto_scroll_check = QCheckBox("Auto-scroll")
        self.auto_scroll_check.setChecked(True)
        self.auto_scroll_check.toggled.connect(self.on_filter_changed)
        filter_layout.addWidget(self.auto_scroll_check)
        
        filter_layout.addStretch()
        
        # Message count
        self.message_count_label = QLabel("Messages: 0")
        filter_layout.addWidget(self.message_count_label)
        
        layout.addWidget(filter_group)
        
        # Log display
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setFont(QFont("Consolas", 9))  # Monospace font
        layout.addWidget(self.log_display)
        
        # Control buttons
        button_layout = QHBoxLayout()
        
        clear_button = QPushButton("Clear Log")
        clear_button.clicked.connect(self.clear_log)
        button_layout.addWidget(clear_button)
        
        save_button = QPushButton("Save to File...")
        save_button.clicked.connect(self.save_log)
        button_layout.addWidget(save_button)
        
        button_layout.addStretch()
        
        # Max messages control
        button_layout.addWidget(QLabel("Max Messages:"))
        max_msg_spin = QSpinBox()
        max_msg_spin.setRange(100, 10000)
        max_msg_spin.setValue(self.max_messages)
        max_msg_spin.valueChanged.connect(self.set_max_messages)
        button_layout.addWidget(max_msg_spin)
        
        layout.addLayout(button_layout)
        
        # Apply theme
        self.apply_theme()
    
    def apply_theme(self):
        """Apply dark theme to the log window"""
        self.setStyleSheet("""
            QWidget {
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
            QTextEdit {
                background-color: #1e1e1e;
                border: 2px solid #555555;
                border-radius: 5px;
                color: #ffffff;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 9pt;
                line-height: 1.2;
            }
            QCheckBox {
                color: #ffffff;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
            }
            QCheckBox::indicator:unchecked {
                border: 2px solid #666666;
                background-color: #4a4a4a;
                border-radius: 3px;
            }
            QCheckBox::indicator:checked {
                border: 2px solid #ff6b35;
                background-color: #ff6b35;
                border-radius: 3px;
            }
            QPushButton {
                background-color: #4a4a4a;
                color: #ffffff;
                border: 1px solid #666666;
                padding: 6px 16px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #5a5a5a;
                border-color: #777777;
            }
            QPushButton:pressed {
                background-color: #ff6b35;
            }
            QLabel {
                color: #ffffff;
            }
            QSpinBox {
                background-color: #4a4a4a;
                border: 1px solid #666666;
                padding: 4px;
                border-radius: 3px;
                color: #ffffff;
                min-width: 60px;
            }
        """)
    
    def add_message(self, message: str, is_incoming: bool):
        """Add a MIDI message to the log"""
        timestamp = datetime.now()
        
        # Parse message type
        msg_type = "OTHER"
        if "SysEx:" in message:
            msg_type = "SYSEX"
        elif "control_change" in message.lower():
            msg_type = "CC"
        
        log_entry = {
            'timestamp': timestamp,
            'message': message,
            'is_incoming': is_incoming,
            'type': msg_type
        }
        
        self.log_messages.append(log_entry)
        
        # Limit memory usage
        if len(self.log_messages) > self.max_messages:
            self.log_messages = self.log_messages[-self.max_messages:]
        
        # Update count immediately
        self.update_message_count()
    
    def refresh_display(self):
        """Refresh the log display based on current filters"""
        if not self.log_messages:
            return
        
        # Get current scroll position
        scrollbar = self.log_display.verticalScrollBar()
        was_at_bottom = scrollbar.value() >= scrollbar.maximum() - 10
        
        # Filter messages
        filtered_messages = []
        for msg in self.log_messages:
            if not self.should_show_message(msg):
                continue
            filtered_messages.append(msg)
        
        # Only update if we have new content or filters changed
        current_text = self.log_display.toPlainText()
        new_text = self.format_messages(filtered_messages)
        
        if current_text != new_text:
            self.log_display.clear()
            
            # Add messages with color formatting
            cursor = self.log_display.textCursor()
            cursor.movePosition(QTextCursor.End)
            
            for msg in filtered_messages:
                # Format timestamp
                time_str = msg['timestamp'].strftime("%H:%M:%S.%f")[:-3]  # Include milliseconds
                
                # Choose color based on direction and type
                if msg['is_incoming']:
                    if msg['type'] == 'SYSEX':
                        color = "#66ff66"  # Bright green for incoming SysEx
                    else:
                        color = "#99ff99"  # Light green for other incoming
                else:
                    if msg['type'] == 'SYSEX':
                        color = "#66ccff"  # Bright blue for outgoing SysEx
                    else:
                        color = "#99ccff"  # Light blue for other outgoing
                
                # Format and insert message
                formatted_msg = f"[{time_str}] {msg['message']}\n"
                
                cursor.insertHtml(f'<span style="color: {color};">{formatted_msg}</span>')
            
            # Auto-scroll if enabled and was at bottom
            if self.filter_settings['auto_scroll'] and was_at_bottom:
                scrollbar.setValue(scrollbar.maximum())
    
    def should_show_message(self, msg: Dict[str, Any]) -> bool:
        """Check if message should be shown based on current filters"""
        # Direction filter
        if msg['is_incoming'] and not self.filter_settings['show_incoming']:
            return False
        if not msg['is_incoming'] and not self.filter_settings['show_outgoing']:
            return False
        
        # Type filter
        if msg['type'] == 'SYSEX' and not self.filter_settings['show_sysex']:
            return False
        if msg['type'] == 'CC' and not self.filter_settings['show_cc']:
            return False
        
        return True
    
    def format_messages(self, messages: List[Dict[str, Any]]) -> str:
        """Format messages for plain text display"""
        formatted = []
        for msg in messages:
            time_str = msg['timestamp'].strftime("%H:%M:%S.%f")[:-3]
            formatted.append(f"[{time_str}] {msg['message']}")
        return '\n'.join(formatted)
    
    def on_filter_changed(self):
        """Handle filter checkbox changes"""
        self.filter_settings['show_incoming'] = self.show_incoming_check.isChecked()
        self.filter_settings['show_outgoing'] = self.show_outgoing_check.isChecked()
        self.filter_settings['show_sysex'] = self.show_sysex_check.isChecked()
        self.filter_settings['show_cc'] = self.show_cc_check.isChecked()
        self.filter_settings['auto_scroll'] = self.auto_scroll_check.isChecked()
        
        # Force immediate refresh
        self.refresh_display()
        self.save_settings()
    
    def clear_log(self):
        """Clear all log messages"""
        reply = QMessageBox.question(
            self, "Clear Log",
            "Are you sure you want to clear all log messages?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.log_messages.clear()
            self.log_display.clear()
            self.update_message_count()
    
    def save_log(self):
        """Save log messages to a file"""
        if not self.log_messages:
            QMessageBox.information(self, "Empty Log", "No messages to save.")
            return
        
        # Default filename with timestamp
        default_name = f"matriarch_midi_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "Save MIDI Log",
            default_name,
            "Text Files (*.txt);;All Files (*)"
        )
        
        if not filename:
            return
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"Matriarch Controller MIDI Log\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Total Messages: {len(self.log_messages)}\n")
                f.write("=" * 80 + "\n\n")
                
                for msg in self.log_messages:
                    timestamp = msg['timestamp'].strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                    direction = "IN " if msg['is_incoming'] else "OUT"
                    f.write(f"[{timestamp}] {direction}: {msg['message']}\n")
            
            QMessageBox.information(self, "Log Saved", f"Log saved to:\n{filename}")
            
        except Exception as e:
            logger.error(f"Error saving log file: {e}")
            QMessageBox.critical(self, "Save Error", f"Failed to save log file:\n{e}")
    
    def set_max_messages(self, value: int):
        """Set maximum number of messages to keep in memory"""
        self.max_messages = value
        
        # Trim current messages if needed
        if len(self.log_messages) > self.max_messages:
            self.log_messages = self.log_messages[-self.max_messages:]
            self.refresh_display()
        
        self.update_message_count()
    
    def update_message_count(self):
        """Update the message count label"""
        count = len(self.log_messages)
        self.message_count_label.setText(f"Messages: {count}/{self.max_messages}")
    
    def load_settings(self):
        """Load window and filter settings"""
        # Window geometry
        geometry = self.settings.value('midi_log/geometry')
        if geometry:
            self.restoreGeometry(geometry)
        
        # Filter settings
        self.filter_settings['show_incoming'] = self.settings.value('midi_log/show_incoming', True, type=bool)
        self.filter_settings['show_outgoing'] = self.settings.value('midi_log/show_outgoing', True, type=bool)
        self.filter_settings['show_sysex'] = self.settings.value('midi_log/show_sysex', True, type=bool)
        self.filter_settings['show_cc'] = self.settings.value('midi_log/show_cc', True, type=bool)
        self.filter_settings['auto_scroll'] = self.settings.value('midi_log/auto_scroll', True, type=bool)
        self.max_messages = self.settings.value('midi_log/max_messages', 1000, type=int)
        
        # Update checkboxes
        self.show_incoming_check.setChecked(self.filter_settings['show_incoming'])
        self.show_outgoing_check.setChecked(self.filter_settings['show_outgoing'])
        self.show_sysex_check.setChecked(self.filter_settings['show_sysex'])
        self.show_cc_check.setChecked(self.filter_settings['show_cc'])
        self.auto_scroll_check.setChecked(self.filter_settings['auto_scroll'])
    
    def save_settings(self):
        """Save window and filter settings"""
        # Window geometry
        self.settings.setValue('midi_log/geometry', self.saveGeometry())
        
        # Filter settings
        self.settings.setValue('midi_log/show_incoming', self.filter_settings['show_incoming'])
        self.settings.setValue('midi_log/show_outgoing', self.filter_settings['show_outgoing'])
        self.settings.setValue('midi_log/show_sysex', self.filter_settings['show_sysex'])
        self.settings.setValue('midi_log/show_cc', self.filter_settings['show_cc'])
        self.settings.setValue('midi_log/auto_scroll', self.filter_settings['auto_scroll'])
        self.settings.setValue('midi_log/max_messages', self.max_messages)
    
    def closeEvent(self, event):
        """Handle window close event"""
        self.save_settings()
        self.refresh_timer.stop()
        event.accept()