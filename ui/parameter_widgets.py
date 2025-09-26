"""
Parameter control widgets for different parameter types
"""

import logging
from typing import Optional, Dict, Any, List
from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, 
    QSlider, QSpinBox, QComboBox, QCheckBox, QGroupBox, QToolTip
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QPalette, QFont

from data.parameter_definitions import Parameter, ParameterType

logger = logging.getLogger(__name__)

class ParameterWidget(QWidget):
    """Base class for parameter control widgets"""
    
    value_changed = pyqtSignal(int, int)  # param_id, value
    
    def __init__(self, parameter: Parameter, parent=None):
        super().__init__(parent)
        self.parameter = parameter
        self.current_value = parameter.default_value
        self.is_updating = False  # Prevent signal loops
        self.is_enabled_by_dependency = True
        
        self.init_ui()
        self.update_enabled_state()
    
    def init_ui(self):
        """Initialize the widget UI - override in subclasses"""
        pass
    
    def set_value_silently(self, value: int):
        """Set value without emitting signals"""
        self.is_updating = True
        try:
            self.current_value = value
            self.update_display()
        finally:
            self.is_updating = False
    
    def update_display(self):
        """Update the visual display - override in subclasses"""
        pass
    
    def emit_value_changed(self, value: int):
        """Emit value changed signal if not updating"""
        if not self.is_updating:
            self.current_value = value
            self.value_changed.emit(self.parameter.param_id, value)
    
    def set_dependency_enabled(self, enabled: bool, reason: str = ""):
        """Enable/disable based on parameter dependencies"""
        self.is_enabled_by_dependency = enabled
        self.update_enabled_state()
        
        if not enabled and reason:
            self.setToolTip(f"{self.parameter.tooltip}\n\nDisabled: {reason}")
        else:
            self.setToolTip(self.parameter.tooltip)
    
    def update_enabled_state(self):
        """Update the enabled state of the widget"""
        self.setEnabled(self.is_enabled_by_dependency)

class ToggleParameterWidget(ParameterWidget):
    """Widget for on/off parameters"""
    
    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)
        
        # Parameter name
        self.name_label = QLabel(self.parameter.name)
        self.name_label.setMinimumWidth(200)
        layout.addWidget(self.name_label)
        
        # Toggle button
        self.toggle_button = QPushButton()
        self.toggle_button.setCheckable(True)
        self.toggle_button.setMinimumWidth(80)
        self.toggle_button.clicked.connect(self.on_toggle_clicked)
        layout.addWidget(self.toggle_button)
        
        # Default indicator
        default_text = "On" if self.parameter.default_value else "Off"
        self.default_label = QLabel(f"(Default: {default_text})")
        self.default_label.setStyleSheet("color: #888888; font-size: 10px;")
        layout.addWidget(self.default_label)
        
        layout.addStretch()
        
        # Set initial state
        self.update_display()
    
    def update_display(self):
        """Update toggle button display"""
        is_on = bool(self.current_value)
        self.toggle_button.setChecked(is_on)
        self.toggle_button.setText("On" if is_on else "Off")
        
        # Highlight if different from default
        is_default = self.current_value == self.parameter.default_value
        if not is_default:
            self.toggle_button.setStyleSheet("""
                QPushButton:checked {
                    background-color: #ff6b35;
                    font-weight: bold;
                }
                QPushButton {
                    background-color: #666666;
                    font-weight: bold;
                }
            """)
        else:
            self.toggle_button.setStyleSheet("")
    
    def on_toggle_clicked(self, checked: bool):
        """Handle toggle button click"""
        value = 1 if checked else 0
        self.emit_value_changed(value)

