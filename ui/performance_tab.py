"""
Performance Tab - Custom layout matching Matriarch hardware
"""

import logging
from typing import Dict, Optional
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, 
    QGroupBox, QLabel, QSlider, QPushButton, QComboBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

from data.parameter_definitions import get_parameter_by_id, Parameter
from ui.parameter_widgets import ParameterWidget, ButtonGroupParameterWidget

logger = logging.getLogger(__name__)

class PerformanceTabWidget(QWidget):
    """Custom performance tab with hardware-inspired layout"""
    
    parameter_changed = pyqtSignal(int, int)  # param_id, value
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parameter_widgets: Dict[int, ParameterWidget] = {}
        self.init_ui()
    
    def init_ui(self):
        """Initialize the performance tab layout"""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Top row with colored sections
        top_row = QHBoxLayout()
        top_row.setSpacing(10)
        
        # Create ARP/SEQ section
        arp_seq_section = self.create_arp_seq_section()
        top_row.addWidget(arp_seq_section)
        
        # Placeholder for other sections
        # TODO: Add OSCILLATORS, STEREO DELAY, OUTPUT sections
        
        main_layout.addLayout(top_row)
        main_layout.addStretch()
    
    def create_arp_seq_section(self) -> QGroupBox:
        """Create the ARP/SEQ section (yellow box)"""
        group = QGroupBox("ARP/SEQ")
        group.setStyleSheet("""
            QGroupBox {
                background-color: #E8E8A0;
                border: 2px solid #B8B870;
                border-radius: 5px;
                margin-top: 10px;
                font-weight: bold;
                padding: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 5px 10px;
                color: #4a4a2a;
            }
        """)
        
        layout = QGridLayout(group)
        layout.setSpacing(8)
        layout.setContentsMargins(10, 20, 10, 10)
        
        # Row 0-1: Rate control
        rate_label = QLabel("Rate")
        rate_label.setStyleSheet("font-weight: bold; color: #4a4a2a;")
        layout.addWidget(rate_label, 0, 0, 1, 3, Qt.AlignCenter)
        
        # Rate slider (parameter 108 - Arp Rate)
        rate_param = get_parameter_by_id(108)
        if rate_param:
            rate_widget = ArpRateWidget(rate_param)
            rate_widget.value_changed.connect(self.on_widget_value_changed)
            self.parameter_widgets[108] = rate_widget
            layout.addWidget(rate_widget, 1, 0, 1, 3)
        
        # Row 2: Mode selector (parameter 191 - Arp Mode)
        mode_label = QLabel("MODE")
        mode_label.setStyleSheet("font-weight: normal; color: #4a4a2a;")
        layout.addWidget(mode_label, 2, 0)
        
        mode_param = get_parameter_by_id(191)
        if mode_param:
            mode_widget = CustomButtonGroup(mode_param, selected_color="#6B8E23")
            mode_widget.value_changed.connect(self.on_widget_value_changed)
            self.parameter_widgets[191] = mode_widget
            layout.addWidget(mode_widget, 2, 1, 1, 3)
        
        # Row 3: Pattern selector (parameter 192 - Arp Pattern)
        pattern_label = QLabel("Pattern")
        pattern_label.setStyleSheet("font-weight: normal; color: #4a4a2a;")
        layout.addWidget(pattern_label, 3, 0)
        
        pattern_param = get_parameter_by_id(192)
        if pattern_param:
            pattern_widget = CustomButtonGroup(pattern_param, selected_color="#6B8E23")
            pattern_widget.value_changed.connect(self.on_widget_value_changed)
            self.parameter_widgets[192] = pattern_widget
            layout.addWidget(pattern_widget, 3, 1, 1, 3)
        
        # Row 4: FW/BW Repeat (parameter 22)
        repeat_param = get_parameter_by_id(22)
        if repeat_param:
            repeat_widget = ToggleButton(repeat_param)
            repeat_widget.value_changed.connect(self.on_widget_value_changed)
            self.parameter_widgets[22] = repeat_widget
            layout.addWidget(repeat_widget, 4, 0, 1, 4)
        
        # Row 5: Oct/Bank (parameter 193)
        octbank_label = QLabel("Oct/Bank")
        octbank_label.setStyleSheet("font-weight: normal; color: #4a4a2a;")
        layout.addWidget(octbank_label, 5, 0)
        
        octbank_param = get_parameter_by_id(193)
        if octbank_param:
            octbank_widget = CustomButtonGroup(octbank_param, selected_color="#6B8E23")
            octbank_widget.value_changed.connect(self.on_widget_value_changed)
            self.parameter_widgets[193] = octbank_widget
            layout.addWidget(octbank_widget, 5, 1, 1, 3)
        
        # Row 6: Sequence selector (using Mode knob visual representation)
        seq_label = QLabel("Sequence")
        seq_label.setStyleSheet("font-weight: normal; color: #4a4a2a;")
        layout.addWidget(seq_label, 6, 0)
        
        # Sequence selector buttons (1, 2, 3, 4)
        seq_layout = QHBoxLayout()
        seq_layout.setSpacing(2)
        for i in range(1, 5):
            btn = QPushButton(str(i))
            btn.setCheckable(True)
            btn.setMinimumHeight(30)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #999999;
                    border: 1px solid #666666;
                    color: white;
                }
                QPushButton:checked {
                    background-color: #6B8E23;
                    border: 2px solid #556B2F;
                    font-weight: bold;
                }
            """)
            seq_layout.addWidget(btn)
        layout.addLayout(seq_layout, 6, 1, 1, 3)
        
        # Row 7: Play and Hold buttons (these aren't parameters, they're transport controls)
        play_hold_layout = QHBoxLayout()
        play_hold_layout.setSpacing(5)
        
        play_btn = QPushButton("Play")
        play_btn.setCheckable(True)
        play_btn.setMinimumHeight(35)
        play_btn.setStyleSheet("""
            QPushButton {
                background-color: #4a4a4a;
                border: 2px solid #666666;
                color: white;
                font-weight: bold;
            }
            QPushButton:checked {
                background-color: #228B22;
                border: 2px solid #1a6b1a;
            }
        """)
        
        hold_btn = QPushButton("Hold")
        hold_btn.setCheckable(True)
        hold_btn.setMinimumHeight(35)
        hold_btn.setStyleSheet("""
            QPushButton {
                background-color: #4a4a4a;
                border: 2px solid #666666;
                color: white;
                font-weight: bold;
            }
            QPushButton:checked {
                background-color: #4169E1;
                border: 2px solid #315bb3;
            }
        """)
        
        play_hold_layout.addWidget(play_btn)
        play_hold_layout.addWidget(hold_btn)
        layout.addLayout(play_hold_layout, 7, 0, 1, 4)
        
        return group
    
    def on_widget_value_changed(self, param_id: int, value: int):
        """Forward parameter changes from widgets"""
        self.parameter_changed.emit(param_id, value)
    
    def set_parameter_value(self, param_id: int, value: int):
        """Update a parameter widget's value"""
        if param_id in self.parameter_widgets:
            self.parameter_widgets[param_id].set_value_silently(value)


