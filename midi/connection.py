"""
MIDI Connection Management for Matriarch Controller
"""

import mido
import time
import threading
import logging
from typing import Optional, List, Dict, Callable, Any
from queue import Queue, Empty
from .sysex import MatriarchSysEx, SysExTimeoutError, SysExValidationError

logger = logging.getLogger(__name__)

class MIDIConnectionManager:
    """Manages MIDI connections and communication with Matriarch"""
    
    def __init__(self, unit_id: int = 0, midi_channel: int = 0):
        self.unit_id = unit_id
        self.midi_channel = midi_channel  # 0-15 for MIDI channels 1-16
        
        self.input_port: Optional[mido.ports.BaseInput] = None
        self.output_port: Optional[mido.ports.BaseOutput] = None
        self.input_port_name: Optional[str] = None
        self.output_port_name: Optional[str] = None
        
        self.sysex_handler = MatriarchSysEx(unit_id)
        self.is_connected = False
        self.is_listening = False
        
        # Response handling
        self.response_queue = Queue()
        self.pending_queries = {}  # param_id -> timestamp
        self.query_timeout = 3.0  # seconds
        self.query_delay = 0.4  # seconds between queries
        
        # Threading
        self.listen_thread: Optional[threading.Thread] = None
        self.stop_listening = threading.Event()
        
        # Callbacks
        self.parameter_callback: Optional[Callable[[int, int], None]] = None
        self.error_callback: Optional[Callable[[str], None]] = None
        self.midi_log_callback: Optional[Callable[[str, bool], None]] = None  # message, is_incoming
        
    def get_available_ports(self) -> Dict[str, List[str]]:
        """Get lists of available MIDI input and output ports"""
        try:
            input_ports = mido.get_input_names()
            output_ports = mido.get_output_names()
            return {
                'inputs': input_ports,
                'outputs': output_ports
            }
        except Exception as e:
            logger.error(f"Error scanning MIDI ports: {e}")
            return {'inputs': [], 'outputs': []}
    
    def connect(self, input_port_name: str, output_port_name: str) -> bool:
        """Connect to specified MIDI ports"""
        try:
            # Disconnect if already connected
            if self.is_connected:
                self.disconnect()
            
            # Open input port
            self.input_port = mido.open_input(input_port_name)
            self.input_port_name = input_port_name
            
            # Open output port
            self.output_port = mido.open_output(output_port_name)
            self.output_port_name = output_port_name
            
            self.is_connected = True
            self.start_listening()
            
            logger.info(f"Connected to MIDI ports: {input_port_name} -> {output_port_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to MIDI ports: {e}")
            if self.error_callback:
                self.error_callback(f"MIDI Connection Error: {e}")
            self.cleanup_connection()
            return False
    
    def disconnect(self):
        """Disconnect from MIDI ports"""
        self.stop_listening_thread()
        self.cleanup_connection()
        logger.info("Disconnected from MIDI ports")
    
    def cleanup_connection(self):
        """Clean up MIDI connection resources"""
        self.is_connected = False
        
        if self.input_port:
            try:
                self.input_port.close()
            except:
                pass
            self.input_port = None
            
        if self.output_port:
            try:
                self.output_port.close()
            except:
                pass
            self.output_port = None
            
        self.input_port_name = None
        self.output_port_name = None
    
    def start_listening(self):
        """Start MIDI input listening thread"""
        if self.is_listening:
            return
            
        self.stop_listening.clear()
        self.listen_thread = threading.Thread(target=self._listen_worker, daemon=True)
        self.listen_thread.start()
        self.is_listening = True
    
    def stop_listening_thread(self):
        """Stop MIDI input listening thread"""
        if not self.is_listening:
            return
            
        self.stop_listening.set()
        if self.listen_thread and self.listen_thread.is_alive():
            self.listen_thread.join(timeout=2.0)
        self.is_listening = False
    
    def _listen_worker(self):
        """Worker thread for processing incoming MIDI messages"""
        logger.debug("MIDI listen thread started")
        
        while not self.stop_listening.is_set() and self.input_port:
            try:
                # Check for messages with timeout
                msg = self.input_port.receive(block=False)
                if msg:
                    self._process_incoming_message(msg)
                else:
                    time.sleep(0.001)  # Small delay to prevent busy waiting
                    
            except Exception as e:
                logger.error(f"Error in MIDI listen thread: {e}")
                time.sleep(0.1)
                
        logger.debug("MIDI listen thread stopped")
    
    def _process_incoming_message(self, msg: mido.Message):
        """Process incoming MIDI message"""
        try:
            # Log incoming message
            if self.midi_log_callback:
                if msg.type == 'sysex':
                    log_msg = f"IN:  {self.sysex_handler.format_sysex_hex(msg)}"
                else:
                    log_msg = f"IN:  {msg}"
                self.midi_log_callback(log_msg, True)
            
            # Handle SysEx messages
            if msg.type == 'sysex' and self.sysex_handler.is_matriarch_sysex(msg):
                result = self.sysex_handler.parse_parameter_response(msg)
                if result:
                    param_id, value = result
                    
                    # Remove from pending queries
                    if param_id in self.pending_queries:
                        del self.pending_queries[param_id]
                    
                    # Notify callback
                    if self.parameter_callback:
                        self.parameter_callback(param_id, value)
                    
                    logger.debug(f"Parameter update: {param_id} = {value}")
            
            # Handle other MIDI messages (CC, etc.) here if needed
            elif msg.type == 'control_change':
                # Handle CC messages if we implement CC parameter control
                pass
                
        except Exception as e:
            logger.error(f"Error processing incoming MIDI message: {e}")
    
    def send_message(self, msg: mido.Message) -> bool:
        """Send MIDI message to output port"""
        if not self.is_connected or not self.output_port:
            logger.warning("Cannot send message: not connected")
            return False
            
        try:
            self.output_port.send(msg)
            
            # Log outgoing message
            if self.midi_log_callback:
                if msg.type == 'sysex':
                    log_msg = f"OUT: {self.sysex_handler.format_sysex_hex(msg)}"
                else:
                    log_msg = f"OUT: {msg}"
                self.midi_log_callback(log_msg, False)
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending MIDI message: {e}")
            if self.error_callback:
                self.error_callback(f"MIDI Send Error: {e}")
            return False
    
    def query_parameter(self, parameter_id: int, timeout: Optional[float] = None) -> Optional[int]:
        """
        Query a parameter value from Matriarch
        Returns the parameter value or None if timeout/error
        """
        if timeout is None:
            timeout = self.query_timeout
            
        # Create and send query message
        query_msg = self.sysex_handler.create_parameter_query(parameter_id)
        
        if not self.send_message(query_msg):
            return None
        
        # Record pending query
        self.pending_queries[parameter_id] = time.time()
        
        # Wait for response
        start_time = time.time()
        while time.time() - start_time < timeout:
            if parameter_id not in self.pending_queries:
                # Response received (handled in _process_incoming_message)
                # The callback would have been called, but we need the value here
                # For now, we'll use a different approach for synchronous queries
                break
            time.sleep(0.01)
        
        # Check if we got a response
        if parameter_id in self.pending_queries:
            del self.pending_queries[parameter_id]
            logger.warning(f"Parameter query timeout: {parameter_id}")
            return None
        
        # For synchronous operation, we need a different approach
        # This is a simplified version - in practice, we'd need a response cache
        return None  # Will be improved in full implementation
    
    def set_parameter(self, parameter_id: int, value: int) -> bool:
        """Set a parameter value on Matriarch"""
        if not self.sysex_handler.validate_parameter_value(parameter_id, value):
            logger.warning(f"Invalid parameter value: {parameter_id} = {value}")
            return False
        
        set_msg = self.sysex_handler.create_parameter_set(parameter_id, value)
        return self.send_message(set_msg)
    
    def send_cc(self, cc_number: int, value: int) -> bool:
        """Send Control Change message"""
        if not (0 <= cc_number <= 127) or not (0 <= value <= 127):
            logger.warning(f"Invalid CC parameters: CC{cc_number} = {value}")
            return False
        
        cc_msg = mido.Message('control_change', 
                             channel=self.midi_channel,
                             control=cc_number, 
                             value=value)
        return self.send_message(cc_msg)
    
    def query_all_parameters(self, parameter_ids: List[int], 
                           progress_callback: Optional[Callable[[int, int], None]] = None,
                           retry_count: int = 3) -> Dict[int, Optional[int]]:
        """
        Query multiple parameters with retry logic and progress reporting
        """
        results = {}
        total_params = len(parameter_ids)
        
        for i, param_id in enumerate(parameter_ids):
            success = False
            
            # Retry logic
            for attempt in range(retry_count):
                try:
                    # Add delay between queries to avoid overwhelming Matriarch
                    if i > 0:  # Skip delay for first parameter
                        time.sleep(self.query_delay)
                    
                    value = self.query_parameter_sync(param_id)
                    if value is not None:
                        results[param_id] = value
                        success = True
                        break
                    else:
                        logger.warning(f"Query attempt {attempt + 1} failed for parameter {param_id}")
                        
                except Exception as e:
                    logger.error(f"Error querying parameter {param_id}, attempt {attempt + 1}: {e}")
            
            if not success:
                results[param_id] = None
                logger.error(f"Failed to query parameter {param_id} after {retry_count} attempts")
            
            # Report progress
            if progress_callback:
                progress_callback(i + 1, total_params)
        
        return results
    
    def query_parameter_sync(self, parameter_id: int) -> Optional[int]:
        """
        Synchronous parameter query with response caching
        """
        # Create a temporary response handler
        response_received = threading.Event()
        response_value = [None]  # Use list for mutable reference
        
        def temp_callback(pid: int, value: int):
            if pid == parameter_id:
                response_value[0] = value
                response_received.set()
        
        # Temporarily set callback
        old_callback = self.parameter_callback
        self.parameter_callback = temp_callback
        
        try:
            # Send query
            query_msg = self.sysex_handler.create_parameter_query(parameter_id)
            logger.debug(f"Sending query for parameter {parameter_id}: {self.sysex_handler.format_sysex_hex(query_msg)}")
            
            if not self.send_message(query_msg):
                logger.error("Failed to send query message")
                return None
            
            # Wait for response
            if response_received.wait(timeout=self.query_timeout):
                logger.debug(f"Query successful: param {parameter_id} = {response_value[0]}")
                return response_value[0]
            else:
                logger.warning(f"Timeout querying parameter {parameter_id}")
                return None
                
        finally:
            # Restore original callback
            self.parameter_callback = old_callback
    
    def test_connection(self) -> bool:
        """Test connection by querying a simple parameter"""
        if not self.is_connected:
            return False
        
        # Try to query Unit ID (parameter 0) as a connection test
        try:
            result = self.query_parameter_sync(0)  # Unit ID parameter
            return result is not None
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
    
    def set_callbacks(self, 
                     parameter_callback: Optional[Callable[[int, int], None]] = None,
                     error_callback: Optional[Callable[[str], None]] = None,
                     midi_log_callback: Optional[Callable[[str, bool], None]] = None):
        """Set callback functions for various events"""
        if parameter_callback:
            self.parameter_callback = parameter_callback
        if error_callback:
            self.error_callback = error_callback
        if midi_log_callback:
            self.midi_log_callback = midi_log_callback
    
    def update_settings(self, unit_id: Optional[int] = None, midi_channel: Optional[int] = None):
        """Update MIDI settings"""
        if unit_id is not None:
            self.unit_id = unit_id
            self.sysex_handler.unit_id = unit_id
            
        if midi_channel is not None:
            self.midi_channel = midi_channel
    
    def get_connection_info(self) -> Dict[str, Any]:
        """Get current connection information"""
        return {
            'connected': self.is_connected,
            'input_port': self.input_port_name,
            'output_port': self.output_port_name,
            'unit_id': self.unit_id,
            'midi_channel': self.midi_channel + 1,  # Display as 1-16
            'listening': self.is_listening
        }