class ChoiceParameterWidget(ParameterWidget):
    """Widget for multiple choice parameters"""
    
    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)
        
        # Parameter name
        self.name_label = QLabel(self.parameter.name)
        self.name_label.setMinimumWidth(200)
        layout.addWidget(self.name_label)
        
        # Combo box
        self.combo_box = QComboBox()
        self.combo_box.setMinimumWidth(150)
        
        # Populate choices
        for value, text in self.parameter.choices.items():
            self.combo_box.addItem(text, value)
        
        self.combo_box.currentIndexChanged.connect(self.on_combo_changed)
        layout.addWidget(self.combo_box)
        
        # Raw value display
        self.raw_value_label = QLabel()
        self.raw_value_label.setStyleSheet("color: #888888; font-size: 10px;")
        layout.addWidget(self.raw_value_label)
        
        # Default indicator
        default_text = self.parameter.choices.get(self.parameter.default_value, "Unknown")
        self.default_label = QLabel(f"(Default: {default_text})")
        self.default_label.setStyleSheet("color: #888888; font-size: 10px;")
        layout.addWidget(self.default_label)
        
        layout.addStretch()
        
        # Set initial state
        self.update_display()
    
    def update_display(self):
        """Update combo box selection"""
        # Find the item with matching value
        for i in range(self.combo_box.count()):
            if self.combo_box.itemData(i) == self.current_value:
                self.combo_box.setCurrentIndex(i)
                break
        
        # Update raw value display
        self.raw_value_label.setText(f"({self.current_value})")
        
        # Highlight if different from default
        is_default = self.current_value == self.parameter.default_value
        if not is_default:
            self.combo_box.setStyleSheet("""
                QComboBox {
                    background-color: #5a4a2a;
                    border: 2px solid #ff6b35;
                }
            """)
        else:
            self.combo_box.setStyleSheet("")
    
    def on_combo_changed(self, index: int):
        """Handle combo box selection change"""
        if index >= 0:
            value = self.combo_box.itemData(index)
            if value is not None:
                self.emit_value_changed(value)

class RangeParameterWidget(ParameterWidget):
    """Widget for range parameters with slider and spinbox"""
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)
        
        # Top row: name and current value
        top_layout = QHBoxLayout()
        
        self.name_label = QLabel(self.parameter.name)
        self.name_label.setMinimumWidth(200)
        top_layout.addWidget(self.name_label)
        
        top_layout.addStretch()
        
        # Current value display
        self.value_label = QLabel()
        self.value_label.setStyleSheet("font-weight: bold; color: #ff6b35;")
        top_layout.addWidget(self.value_label)
        
        # Raw value in parentheses
        self.raw_value_label = QLabel()
        self.raw_value_label.setStyleSheet("color: #888888; font-size: 10px;")
        top_layout.addWidget(self.raw_value_label)
        
        layout.addLayout(top_layout)
        
        # Bottom row: slider and spinbox
        bottom_layout = QHBoxLayout()
        
        # Slider
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(self.parameter.min_value or 0)
        self.slider.setMaximum(self.parameter.max_value or 127)
        self.slider.valueChanged.connect(self.on_slider_changed)
        bottom_layout.addWidget(self.slider, stretch=3)
        
        # Spinbox for precise control
        self.spinbox = QSpinBox()
        self.spinbox.setMinimum(self.parameter.min_value or 0)
        self.spinbox.setMaximum(self.parameter.max_value or 127)
        self.spinbox.setMinimumWidth(80)
        self.spinbox.valueChanged.connect(self.on_spinbox_changed)
        bottom_layout.addWidget(self.spinbox)
        
        layout.addLayout(bottom_layout)
        
        # Default value indicator
        default_readable = self.parameter.get_human_readable(self.parameter.default_value)
        self.default_label = QLabel(f"Default: {default_readable} ({self.parameter.default_value})")
        self.default_label.setStyleSheet("color: #888888; font-size: 10px;")
        layout.addWidget(self.default_label)
        
        # Set initial state
        self.update_display()
    
    def update_display(self):
        """Update slider and spinbox values"""
        # Update controls without triggering signals
        self.slider.blockSignals(True)
        self.spinbox.blockSignals(True)
        
        self.slider.setValue(self.current_value)
        self.spinbox.setValue(self.current_value)
        
        self.slider.blockSignals(False)
        self.spinbox.blockSignals(False)
        
        # Update value displays
        human_readable = self.parameter.get_human_readable(self.current_value)
        self.value_label.setText(human_readable)
        self.raw_value_label.setText(f"({self.current_value})")
        
        # Highlight if different from default
        is_default = self.current_value == self.parameter.default_value
        if not is_default:
            self.slider.setStyleSheet("""
                QSlider::groove:horizontal {
                    border: 1px solid #ff6b35;
                    background: #4a4a4a;
                    height: 8px;
                }
                QSlider::handle:horizontal {
                    background: #ff6b35;
                    border: 1px solid #ff6b35;
                    width: 18px;
                    margin: -5px 0;
                    border-radius: 9px;
                }
            """)
            self.spinbox.setStyleSheet("""
                QSpinBox {
                    background-color: #5a4a2a;
                    border: 2px solid #ff6b35;
                }
            """)
        else:
            self.slider.setStyleSheet("")
            self.spinbox.setStyleSheet("")
    
    def on_slider_changed(self, value: int):
        """Handle slider value change"""
        # Update spinbox to match
        self.spinbox.blockSignals(True)
        self.spinbox.setValue(value)
        self.spinbox.blockSignals(False)
        
        # Update display and emit signal
        self.emit_value_changed(value)
        
        # Update display immediately for responsiveness
        human_readable = self.parameter.get_human_readable(value)
        self.value_label.setText(human_readable)
        self.raw_value_label.setText(f"({value})")
    
    def on_spinbox_changed(self, value: int):
        """Handle spinbox value change"""
        # Update slider to match
        self.slider.blockSignals(True)
        self.slider.setValue(value)
        self.slider.blockSignals(False)
        
        self.emit_value_changed(value)

