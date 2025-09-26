# ui/__init__.py  
"""
UI module for Matriarch Controller
Contains all user interface components
"""

from .main_window import MatriarchMainWindow
from .parameter_widgets import (
    ParameterWidget,
    ToggleParameterWidget, 
    ChoiceParameterWidget,
    RangeParameterWidget,
    MIDIChannelParameterWidget,
    ParameterWidgetFactory,
    ParameterGroupWidget,
    DependencyManager
)
from .midi_settings_dialog import MIDISettingsDialog
from .midi_log_window import MIDILogWindow

__all__ = [
    'MatriarchMainWindow',
    'ParameterWidget',
    'ToggleParameterWidget',
    'ChoiceParameterWidget', 
    'RangeParameterWidget',
    'MIDIChannelParameterWidget',
    'ParameterWidgetFactory',
    'ParameterGroupWidget',
    'DependencyManager',
    'MIDISettingsDialog',
    'MIDILogWindow'
]