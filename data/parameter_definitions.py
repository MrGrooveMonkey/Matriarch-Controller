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
    PERFORMANCE = "Performance"
    ARP_SEQ = "Arp/Seq"
    MIDI_CONFIG = "MIDI/Config"
    CV = "CV"
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
    """Convert swing value 0-16383 to percentage (22% to 78% range)"""
    # Map 0-16383 to 22-78% range
    percent = 22 + (value / 16383.0) * (78 - 22)
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
# Parameter definitions based on Matriarch manual
PARAMETERS = {
    # Advanced Tab
    0: Parameter(
        param_id=0,
        name="Unit ID",
        description="MIDI Unit ID (0-15)",
        param_type=ParameterType.RANGE,
        min_value=0,
        max_value=15,
        default_value=0,
        category=ParameterCategory.ADVANCED,
        tooltip="MIDI Unit ID (0-15)"
    ),
    1: Parameter(
        param_id=1,
        name="Tuning Scale",
        description="Select tuning scale (0 = 12-TET)",
        param_type=ParameterType.RANGE,
        min_value=0,
        max_value=31,
        default_value=0,
        category=ParameterCategory.ADVANCED,
        tooltip="Select tuning scale (0 = 12-TET)"
    ),
    2: Parameter(
        param_id=2,
        name="Knob Mode",
        description="How knobs respond when values change",
        param_type=ParameterType.CHOICE,
        choices={0: "Snap", 1: "Pass-Thru", 2: "Relative"},
        default_value=2,
        category=ParameterCategory.ADVANCED,
        tooltip="How knobs respond when values change"
    ),
    76: Parameter(
        param_id=76,
        name="Load Default Settings",
        description="Reset all global parameters to defaults",
        param_type=ParameterType.TOGGLE,
        default_value=0,
        category=ParameterCategory.ADVANCED,
        tooltip="Reset all global parameters to defaults"
    ),

    # Performance Tab
    3: Parameter(
        param_id=3,
        name="Note Priority",
        description="Which note takes priority in monophonic mode",
        param_type=ParameterType.CHOICE,
        choices={0: "Low", 1: "High", 2: "Last Note"},
        default_value=2,
        category=ParameterCategory.PERFORMANCE,
        tooltip="Which note takes priority in monophonic mode"
    ),
    37: Parameter(
        param_id=37,
        name="Pitch Bend Range",
        description="Pitch bend wheel range in semitones",
        param_type=ParameterType.RANGE,
        min_value=0,
        max_value=12,
        default_value=2,
        category=ParameterCategory.PERFORMANCE,
        tooltip="Pitch bend wheel range in semitones"
    ),
    38: Parameter(
        param_id=38,
        name="Keyboard Octave Transpose",
        description="Transpose keyboard by octaves",
        param_type=ParameterType.CHOICE,
        choices={0: "-2", 1: "-1", 2: "0", 3: "+1", 4: "+2"},
        default_value=2,
        category=ParameterCategory.PERFORMANCE,
        tooltip="Transpose keyboard by octaves"
    ),
    39: Parameter(
        param_id=39,
        name="Delayed Keyboard Octave Shift",
        description="Delay octave shift until new notes are played",
        param_type=ParameterType.TOGGLE,
        default_value=1,
        category=ParameterCategory.PERFORMANCE,
        tooltip="Delay octave shift until new notes are played"
    ),
    40: Parameter(
        param_id=40,
        name="Glide Type",
        description="How glide transitions between notes",
        param_type=ParameterType.CHOICE,
        choices={0: "Linear Constant Rate", 1: "Linear Constant Time", 2: "Exponential"},
        default_value=0,
        category=ParameterCategory.PERFORMANCE,
        tooltip="How glide transitions between notes"
    ),
    41: Parameter(
        param_id=41,
        name="Gated Glide",
        description="Glide only while keys are held",
        param_type=ParameterType.TOGGLE,
        default_value=1,
        category=ParameterCategory.PERFORMANCE,
        tooltip="Glide only while keys are held"
    ),
    42: Parameter(
        param_id=42,
        name="Legato Glide",
        description="Glide only between overlapping notes",
        param_type=ParameterType.TOGGLE,
        default_value=1,
        category=ParameterCategory.PERFORMANCE,
        tooltip="Glide only between overlapping notes"
    ),
    43: Parameter(
        param_id=43,
        name="Osc 2 Freq Knob Range",
        description="Range of Oscillator 2 frequency knob in semitones",
        param_type=ParameterType.RANGE,
        min_value=0,
        max_value=24,
        default_value=7,
        category=ParameterCategory.PERFORMANCE,
        tooltip="Range of Oscillator 2 frequency knob in semitones"
    ),
    44: Parameter(
        param_id=44,
        name="Osc 3 Freq Knob Range",
        description="Range of Oscillator 3 frequency knob in semitones",
        param_type=ParameterType.RANGE,
        min_value=0,
        max_value=24,
        default_value=7,
        category=ParameterCategory.PERFORMANCE,
        tooltip="Range of Oscillator 3 frequency knob in semitones"
    ),
    45: Parameter(
        param_id=45,
        name="Osc 4 Freq Knob Range",
        description="Range of Oscillator 4 frequency knob in semitones",
        param_type=ParameterType.RANGE,
        min_value=0,
        max_value=24,
        default_value=7,
        category=ParameterCategory.PERFORMANCE,
        tooltip="Range of Oscillator 4 frequency knob in semitones"
    ),
    46: Parameter(
        param_id=46,
        name="Hard Sync Enable",
        description="Enable hard sync for oscillators",
        param_type=ParameterType.TOGGLE,
        default_value=0,
        category=ParameterCategory.PERFORMANCE,
        tooltip="Enable hard sync for oscillators"
    ),
    47: Parameter(
        param_id=47,
        name="Osc 2 Hard Sync",
        description="Hard sync Oscillator 2 to Oscillator 1",
        param_type=ParameterType.TOGGLE,
        default_value=0,
        category=ParameterCategory.PERFORMANCE,
        tooltip="Hard sync Oscillator 2 to Oscillator 1"
    ),
    48: Parameter(
        param_id=48,
        name="Osc 3 Hard Sync",
        description="Hard sync Oscillator 3 to Oscillator 2",
        param_type=ParameterType.TOGGLE,
        default_value=0,
        category=ParameterCategory.PERFORMANCE,
        tooltip="Hard sync Oscillator 3 to Oscillator 2"
    ),
    49: Parameter(
        param_id=49,
        name="Osc 4 Hard Sync",
        description="Hard sync Oscillator 4 to Oscillator 3",
        param_type=ParameterType.TOGGLE,
        default_value=0,
        category=ParameterCategory.PERFORMANCE,
        tooltip="Hard sync Oscillator 4 to Oscillator 3"
    ),
    50: Parameter(
        param_id=50,
        name="Delay Ping Pong",
        description="Enable ping pong delay effect",
        param_type=ParameterType.TOGGLE,
        default_value=0,
        category=ParameterCategory.PERFORMANCE,
        tooltip="Enable ping pong delay effect"
    ),
    51: Parameter(
        param_id=51,
        name="Delay Sync",
        description="Sync delay to tempo",
        param_type=ParameterType.TOGGLE,
        default_value=0,
        category=ParameterCategory.PERFORMANCE,
        tooltip="Sync delay to tempo"
    ),
    52: Parameter(
        param_id=52,
        name="Delay Filter Brightness",
        description="Delay output filter tone",
        param_type=ParameterType.CHOICE,
        choices={0: "Dark", 1: "Bright"},
        default_value=1,
        category=ParameterCategory.PERFORMANCE,
        tooltip="Delay output filter tone"
    ),
    53: Parameter(
        param_id=53,
        name="Delay CV Sync-Bend",
        description="Allow CV to bend synced delay time",
        param_type=ParameterType.TOGGLE,
        default_value=0,
        category=ParameterCategory.PERFORMANCE,
        tooltip="Allow CV to bend synced delay time"
    ),
    54: Parameter(
        param_id=54,
        name="Tap-Tempo Clock Division Persistence",
        description="Remember clock division when using tap tempo",
        param_type=ParameterType.TOGGLE,
        default_value=0,
        category=ParameterCategory.PERFORMANCE,
        tooltip="Remember clock division when using tap tempo"
    ),
    55: Parameter(
        param_id=55,
        name="Paraphony Mode",
        description="Number of voices available",
        param_type=ParameterType.CHOICE,
        choices={0: "Mono", 1: "Duo", 2: "Quad"},
        default_value=0,
        category=ParameterCategory.PERFORMANCE,
        tooltip="Number of voices available"
    ),
    56: Parameter(
        param_id=56,
        name="Paraphonic Unison",
        description="All oscillators play in paraphonic modes",
        param_type=ParameterType.TOGGLE,
        default_value=0,
        category=ParameterCategory.PERFORMANCE,
        tooltip="All oscillators play in paraphonic modes"
    ),
    57: Parameter(
        param_id=57,
        name="Multi Trig",
        description="Retrigger envelopes on each new note",
        param_type=ParameterType.TOGGLE,
        default_value=0,
        category=ParameterCategory.PERFORMANCE,
        tooltip="Retrigger envelopes on each new note"
    ),
    58: Parameter(
        param_id=58,
        name="Pitch Variance",
        description="Random pitch variation per note (0.1 cent units)",
        param_type=ParameterType.RANGE,
        min_value=0,
        max_value=400,
        default_value=0,
        category=ParameterCategory.PERFORMANCE,
        tooltip="Random pitch variation per note (0.1 cent units)"
    ),
    70: Parameter(
        param_id=70,
        name="Mod Oscillator Square Wave Polarity",
        description="Modulation oscillator square wave output type",
        param_type=ParameterType.CHOICE,
        choices={0: "Unipolar", 1: "Bipolar"},
        default_value=1,
        category=ParameterCategory.PERFORMANCE,
        tooltip="Modulation oscillator square wave output type"
    ),
    71: Parameter(
        param_id=71,
        name="Noise Filter Cutoff",
        description="High-pass filter cutoff for noise generator",
        param_type=ParameterType.RANGE,
        min_value=0,
        max_value=16383,
        default_value=16383,
        category=ParameterCategory.PERFORMANCE,
        tooltip="High-pass filter cutoff for noise generator"
    ),

    # Arp/Seq Tab
    20: Parameter(
        param_id=20,
        name="Sequence Transpose Mode",
        description="How sequences are transposed",
        param_type=ParameterType.CHOICE,
        choices={0: "Relative to First Note", 1: "Relative to Middle C"},
        default_value=0,
        category=ParameterCategory.ARP_SEQ,
        tooltip="How sequences are transposed"
    ),
    21: Parameter(
        param_id=21,
        name="Arp/Seq Keyed Timing Reset",
        description="Reset timing when new notes are played",
        param_type=ParameterType.TOGGLE,
        default_value=0,
        category=ParameterCategory.ARP_SEQ,
        tooltip="Reset timing when new notes are played"
    ),
    22: Parameter(
        param_id=22,
        name="Arp FW/BW Repeats",
        description="Repeat end notes in forward/backward arpeggio",
        param_type=ParameterType.TOGGLE,
        default_value=1,
        category=ParameterCategory.ARP_SEQ,
        tooltip="Repeat end notes in forward/backward arpeggio"
    ),
    23: Parameter(
        param_id=23,
        name="Arp/Seq Swing",
        description="Swing amount for arpeggiator and sequencer",
        param_type=ParameterType.RANGE,
        min_value=0,
        max_value=16383,
        default_value=8192,
        category=ParameterCategory.ARP_SEQ,
        tooltip="Swing amount for arpeggiator and sequencer",
        human_readable_func=lambda value: f"{22 + (value / 16383.0) * 56:.1f}%"
    ),
    24: Parameter(
        param_id=24,
        name="Sequence Keyboard Control",
        description="Keyboard controls sequence playback",
        param_type=ParameterType.TOGGLE,
        default_value=1,
        category=ParameterCategory.ARP_SEQ,
        tooltip="Keyboard controls sequence playback"
    ),
    25: Parameter(
        param_id=25,
        name="Delay Sequence Change",
        description="Wait for sequence to finish before changing",
        param_type=ParameterType.TOGGLE,
        default_value=0,
        category=ParameterCategory.ARP_SEQ,
        tooltip="Wait for sequence to finish before changing"
    ),
    26: Parameter(
        param_id=26,
        name="Sequence Keyed Restart",
        description="Restart sequence when latch is used",
        param_type=ParameterType.TOGGLE,
        default_value=0,
        category=ParameterCategory.ARP_SEQ,
        tooltip="Restart sequence when latch is used"
    ),
    27: Parameter(
        param_id=27,
        name="Arp/Seq Clock Input Mode",
        description="How external clock input is interpreted",
        param_type=ParameterType.CHOICE,
        choices={0: "Clock", 1: "Step-Advance"},
        default_value=0,
        category=ParameterCategory.ARP_SEQ,
        tooltip="How external clock input is interpreted"
    ),
    28: Parameter(
        param_id=28,
        name="Arp/Seq Clock Output",
        description="When to output clock signals",
        param_type=ParameterType.CHOICE,
        choices={0: "Always", 1: "Only When Playing"},
        default_value=1,
        category=ParameterCategory.ARP_SEQ,
        tooltip="When to output clock signals"
    ),
    29: Parameter(
        param_id=29,
        name="Arp MIDI Output",
        description="Send arpeggiator notes via MIDI",
        param_type=ParameterType.TOGGLE,
        default_value=1,
        category=ParameterCategory.ARP_SEQ,
        tooltip="Send arpeggiator notes via MIDI"
    ),
    72: Parameter(
        param_id=72,
        name="Arp/Seq Random Repeats",
        description="Allow note repeats in random mode",
        param_type=ParameterType.TOGGLE,
        default_value=1,
        category=ParameterCategory.ARP_SEQ,
        tooltip="Allow note repeats in random mode"
    ),
    73: Parameter(
        param_id=73,
        name="ARP/SEQ CV OUT Mirrors KB CV",
        description="Arp/Seq CV outputs follow keyboard when not running",
        param_type=ParameterType.TOGGLE,
        default_value=0,
        category=ParameterCategory.ARP_SEQ,
        tooltip="Arp/Seq CV outputs follow keyboard when not running"
    ),
    74: Parameter(
        param_id=74,
        name="KB CV OUT Mirrors ARP/SEQ CV",
        description="Keyboard CV outputs follow Arp/Seq when running",
        param_type=ParameterType.TOGGLE,
        default_value=0,
        category=ParameterCategory.ARP_SEQ,
        tooltip="Keyboard CV outputs follow Arp/Seq when running"
    ),

    # MIDI/Config Tab
    4: Parameter(
        param_id=4,
        name="Send Program Change",
        description="Send MIDI program change messages",
        param_type=ParameterType.TOGGLE,
        default_value=0,
        category=ParameterCategory.MIDI_CONFIG,
        tooltip="Send MIDI program change messages"
    ),
    5: Parameter(
        param_id=5,
        name="Receive Program Change",
        description="Respond to MIDI program change messages",
        param_type=ParameterType.TOGGLE,
        default_value=1,
        category=ParameterCategory.MIDI_CONFIG,
        tooltip="Respond to MIDI program change messages"
    ),
    6: Parameter(
        param_id=6,
        name="MIDI Input Ports",
        description="Which MIDI inputs to use",
        param_type=ParameterType.CHOICE,
        choices={0: "None", 1: "DIN Only", 2: "USB Only", 3: "Both"},
        default_value=3,
        category=ParameterCategory.MIDI_CONFIG,
        tooltip="Which MIDI inputs to use"
    ),
    7: Parameter(
        param_id=7,
        name="MIDI Output Ports",
        description="Which MIDI outputs to use",
        param_type=ParameterType.CHOICE,
        choices={0: "None", 1: "DIN Only", 2: "USB Only", 3: "Both"},
        default_value=3,
        category=ParameterCategory.MIDI_CONFIG,
        tooltip="Which MIDI outputs to use"
    ),
    8: Parameter(
        param_id=8,
        name="MIDI Echo USB In",
        description="Echo USB MIDI input to outputs",
        param_type=ParameterType.CHOICE,
        choices={0: "Off", 1: "Echo to DIN", 2: "Echo to USB", 3: "Echo to Both"},
        default_value=0,
        category=ParameterCategory.MIDI_CONFIG,
        tooltip="Echo USB MIDI input to outputs"
    ),
    9: Parameter(
        param_id=9,
        name="MIDI Echo DIN In",
        description="Echo DIN MIDI input to outputs",
        param_type=ParameterType.CHOICE,
        choices={0: "Off", 1: "Echo to DIN", 2: "Echo to USB", 3: "Echo to Both"},
        default_value=0,
        category=ParameterCategory.MIDI_CONFIG,
        tooltip="Echo DIN MIDI input to outputs"
    ),
    10: Parameter(
        param_id=10,
        name="MIDI Input Channel",
        description="MIDI input channel (1-16)",
        param_type=ParameterType.MIDI_CHANNEL,
        default_value=0,
        category=ParameterCategory.MIDI_CONFIG,
        tooltip="MIDI input channel (1-16)"
    ),
    11: Parameter(
        param_id=11,
        name="MIDI Output Channel",
        description="MIDI output channel (1-16)",
        param_type=ParameterType.MIDI_CHANNEL,
        default_value=0,
        category=ParameterCategory.MIDI_CONFIG,
        tooltip="MIDI output channel (1-16)"
    ),
    12: Parameter(
        param_id=12,
        name="MIDI Out Filter - Keys",
        description="Send keyboard MIDI note messages",
        param_type=ParameterType.TOGGLE,
        default_value=1,
        category=ParameterCategory.MIDI_CONFIG,
        tooltip="Send keyboard MIDI note messages"
    ),
    13: Parameter(
        param_id=13,
        name="MIDI Out Filter - Wheels",
        description="Send pitch and mod wheel MIDI messages",
        param_type=ParameterType.TOGGLE,
        default_value=1,
        category=ParameterCategory.MIDI_CONFIG,
        tooltip="Send pitch and mod wheel MIDI messages"
    ),
    14: Parameter(
        param_id=14,
        name="MIDI Out Filter - Panel",
        description="Send panel control MIDI messages",
        param_type=ParameterType.TOGGLE,
        default_value=1,
        category=ParameterCategory.MIDI_CONFIG,
        tooltip="Send panel control MIDI messages"
    ),
    15: Parameter(
        param_id=15,
        name="Output 14-bit MIDI CCs",
        description="Use 14-bit MIDI CC resolution",
        param_type=ParameterType.TOGGLE,
        default_value=0,
        category=ParameterCategory.MIDI_CONFIG,
        tooltip="Use 14-bit MIDI CC resolution"
    ),
    16: Parameter(
        param_id=16,
        name="Local Control: Keys",
        description="Keyboard controls internal sound engine",
        param_type=ParameterType.TOGGLE,
        default_value=1,
        category=ParameterCategory.MIDI_CONFIG,
        tooltip="Keyboard controls internal sound engine"
    ),
    17: Parameter(
        param_id=17,
        name="Local Control: Wheels",
        description="Wheels control internal sound engine",
        param_type=ParameterType.TOGGLE,
        default_value=1,
        category=ParameterCategory.MIDI_CONFIG,
        tooltip="Wheels control internal sound engine"
    ),
    18: Parameter(
        param_id=18,
        name="Local Control: Panel",
        description="Panel controls internal sound engine",
        param_type=ParameterType.TOGGLE,
        default_value=1,
        category=ParameterCategory.MIDI_CONFIG,
        tooltip="Panel controls internal sound engine"
    ),
    19: Parameter(
        param_id=19,
        name="Local Control: Arp/Seq",
        description="Arp/Seq controls internal sound engine",
        param_type=ParameterType.TOGGLE,
        default_value=1,
        category=ParameterCategory.MIDI_CONFIG,
        tooltip="Arp/Seq controls internal sound engine"
    ),
    30: Parameter(
        param_id=30,
        name="MIDI Clock Input",
        description="How to respond to MIDI clock",
        param_type=ParameterType.CHOICE,
        choices={0: "Follow Clock + Start/Stop", 1: "Follow Clock Only", 2: "Ignore All"},
        default_value=0,
        category=ParameterCategory.MIDI_CONFIG,
        tooltip="How to respond to MIDI clock"
    ),
    31: Parameter(
        param_id=31,
        name="MIDI Clock Output",
        description="What MIDI clock data to send",
        param_type=ParameterType.CHOICE,
        choices={0: "Send Clock + Start/Stop", 1: "Send Clock Only", 2: "Send Nothing"},
        default_value=0,
        category=ParameterCategory.MIDI_CONFIG,
        tooltip="What MIDI clock data to send"
    ),
    32: Parameter(
        param_id=32,
        name="Follow Song Position Pointer",
        description="Respond to MIDI song position messages",
        param_type=ParameterType.TOGGLE,
        default_value=1,
        category=ParameterCategory.MIDI_CONFIG,
        tooltip="Respond to MIDI song position messages"
    ),
    35: Parameter(
        param_id=35,
        name="Clock Input PPQN",
        description="Pulses per quarter note for clock input",
        param_type=ParameterType.CHOICE,
        choices={0: "1", 1: "2", 2: "3", 3: "4", 4: "5", 5: "6", 6: "7", 7: "8", 8: "9", 9: "10", 10: "11", 11: "12", 12: "24", 13: "48"},
        default_value=3,
        category=ParameterCategory.MIDI_CONFIG,
        tooltip="Pulses per quarter note for clock input"
    ),
    36: Parameter(
        param_id=36,
        name="Clock Output PPQN",
        description="Pulses per quarter note for clock output",
        param_type=ParameterType.CHOICE,
        choices={0: "1", 1: "2", 2: "3", 3: "4", 4: "5", 5: "6", 6: "7", 7: "8", 8: "9", 9: "10", 10: "11", 11: "12", 12: "24", 13: "48"},
        default_value=3,
        category=ParameterCategory.MIDI_CONFIG,
        tooltip="Pulses per quarter note for clock output"
    ),
    67: Parameter(
        param_id=67,
        name="Round-Robin Mode",
        description="How voices are assigned in paraphonic mode",
        param_type=ParameterType.CHOICE,
        choices={0: "Off", 1: "On with Reset", 2: "On"},
        default_value=1,
        category=ParameterCategory.MIDI_CONFIG,
        tooltip="How voices are assigned in paraphonic mode"
    ),
    68: Parameter(
        param_id=68,
        name="Restore Stolen Voices",
        description="Restore notes when voices become available",
        param_type=ParameterType.TOGGLE,
        default_value=0,
        category=ParameterCategory.MIDI_CONFIG,
        tooltip="Restore notes when voices become available"
    ),
    69: Parameter(
        param_id=69,
        name="Update Unison on Note-Off",
        description="Reassign oscillators when notes are released",
        param_type=ParameterType.TOGGLE,
        default_value=0,
        category=ParameterCategory.MIDI_CONFIG,
        tooltip="Reassign oscillators when notes are released"
    ),
    75: Parameter(
        param_id=75,
        name="MIDI Velocity Curves",
        description="Keyboard velocity response curve",
        param_type=ParameterType.CHOICE,
        choices={0: "Base", 1: "Linear", 2: "Hard", 3: "Soft"},
        default_value=0,
        category=ParameterCategory.MIDI_CONFIG,
        tooltip="Keyboard velocity response curve"
    ),

    # CV Tab
    59: Parameter(
        param_id=59,
        name="KB CV OUT Range",
        description="Keyboard CV output voltage range",
        param_type=ParameterType.CHOICE,
        choices={0: "-5V to +5V", 1: "0V to +10V"},
        default_value=0,
        category=ParameterCategory.CV,
        tooltip="Keyboard CV output voltage range"
    ),
    60: Parameter(
        param_id=60,
        name="Arp/Seq CV OUT Range",
        description="Arpeggiator/Sequencer CV output voltage range",
        param_type=ParameterType.CHOICE,
        choices={0: "-5V to +5V", 1: "0V to +10V"},
        default_value=0,
        category=ParameterCategory.CV,
        tooltip="Arpeggiator/Sequencer CV output voltage range"
    ),
    61: Parameter(
        param_id=61,
        name="KB VEL OUT Range",
        description="Keyboard velocity CV output voltage range",
        param_type=ParameterType.CHOICE,
        choices={0: "0V to +5V", 1: "0V to +10V"},
        default_value=0,
        category=ParameterCategory.CV,
        tooltip="Keyboard velocity CV output voltage range"
    ),
    62: Parameter(
        param_id=62,
        name="Arp/Seq VEL OUT Range",
        description="Arpeggiator/Sequencer velocity CV output voltage range",
        param_type=ParameterType.CHOICE,
        choices={0: "0V to +5V", 1: "0V to +10V"},
        default_value=0,
        category=ParameterCategory.CV,
        tooltip="Arpeggiator/Sequencer velocity CV output voltage range"
    ),
    63: Parameter(
        param_id=63,
        name="KB AT OUT Range",
        description="Keyboard aftertouch CV output voltage range",
        param_type=ParameterType.CHOICE,
        choices={0: "0V to +5V", 1: "0V to +10V"},
        default_value=0,
        category=ParameterCategory.CV,
        tooltip="Keyboard aftertouch CV output voltage range"
    ),
    64: Parameter(
        param_id=64,
        name="MOD WHL OUT Range",
        description="Modulation wheel CV output voltage range",
        param_type=ParameterType.CHOICE,
        choices={0: "0V to +5V", 1: "0V to +10V"},
        default_value=0,
        category=ParameterCategory.CV,
        tooltip="Modulation wheel CV output voltage range"
    ),
    65: Parameter(
        param_id=65,
        name="KB GATE OUT Range",
        description="Keyboard gate output voltage level",
        param_type=ParameterType.CHOICE,
        choices={0: "+5V", 1: "+10V"},
        default_value=0,
        category=ParameterCategory.CV,
        tooltip="Keyboard gate output voltage level"
    ),
    66: Parameter(
        param_id=66,
        name="Arp/Seq GATE OUT Range",
        description="Arpeggiator/Sequencer gate output voltage level",
        param_type=ParameterType.CHOICE,
        choices={0: "+5V", 1: "+10V"},
        default_value=0,
        category=ParameterCategory.CV,
        tooltip="Arpeggiator/Sequencer gate output voltage level"
    ),
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
    
    # Return ordered dictionary with categories in the desired order
    ordered_categories = {}
    desired_order = [
        ParameterCategory.PERFORMANCE,
        ParameterCategory.ARP_SEQ,
        ParameterCategory.MIDI_CONFIG,
        ParameterCategory.CV,
        ParameterCategory.ADVANCED
    ]
    
    for category in desired_order:
        if category in categories:
            ordered_categories[category] = categories[category]
    
    return ordered_categories

def get_parameter_by_id(param_id: int) -> Optional[Parameter]:
    """Get parameter by ID"""
    return PARAMETERS.get(param_id)

def get_all_parameter_defaults() -> Dict[int, int]:
    """Get all default values for factory reset"""
    return {pid: param.default_value for pid, param in PARAMETERS.items()}