class ArpRateWidget(ParameterWidget):
    """Custom widget for Arp Rate with BPM display"""
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(2)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Value display
        self.value_label = QLabel("120 BPM")
        self.value_label.setStyleSheet("font-weight: bold; color: #4a4a2a; font-size: 14px;")
        self.value_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.value_label)
        
        # Slider
        self.slider = QSlider(Qt.Vertical)
        self.slider.setMinimum(0)
        self.slider.setMaximum(16383)
        self.slider.setValue(8192)
        self.slider.setMinimumHeight(80)
        self.slider.valueChanged.connect(self.on_slider_changed)
        layout.addWidget(self.slider, alignment=Qt.AlignCenter)
        
        self.update_display()
    
    def update_display(self):
        """Update the BPM display"""
        # TODO: Convert value to BPM (20-280 range)
        # For now, simple mapping
        bpm = int(20 + (self.current_value / 16383.0) * 260)
        self.value_label.setText(f"{bpm} BPM")
    
    def on_slider_changed(self, value: int):
        """Handle slider changes"""
        self.emit_value_changed(value)
        self.current_value = value
        self.update_display()


class CustomButtonGroup(ParameterWidget):
    """Button group with custom styling"""
    
    def __init__(self, parameter: Parameter, selected_color: str = "#6B8E23", parent=None):
        self.selected_color = selected_color
        super().__init__(parameter, parent)
    
    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setSpacing(2)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.buttons = {}
        for value, text in sorted(self.parameter.choices.items()):
            button = QPushButton(text)
            button.setCheckable(True)
            button.setMinimumHeight(30)
            button.clicked.connect(lambda checked, v=value: self.on_button_clicked(v))
            
            self.buttons[value] = button
            layout.addWidget(button)
        
        self.update_display()
    
    def update_display(self):
        """Update button states"""
        for value, button in self.buttons.items():
            button.blockSignals(True)
            button.setChecked(value == self.current_value)
            
            if button.isChecked():
                button.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {self.selected_color};
                        border: 2px solid #556B2F;
                        color: white;
                        font-weight: bold;
                    }}
                """)
            else:
                button.setStyleSheet("""
                    QPushButton {
                        background-color: #999999;
                        border: 1px solid #666666;
                        color: white;
                    }
                    QPushButton:hover {
                        background-color: #aaaaaa;
                    }
                """)
            button.blockSignals(False)
    
    def on_button_clicked(self, value: int):
        """Handle button click"""
        self.emit_value_changed(value)


class ToggleButton(ParameterWidget):
    """Simple toggle button"""
    
    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.button = QPushButton(self.parameter.name)
        self.button.setCheckable(True)
        self.button.setMinimumHeight(30)
        self.button.clicked.connect(self.on_clicked)
        layout.addWidget(self.button)
        
        self.update_display()
    
    def update_display(self):
        """Update button state"""
        self.button.blockSignals(True)
        self.button.setChecked(bool(self.current_value))
        
        if self.button.isChecked():
            self.button.setStyleSheet("""
                QPushButton {
                    background-color: #6B8E23;
                    border: 2px solid #556B2F;
                    color: white;
                    font-weight: bold;
                }
            """)
        else:
            self.button.setStyleSheet("""
                QPushButton {
                    background-color: #999999;
                    border: 1px solid #666666;
                    color: white;
                }
            """)
        self.button.blockSignals(False)
    
    def on_clicked(self):
        """Handle button click"""
        value = 1 if self.button.isChecked() else 0
        self.emit_value_changed(value)