class MIDIChannelParameterWidget(ParameterWidget):
    """Special widget for MIDI channel parameters (1-16 display, 0-15 internal)"""
    
    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)
        
        # Parameter name
        self.name_label = QLabel(self.parameter.name)
        self.name_label.setMinimumWidth(200)
        layout.addWidget(self.name_label)
        
        # Channel selector
        self.channel_combo = QComboBox()
        self.channel_combo.setMinimumWidth(100)
        
        # Add channels 1-16 (stored as 0-15)
        for i in range(16):
            self.channel_combo.addItem(f"Channel {i + 1}", i)
        
        self.channel_combo.currentIndexChanged.connect(self.on_channel_changed)
        layout.addWidget(self.channel_combo)
        
        # Raw value display
        self.raw_value_label = QLabel()
        self.raw_value_label.setStyleSheet("color: #888888; font-size: 10px;")
        layout.addWidget(self.raw_value_label)
        
        # Default indicator
        default_display = f"Channel {self.parameter.default_value + 1}"
        self.default_label = QLabel(f"(Default: {default_display})")
        self.default_label.setStyleSheet("color: #888888; font-size: 10px;")
        layout.addWidget(self.default_label)
        
        layout.addStretch()
        
        # Set initial state
        self.update_display()
    
    def update_display(self):
        """Update channel combo selection"""
        self.channel_combo.setCurrentIndex(self.current_value)
        self.raw_value_label.setText(f"(Raw: {self.current_value})")
        
        # Highlight if different from default
        is_default = self.current_value == self.parameter.default_value
        if not is_default:
            self.channel_combo.setStyleSheet("""
                QComboBox {
                    background-color: #5a4a2a;
                    border: 2px solid #ff6b35;
                }
            """)
        else:
            self.channel_combo.setStyleSheet("")
    
    def on_channel_changed(self, index: int):
        """Handle channel selection change"""
        if index >= 0:
            value = self.channel_combo.itemData(index)
            if value is not None:
                self.emit_value_changed(value)

class ParameterWidgetFactory:
    """Factory for creating appropriate parameter widgets"""
    
    @staticmethod
    def create_widget(parameter: Parameter) -> ParameterWidget:
        """Create appropriate widget for parameter type"""
        if parameter.param_type == ParameterType.TOGGLE:
            return ToggleParameterWidget(parameter)
        elif parameter.param_type == ParameterType.CHOICE:
            return ChoiceParameterWidget(parameter)
        elif parameter.param_type == ParameterType.RANGE:
            return RangeParameterWidget(parameter)
        elif parameter.param_type == ParameterType.MIDI_CHANNEL:
            return MIDIChannelParameterWidget(parameter)
        else:
            logger.warning(f"Unknown parameter type: {parameter.param_type}")
            return ToggleParameterWidget(parameter)  # Fallback

