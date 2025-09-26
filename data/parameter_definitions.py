"""
Matriarch Global Parameter Definitions
Based on Matriarch Manual pages 76-79
"""

from enum import Enum
from typing import Dict, Any, List, Optional, Union

class ParameterType(Enum):
    TOGGLE = "toggle"           # On/Off, 0/1 values
    CHOICE = "choice"           # Multiple discrete choices
    RANGE = "range"             # Continuous range with min/max
    MIDI_CHANNEL = "midi_channel"  # Special case for MIDI channels 1-16

class ParameterCategory(Enum):
    MIDI_COMMUNICATION = "MIDI & Communication"
    PERFORMANCE_KEYBOARD = "Performance & Keyboard" 
    ARP_SEQUENCER = "Arp/Sequencer"
    AUDIO_CV = "Audio & CV"
    ADVANCED = "Advanced"

class Parameter:
    """Represents a single Matriarch global parameter"""
    
    def __init__(self, 
                 param_id: int,
                 name: str,
                 category: ParameterCategory,
                 param_type: ParameterType,
                 default_value: Union[int, str],
                 description: str,
                 sysex_group: int = 0,
                 sysex_param: int = 0,
                 cc_number: Optional[int] = None,
                 min_value: Optional[int] = None,
                 max_value: Optional[int] = None,
                 choices: Optional[Dict[int, str]] = None,
                 human_readable_func: Optional[callable] = None,
                 dependencies: Optional[List[str]] = None,
                 tooltip: Optional[str] = None):
        
        self.param_id = param_id
        self.name = name
        self.category = category
        self.param_type = param_type
        self.default_value = default_value
        self.description = description
        self.sysex_group = sysex_group
        self.sysex_param = sysex_param
        self.cc_number = cc_number
        self.min_value = min_value
        self.max_value = max_value
        self.choices = choices or {}
        self.human_readable_func = human_readable_func
        self.dependencies = dependencies or []
        self.tooltip = tooltip or description
        
    def validate_value(self, value: int) -> int:
        """Validate and clamp value to acceptable range"""
        if self.param_type == ParameterType.TOGGLE:
            return 1 if value else 0
        elif self.param_type == ParameterType.CHOICE:
            if value in self.choices:
                return value
            # Return closest valid choice
            valid_values = list(self.choices.keys())
            return min(valid_values, key=lambda x: abs(x - value))
        elif self.param_type == ParameterType.RANGE:
            if self.min_value is not None and self.max_value is not None:
                return max(self.min_value, min(self.max_value, value))
        elif self.param_type == ParameterType.MIDI_CHANNEL:
            return max(0, min(15, value))  # 0-15 for MIDI channels 1-16
            
        return value
    
    def get_human_readable(self, value: int) -> str:
        """Get human-readable representation of value"""
        if self.human_readable_func:
            return self.human_readable_func(value)
        elif self.param_type == ParameterType.TOGGLE:
            return "On" if value else "Off"
        elif self.param_type == ParameterType.CHOICE:
            return self.choices.get(value, f"Unknown ({value})")
        elif self.param_type == ParameterType.MIDI_CHANNEL:
            return f"Channel {value + 1}"
        else:
            return str(value)

# Helper functions for human-readable conversions
def swing_percentage(value: int) -> str:
    """Convert swing value 0-16383 to percentage"""
    percent = (value / 16383.0) * 100
    return f"{percent:.1f}%"

def semitones_display(value: int) -> str:
    """Display semitone values"""
    if value == 0:
        return "None"
    return f"{value} semitone{'s' if value != 1 else ''}"

def ppqn_display(value: int) -> str:
    """Convert PPQN index to descriptive text"""
    ppqn_values = {
        0: "1 PPQN (Whole Notes)",
        1: "2 PPQN (Half Notes)", 
        2: "3 PPQN (Triplet Half Notes)",
        3: "4 PPQN (Quarter Notes)",
        4: "5 PPQN", 
        5: "6 PPQN (Triplet Quarter)",
        6: "7 PPQN",
        7: "8 PPQN (Eighth Notes)",
        8: "9 PPQN",
        9: "10 PPQN",
        10: "11 PPQN", 
        11: "12 PPQN (Triplet Eighth)",
        12: "24 PPQN (Sixteenth Notes)",
        13: "48 PPQN (Thirty-second Notes)"
    }
    return ppqn_values.get(value, f"{value} PPQN")

