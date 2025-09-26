# data/__init__.py
"""
Data module for Matriarch Controller
Contains parameter definitions and data structures
"""

from .parameter_definitions import (
    Parameter,
    ParameterType, 
    ParameterCategory,
    PARAMETERS,
    get_parameters_by_category,
    get_parameter_by_id,
    get_all_parameter_defaults
)

__all__ = [
    'Parameter',
    'ParameterType',
    'ParameterCategory', 
    'PARAMETERS',
    'get_parameters_by_category',
    'get_parameter_by_id',
    'get_all_parameter_defaults'
]

# ---

# midi/__init__.py
"""
MIDI communication module for Matriarch Controller
Handles SysEx messages and MIDI connection management
"""

from .connection import MIDIConnectionManager
from .sysex import MatriarchSysEx, SysExError, SysExTimeoutError, SysExValidationError

__all__ = [
    'MIDIConnectionManager',
    'MatriarchSysEx',
    'SysExError',
    'SysExTimeoutError', 
    'SysExValidationError'
]

# ---

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