class DependencyManager:
    """Manages parameter dependencies and enables/disables widgets accordingly"""
    
    def __init__(self, widgets: Dict[int, ParameterWidget]):
        self.widgets = widgets
        self.current_values = {}
    
    def update_value(self, param_id: int, value: int):
        """Update value and check dependencies"""
        self.current_values[param_id] = value
        self._check_all_dependencies()
    
    def _check_all_dependencies(self):
        """Check all parameter dependencies and update widget states"""
        from data.parameter_definitions import get_parameter_by_id
        
        for param_id, widget in self.widgets.items():
            param = get_parameter_by_id(param_id)
            if param and param.dependencies:
                enabled, reason = self._check_dependencies(param)
                widget.set_dependency_enabled(enabled, reason)
    
    def _check_dependencies(self, parameter: Parameter) -> tuple[bool, str]:
        """Check if parameter dependencies are satisfied"""
        # This is a simplified implementation
        # In a full implementation, you would parse dependency strings
        # and check actual parameter values
        
        # For now, just return enabled for all
        # TODO: Implement actual dependency checking based on parameter.dependencies
        return True, ""
    
    def set_dependency_rules(self, rules: Dict[int, callable]):
        """Set custom dependency checking rules"""
        # TODO: Implement custom dependency rule system
        pass

# Helper functions for creating parameter groups

def create_parameter_group(title: str, parameters: List[Parameter], 
                          factory: ParameterWidgetFactory) -> QGroupBox:
    """Create a group box containing parameter widgets"""
    group = QGroupBox(title)
    layout = QVBoxLayout(group)
    layout.setSpacing(3)
    
    widgets = []
    for param in parameters:
        widget = factory.create_widget(param)
        layout.addWidget(widget)
        widgets.append(widget)
    
    return group, widgets

class ParameterGroupWidget(QWidget):
    """Widget that groups related parameters together visually"""
    
    value_changed = pyqtSignal(int, int)  # param_id, value
    
    def __init__(self, title: str, parameters: List[Parameter], parent=None):
        super().__init__(parent)
        self.parameters = parameters
        self.widgets = {}
        
        self.init_ui(title)
    
    def init_ui(self, title: str):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Group title
        title_label = QLabel(title)
        title_label.setStyleSheet("font-weight: bold; color: #ff6b35; font-size: 12px;")
        layout.addWidget(title_label)
        
        # Add parameter widgets
        factory = ParameterWidgetFactory()
        for param in self.parameters:
            widget = factory.create_widget(param)
            widget.value_changed.connect(self.value_changed.emit)
            self.widgets[param.param_id] = widget
            layout.addWidget(widget)
    
    def set_value_silently(self, param_id: int, value: int):
        """Set value for a specific parameter without emitting signals"""
        if param_id in self.widgets:
            self.widgets[param_id].set_value_silently(value)
    
    def get_parameter_widget(self, param_id: int) -> Optional[ParameterWidget]:
        """Get widget for specific parameter"""
        return self.widgets.get(param_id)
    def apply_widget_theme(widget):
        """Apply consistent theming to parameter widgets"""
        widget.setStyleSheet("""
            ParameterWidget {
                background-color: #3c3c3c;
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 3px;
                margin: 1px;
            }
            ParameterWidget:hover {
                border-color: #777777;
            }
            QLabel {
                color: #ffffff;
                font-size: 11px;
            }
            QSlider::groove:horizontal {
                border: 1px solid #666666;
                background: #4a4a4a;
                height: 6px;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #ff6b35;
                border: 1px solid #ff6b35;
                width: 16px;
                margin: -5px 0;
                border-radius: 8px;
            }
            QSlider::handle:horizontal:hover {
                background: #ff8c5a;
            }
            QComboBox {
                background-color: #4a4a4a;
                border: 1px solid #666666;
                padding: 2px 5px;
                border-radius: 3px;
                color: #ffffff;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 4px solid #ffffff;
                margin-right: 5px;
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
                padding: 2px;
                border-radius: 3px;
                color: #ffffff;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                background-color: #5a5a5a;
                border: 1px solid #666666;
            }
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {
                background-color: #6a6a6a;
            }
            QPushButton {
                background-color: #4a4a4a;
                border: 1px solid #666666;
                padding: 4px 12px;
                border-radius: 3px;
                color: #ffffff;
                font-weight: normal;
            }
            QPushButton:hover {
                background-color: #5a5a5a;
                border-color: #777777;
            }
            QPushButton:checked {
                background-color: #ff6b35;
                border-color: #ff6b35;
                color: #ffffff;
                font-weight: bold;
            }
            QPushButton:pressed {
                background-color: #e55a2b;
            }
        """)