def pitch_variance_cents(value: int) -> str:
    """Convert pitch variance to cents"""
    cents = value * 0.1  # 0.1 cent increments
    if cents == 0:
        return "Off"
    return f"±{cents:.1f} cents"

# Parameter definitions based on Matriarch manual
PARAMETERS = {
    # Group 0 - Default Parameters (pages 62-63)
    0: Parameter(0, "Unit ID", ParameterCategory.ADVANCED, ParameterType.RANGE,
                0, "MIDI Unit ID for SysEx communication", 
                min_value=0, max_value=15, tooltip="Unit ID for MIDI SysEx (usually 0)"),
                
    1: Parameter(1, "Tuning Scale", ParameterCategory.ADVANCED, ParameterType.RANGE,
                0, "Active tuning scale (0=12-TET)", 
                min_value=0, max_value=31, tooltip="Tuning table selection (0=12-tone equal temperament)"),
                
    2: Parameter(2, "Knob Mode", ParameterCategory.ADVANCED, ParameterType.CHOICE,
                2, "How panel knobs respond to value changes",
                choices={0: "Snap", 1: "Pass-Thru", 2: "Relative"}),
                
    3: Parameter(3, "Note Priority", ParameterCategory.PERFORMANCE_KEYBOARD, ParameterType.CHOICE,
                2, "Which note takes priority in monophonic mode",
                choices={0: "Low", 1: "High", 2: "Last Note"}),
                
    4: Parameter(4, "Send Program Change", ParameterCategory.MIDI_COMMUNICATION, ParameterType.TOGGLE,
                0, "Send MIDI Program Change when selecting sequences"),
                
    5: Parameter(5, "Receive Program Change", ParameterCategory.MIDI_COMMUNICATION, ParameterType.TOGGLE,
                1, "Respond to MIDI Program Change messages"),
                
    6: Parameter(6, "MIDI Input Ports", ParameterCategory.MIDI_COMMUNICATION, ParameterType.CHOICE,
                3, "Which MIDI input ports to use",
                choices={0: "None", 1: "DIN Only", 2: "USB Only", 3: "Both DIN and USB"}),
                
    7: Parameter(7, "MIDI Output Ports", ParameterCategory.MIDI_COMMUNICATION, ParameterType.CHOICE,
                3, "Which MIDI output ports to use",
                choices={0: "None", 1: "DIN Only", 2: "USB Only", 3: "Both DIN and USB"}),
                
    8: Parameter(8, "MIDI Echo USB In", ParameterCategory.MIDI_COMMUNICATION, ParameterType.CHOICE,
                0, "Echo USB MIDI input to outputs",
                choices={0: "Off", 1: "Echo to DIN Out", 2: "Echo to USB Out", 3: "Echo to Both"}),
                
    9: Parameter(9, "MIDI Echo DIN In", ParameterCategory.MIDI_COMMUNICATION, ParameterType.CHOICE,
                0, "Echo DIN MIDI input to outputs", 
                choices={0: "Off", 1: "Echo to DIN Out", 2: "Echo to USB Out", 3: "Echo to Both"}),
                
    10: Parameter(10, "MIDI Input Channel", ParameterCategory.MIDI_COMMUNICATION, ParameterType.MIDI_CHANNEL,
                 0, "MIDI input channel (1-16)"),
                 
    11: Parameter(11, "MIDI Output Channel", ParameterCategory.MIDI_COMMUNICATION, ParameterType.MIDI_CHANNEL,
                 0, "MIDI output channel (1-16)"),
                 
    12: Parameter(12, "MIDI Out Filter - Keys", ParameterCategory.MIDI_COMMUNICATION, ParameterType.TOGGLE,
                 1, "Send MIDI note messages from keyboard"),
                 
    13: Parameter(13, "MIDI Out Filter - Wheels", ParameterCategory.MIDI_COMMUNICATION, ParameterType.TOGGLE,
                 1, "Send MIDI CC from pitch/mod wheels"),
                 
    14: Parameter(14, "MIDI Out Filter - Panel", ParameterCategory.MIDI_COMMUNICATION, ParameterType.TOGGLE,
                 1, "Send MIDI CC from panel controls"),
                 
    15: Parameter(15, "Output 14-bit MIDI CCs", ParameterCategory.MIDI_COMMUNICATION, ParameterType.TOGGLE,
                 0, "Use 14-bit resolution for MIDI CC output"),
                 
    16: Parameter(16, "Local Control: Keys", ParameterCategory.MIDI_COMMUNICATION, ParameterType.TOGGLE,
                 1, "Keyboard controls internal synth engine"),
                 
    17: Parameter(17, "Local Control: Wheels", ParameterCategory.MIDI_COMMUNICATION, ParameterType.TOGGLE,
                 1, "Pitch/Mod wheels control internal synth engine"),
                 
    18: Parameter(18, "Local Control: Panel", ParameterCategory.MIDI_COMMUNICATION, ParameterType.TOGGLE,
                 1, "Panel controls affect internal synth engine"),
                 
    19: Parameter(19, "Local Control: Arp/Seq", ParameterCategory.MIDI_COMMUNICATION, ParameterType.TOGGLE,
                 1, "Arp/Sequencer controls internal synth engine"),
                 
    20: Parameter(20, "Sequence Transpose Mode", ParameterCategory.ARP_SEQUENCER, ParameterType.CHOICE,
                 0, "How sequences transpose with keyboard input",
                 choices={0: "Relative to First Note", 1: "Relative to Middle C"}),
                 
    21: Parameter(21, "Arp/Seq Keyed Timing Reset", ParameterCategory.ARP_SEQUENCER, ParameterType.TOGGLE,
                 0, "Reset master clock when key is pressed"),
                 
    22: Parameter(22, "Arp FW/BW Repeats", ParameterCategory.ARP_SEQUENCER, ParameterType.TOGGLE,
                 1, "Repeat end notes when direction changes"),
                 
    23: Parameter(23, "Arp/Seq Swing", ParameterCategory.ARP_SEQUENCER, ParameterType.RANGE,
                 8192, "Rhythmic swing amount for arp/sequencer",
                 min_value=0, max_value=16383, human_readable_func=swing_percentage,
                 tooltip="Swing timing: 50% = straight, <50% = early, >50% = late"),
                 
    24: Parameter(24, "Sequence Keyboard Control", ParameterCategory.ARP_SEQUENCER, ParameterType.TOGGLE,
                 1, "Keyboard controls sequence playback"),
                 
    25: Parameter(25, "Delay Sequence Change", ParameterCategory.ARP_SEQUENCER, ParameterType.TOGGLE,
                 0, "Wait for sequence end before changing"),
                 
    26: Parameter(26, "Sequence Keyed Restart", ParameterCategory.ARP_SEQUENCER, ParameterType.TOGGLE,
                 0, "Restart sequence when keyboard control changes"),
                 
    27: Parameter(27, "Arp/Seq Clock Input Mode", ParameterCategory.ARP_SEQUENCER, ParameterType.CHOICE,
                 0, "How external clock input works",
                 choices={0: "Clock", 1: "Step-Advance Trigger"}),
                 
    28: Parameter(28, "Arp/Seq Clock Output", ParameterCategory.ARP_SEQUENCER, ParameterType.CHOICE,
                 1, "When to send clock output",
                 choices={0: "Always", 1: "Only When Playing"}),
                 
    29: Parameter(29, "Arp MIDI Output", ParameterCategory.ARP_SEQUENCER, ParameterType.TOGGLE,
                 1, "Send MIDI notes from arp/sequencer"),
                 
    30: Parameter(30, "MIDI Clock Input", ParameterCategory.MIDI_COMMUNICATION, ParameterType.CHOICE,
                 0, "MIDI clock and start/stop input behavior",
                 choices={0: "Follow Clock + Start/Stop", 1: "Follow Clock Only", 2: "Ignore All"}),
                 
    31: Parameter(31, "MIDI Clock Output", ParameterCategory.MIDI_COMMUNICATION, ParameterType.CHOICE,
                 0, "MIDI clock and start/stop output behavior", 
                 choices={0: "Send Clock + Start/Stop", 1: "Send Clock Only", 2: "Send Nothing"}),
                 
    32: Parameter(32, "Follow Song Position Pointer", ParameterCategory.MIDI_COMMUNICATION, ParameterType.TOGGLE,
                 1, "Respond to MIDI song position"),
                 
    # Remove the old separate parameters and keep the combined ones
    # Parameters 31, 33, 34 are now handled by the combined parameters 30 and 32
    # Skip these parameter IDs to maintain SysEx compatibility
    
    35: Parameter(35, "Clock Input PPQN", ParameterCategory.ARP_SEQUENCER, ParameterType.CHOICE,
                 3, "Clock input resolution",
                 choices={0: "1 PPQN", 1: "2 PPQN", 2: "3 PPQN", 3: "4 PPQN", 4: "5 PPQN",
                         5: "6 PPQN", 6: "7 PPQN", 7: "8 PPQN", 8: "9 PPQN", 9: "10 PPQN",
                         10: "11 PPQN", 11: "12 PPQN", 12: "24 PPQN", 13: "48 PPQN"},
                 human_readable_func=ppqn_display),
                 
    36: Parameter(36, "Clock Output PPQN", ParameterCategory.ARP_SEQUENCER, ParameterType.CHOICE,
                 3, "Clock output resolution", 
                 choices={0: "1 PPQN", 1: "2 PPQN", 2: "3 PPQN", 3: "4 PPQN", 4: "5 PPQN",
                         5: "6 PPQN", 6: "7 PPQN", 7: "8 PPQN", 8: "9 PPQN", 9: "10 PPQN",
                         10: "11 PPQN", 11: "12 PPQN", 12: "24 PPQN", 13: "48 PPQN"},
                 human_readable_func=ppqn_display),
                 
    37: Parameter(37, "Pitch Bend Range", ParameterCategory.PERFORMANCE_KEYBOARD, ParameterType.RANGE,
                 2, "Pitch wheel bend range in semitones",
                 min_value=0, max_value=12, human_readable_func=semitones_display),
                 
    38: Parameter(38, "Keyboard Octave Transpose", ParameterCategory.PERFORMANCE_KEYBOARD, ParameterType.CHOICE,
                 2, "Keyboard octave transpose setting",
                 choices={0: "-2 Octaves", 1: "-1 Octave", 2: "Normal", 3: "+1 Octave", 4: "+2 Octaves"}),
                 
    39: Parameter(39, "Delayed Keyboard Octave Shift", ParameterCategory.PERFORMANCE_KEYBOARD, ParameterType.TOGGLE,
                 1, "Delay octave shifts until new notes"),
                 
    40: Parameter(40, "Glide Type", ParameterCategory.PERFORMANCE_KEYBOARD, ParameterType.CHOICE,
                 0, "Portamento/glide behavior type",
                 choices={0: "Linear Constant Rate", 1: "Linear Constant Time", 2: "Exponential"}),
                 
    41: Parameter(41, "Gated Glide", ParameterCategory.PERFORMANCE_KEYBOARD, ParameterType.TOGGLE,
                 1, "Glide only occurs while keys are held"),
                 
    42: Parameter(42, "Legato Glide", ParameterCategory.PERFORMANCE_KEYBOARD, ParameterType.TOGGLE,
                 1, "Glide only when playing legato"),
                 
    43: Parameter(43, "Osc 2 Freq Knob Range", ParameterCategory.AUDIO_CV, ParameterType.RANGE,
                 7, "Oscillator 2 frequency knob range in semitones",
                 min_value=0, max_value=24, human_readable_func=semitones_display),
                 
    44: Parameter(44, "Osc 3 Freq Knob Range", ParameterCategory.AUDIO_CV, ParameterType.RANGE,
                 7, "Oscillator 3 frequency knob range in semitones", 
                 min_value=0, max_value=24, human_readable_func=semitones_display),
                 
    45: Parameter(45, "Osc 4 Freq Knob Range", ParameterCategory.AUDIO_CV, ParameterType.RANGE,
                 7, "Oscillator 4 frequency knob range in semitones",
                 min_value=0, max_value=24, human_readable_func=semitones_display),
                 
    46: Parameter(46, "Hard Sync Enable", ParameterCategory.AUDIO_CV, ParameterType.TOGGLE,
                 0, "Enable hard sync functionality"),
                 
    47: Parameter(47, "Osc 2 Hard Sync", ParameterCategory.AUDIO_CV, ParameterType.TOGGLE,
                 0, "Sync Oscillator 2 to Oscillator 1"),
                 
    48: Parameter(48, "Osc 3 Hard Sync", ParameterCategory.AUDIO_CV, ParameterType.TOGGLE,
                 0, "Sync Oscillator 3 to Oscillator 2"),
                 
    49: Parameter(49, "Osc 4 Hard Sync", ParameterCategory.AUDIO_CV, ParameterType.TOGGLE,
                 0, "Sync Oscillator 4 to Oscillator 3"),
                 
    50: Parameter(50, "Delay Ping Pong", ParameterCategory.AUDIO_CV, ParameterType.TOGGLE,
                 0, "Enable ping pong delay mode"),
                 
    51: Parameter(51, "Delay Sync", ParameterCategory.AUDIO_CV, ParameterType.TOGGLE,
                 0, "Sync delay to clock"),
                 
    52: Parameter(52, "Delay Filter Brightness", ParameterCategory.AUDIO_CV, ParameterType.CHOICE,
                 1, "Delay output filtering",
                 choices={0: "Dark", 1: "Bright"}),
                 
    53: Parameter(53, "Delay CV Sync-Bend", ParameterCategory.AUDIO_CV, ParameterType.TOGGLE,
                 0, "Allow CV to bend sync'd delay time"),
                 
    54: Parameter(54, "Tap-Tempo Clock Division Persistence", ParameterCategory.ARP_SEQUENCER, ParameterType.TOGGLE,
                 0, "Maintain clock divisions when using tap tempo"),
                 
    55: Parameter(55, "Paraphony Mode", ParameterCategory.PERFORMANCE_KEYBOARD, ParameterType.CHOICE,
                 0, "Voice assignment mode",
                 choices={0: "Mono (1 Voice)", 1: "Duo (2 Voice)", 2: "Quad (4 Voice)"}),
                 
    56: Parameter(56, "Paraphonic Unison", ParameterCategory.PERFORMANCE_KEYBOARD, ParameterType.TOGGLE,
                 0, "All oscillators sound even in paraphonic modes"),
                 
    57: Parameter(57, "Multi Trig", ParameterCategory.PERFORMANCE_KEYBOARD, ParameterType.TOGGLE,
                 0, "Envelope retriggering behavior"),
                 
    58: Parameter(58, "Pitch Variance", ParameterCategory.ADVANCED, ParameterType.RANGE,
                 0, "Random pitch variation per note",
                 min_value=0, max_value=400, human_readable_func=pitch_variance_cents),
                 
    # CV Output Ranges (Group 3)
    59: Parameter(59, "KB CV OUT Range", ParameterCategory.AUDIO_CV, ParameterType.CHOICE,
                 0, "Keyboard CV output voltage range",
                 choices={0: "-5V to +5V", 1: "0V to +10V"}),
                 
    60: Parameter(60, "Arp/Seq CV OUT Range", ParameterCategory.AUDIO_CV, ParameterType.CHOICE,
                 0, "Arpeggiator/Sequencer CV output range",
                 choices={0: "-5V to +5V", 1: "0V to +10V"}),
                 
    61: Parameter(61, "KB VEL OUT Range", ParameterCategory.AUDIO_CV, ParameterType.CHOICE,
                 0, "Keyboard velocity CV output range", 
                 choices={0: "0V to +5V", 1: "0V to +10V"}),
                 
    62: Parameter(62, "Arp/Seq VEL OUT Range", ParameterCategory.AUDIO_CV, ParameterType.CHOICE,
                 0, "Arp/Seq velocity CV output range",
                 choices={0: "0V to +5V", 1: "0V to +10V"}),
                 
    63: Parameter(63, "KB AT OUT Range", ParameterCategory.AUDIO_CV, ParameterType.CHOICE,
                 0, "Keyboard aftertouch CV output range",
                 choices={0: "0V to +5V", 1: "0V to +10V"}),
                 
    64: Parameter(64, "MOD WHL OUT Range", ParameterCategory.AUDIO_CV, ParameterType.CHOICE,
                 0, "Modulation wheel CV output range",
                 choices={0: "0V to +5V", 1: "0V to +10V"}),
                 
    65: Parameter(65, "KB GATE OUT Range", ParameterCategory.AUDIO_CV, ParameterType.CHOICE,
                 0, "Keyboard gate CV output voltage",
                 choices={0: "+5V", 1: "+10V"}),
                 
    66: Parameter(66, "Arp/Seq GATE OUT Range", ParameterCategory.AUDIO_CV, ParameterType.CHOICE,
                 0, "Arp/Seq gate CV output voltage",
                 choices={0: "+5V", 1: "+10V"}),
                 
    67: Parameter(67, "Round-Robin Mode", ParameterCategory.PERFORMANCE_KEYBOARD, ParameterType.CHOICE,
                 1, "Voice assignment pattern in paraphonic mode",
                 choices={0: "Off", 1: "On with Reset", 2: "On"}),
                 
    68: Parameter(68, "Restore Stolen Voices", ParameterCategory.PERFORMANCE_KEYBOARD, ParameterType.TOGGLE,
                 0, "Resume stolen voices when keys released"),
                 
    69: Parameter(69, "Update Unison on Note-Off", ParameterCategory.PERFORMANCE_KEYBOARD, ParameterType.TOGGLE,
                 0, "Reassign oscillators when notes released",
                 dependencies=["Paraphonic Unison"]),
                 
    70: Parameter(70, "Mod Oscillator Square Wave Polarity", ParameterCategory.ADVANCED, ParameterType.CHOICE,
                 1, "Modulation LFO square wave behavior",
                 choices={0: "Unipolar", 1: "Bipolar"}),
                 
    71: Parameter(71, "Noise Filter Cutoff", ParameterCategory.AUDIO_CV, ParameterType.RANGE,
                 16383, "High-pass filter cutoff for noise generator",
                 min_value=0, max_value=16383),
                 
    72: Parameter(72, "Arp/Seq Random Repeats", ParameterCategory.ARP_SEQUENCER, ParameterType.CHOICE,
                 1, "Allow repeated notes in random mode",
                 choices={0: "No Repeats", 1: "Allow Repeats"}),
                 
    73: Parameter(73, "ARP/SEQ CV OUT Mirrors KB CV", ParameterCategory.AUDIO_CV, ParameterType.TOGGLE,
                 0, "Arp/Seq outputs mirror keyboard when not running"),
                 
    74: Parameter(74, "KB CV OUT Mirrors ARP/SEQ CV", ParameterCategory.AUDIO_CV, ParameterType.TOGGLE,
                 0, "Keyboard outputs mirror arp/seq when running"),
                 
    75: Parameter(75, "MIDI Velocity Curves", ParameterCategory.MIDI_COMMUNICATION, ParameterType.CHOICE,
                 0, "Keyboard velocity response curve",
                 choices={0: "Base", 1: "Linear", 2: "Hard", 3: "Soft"}),
}

# Organize parameters by category for UI tabs
def get_parameters_by_category() -> Dict[ParameterCategory, List[Parameter]]:
    """Return parameters organized by category for UI layout"""
    categories = {}
    for param in PARAMETERS.values():
        if param.category not in categories:
            categories[param.category] = []
        categories[param.category].append(param)
    
    # Sort parameters within each category by name
    for category in categories:
        categories[category].sort(key=lambda p: p.name)
    
    return categories

def get_parameter_by_id(param_id: int) -> Optional[Parameter]:
    """Get parameter by ID"""
    return PARAMETERS.get(param_id)

def get_all_parameter_defaults() -> Dict[int, int]:
    """Get all default values for factory reset"""
    return {pid: param.default_value for pid, param in PARAMETERS.items()}