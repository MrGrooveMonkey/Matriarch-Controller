"""
Matriarch SysEx Message Handling
Based on manual pages 76-79
"""

import mido
from typing import Optional, Tuple, List
import logging

logger = logging.getLogger(__name__)

class MatriarchSysEx:
    """Handles SysEx message creation and parsing for Matriarch"""
    
    # SysEx message structure constants
    SYSEX_START = 0xF0
    SYSEX_END = 0xF7
    MANUFACTURER_ID = [0x04, 0x17]  # Moog Music
    DEVICE_ID = 0x23  # Matriarch device ID
    SET_PARAM_CMD = 0x23
    GET_PARAM_CMD = 0x3E
    
    def __init__(self, unit_id: int = 0):
        """Initialize with Unit ID (default 0)"""
        self.unit_id = unit_id
        
    def create_parameter_query(self, parameter_id: int) -> mido.Message:
        """
        Create SysEx message to query a parameter value
        Format: F0 04 17 3E [Parameter ID] 00 00 00 00 00 00 00 00 00 00 [Unit ID] F7
        """
        data = [
            self.SYSEX_START,
            *self.MANUFACTURER_ID,
            self.GET_PARAM_CMD,
            parameter_id,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            self.unit_id,
            self.SYSEX_END
        ]
        
        return mido.Message('sysex', data=data[1:-1])  # mido handles F0/F7
    
    def create_parameter_set(self, parameter_id: int, value: int) -> mido.Message:
        """
        Create SysEx message to set a parameter value
        Format: F0 04 17 23 [Parameter ID], [value MSB], [value LSB], 00 00 00 00 00 00 00 00 [Unit ID] F7
        """
        # Split value into MSB/LSB
        value_msb = value // 128 if value >= 128 else 0
        value_lsb = value % 128
        
        data = [
            self.SYSEX_START,
            *self.MANUFACTURER_ID,
            self.SET_PARAM_CMD,
            parameter_id,
            value_msb,
            value_lsb,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            self.unit_id,
            self.SYSEX_END
        ]
        
        return mido.Message('sysex', data=data[1:-1])  # mido handles F0/F7
        
    def parse_parameter_response(self, msg: mido.Message) -> Optional[Tuple[int, int]]:
        """
        Parse parameter response from Matriarch
        Returns (parameter_id, value) if valid, None if invalid
        """
        if msg.type != 'sysex':
            return None
            
        data = [0xF0] + list(msg.data) + [0xF7]  # Reconstruct full message
        
        # Validate message structure
        if len(data) < 16:
            logger.warning(f"SysEx message too short: {len(data)} bytes")
            logger.debug(f"Raw data: {' '.join(f'{b:02X}' for b in data)}")
            return None
            
        if data[0] != self.SYSEX_START or data[-1] != self.SYSEX_END:
            logger.warning("Invalid SysEx start/end bytes")
            return None
            
        if data[1:3] != self.MANUFACTURER_ID:
            logger.warning("Invalid manufacturer ID")
            logger.debug(f"Expected: {self.MANUFACTURER_ID}, Got: {data[1:3]}")
            return None
            
        if data[3] != self.SET_PARAM_CMD:
            logger.warning(f"Unexpected command: {data[3]:02X} (expected {self.SET_PARAM_CMD:02X})")
            return None
            
        # Extract parameter ID and value
        parameter_id = data[4]
        value_msb = data[5]
        value_lsb = data[6]
        value = (value_msb * 128) + value_lsb
        
        # Check if this is a response (byte 14 should be 1 for responses)
        is_response = len(data) >= 16 and data[14] == 1
        
        # Check unit ID - it's at different positions for query vs response
        unit_id_byte = data[-2] if len(data) >= 16 else 0
        
        logger.debug(f"SysEx parse: param_id={parameter_id}, value={value}, is_response={is_response}, unit_id={unit_id_byte}")
        
        if is_response:
            logger.debug(f"Received response: param {parameter_id} = {value}")
        else:
            logger.debug(f"Received set command: param {parameter_id} = {value}")
            
        return (parameter_id, value)
    
    def is_matriarch_sysex(self, msg: mido.Message) -> bool:
        """Check if message is a Matriarch SysEx message"""
        if msg.type != 'sysex':
            return False
            
        data = list(msg.data)
        if len(data) < 3:
            return False
            
        return data[0:2] == self.MANUFACTURER_ID and len(data) >= 14
    
    def create_bulk_query(self, parameter_ids: List[int]) -> List[mido.Message]:
        """Create multiple query messages for bulk parameter retrieval"""
        return [self.create_parameter_query(pid) for pid in parameter_ids]
    
    def format_sysex_hex(self, msg: mido.Message) -> str:
        """Format SysEx message as hex string for logging"""
        if msg.type != 'sysex':
            return str(msg)
            
        hex_data = ' '.join(f'{b:02X}' for b in ([0xF0] + list(msg.data) + [0xF7]))
        return f"SysEx: {hex_data}"
    
    def validate_parameter_value(self, parameter_id: int, value: int) -> bool:
        """Basic validation of parameter values"""
        # Most parameters are in range 0-16383 (14-bit)
        if value < 0 or value > 16383:
            return False
            
        # Add specific parameter validation as needed
        # This can be expanded based on parameter_definitions.py
        return True

class SysExError(Exception):
    """Custom exception for SysEx-related errors"""
    pass

class SysExTimeoutError(SysExError):
    """Raised when SysEx query times out"""
    pass

class SysExValidationError(SysExError):
    """Raised when SysEx message validation fails"""
    pass

# Utility functions for working with SysEx data

def bytes_to_hex_string(data: bytes) -> str:
    """Convert bytes to readable hex string"""
    return ' '.join(f'{b:02X}' for b in data)

def calculate_checksum(data: List[int]) -> int:
    """Calculate simple checksum for SysEx validation (if needed)"""
    return sum(data) & 0x7F

def split_14bit_value(value: int) -> Tuple[int, int]:
    """Split 14-bit value into 7-bit MSB and LSB"""
    msb = (value >> 7) & 0x7F
    lsb = value & 0x7F
    return msb, lsb

def combine_7bit_values(msb: int, lsb: int) -> int:
    """Combine 7-bit MSB and LSB into 14-bit value"""
    return ((msb & 0x7F) << 7) | (lsb & 0x7F)

def validate_7bit_data(data: List[int]) -> bool:
    """Validate that all bytes are valid 7-bit MIDI data"""
    return all(0 <= b <= 127 for b in data)