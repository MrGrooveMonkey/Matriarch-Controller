#!/usr/bin/env python3
"""
Test script for Matriarch MIDI communication
Run this to verify MIDI connection and parameter queries work
"""

import sys
import time
import logging
from typing import Dict, Any

# Add project root to path for imports
sys.path.append('.')

from midi.connection import MIDIConnectionManager
from data.parameter_definitions import PARAMETERS, get_parameter_by_id

# Set up logging based on command line args
log_level = logging.DEBUG if '--debug' in sys.argv else logging.INFO
logging.basicConfig(level=log_level, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MatriarchTester:
    """Simple test class for Matriarch MIDI communication"""
    
    def __init__(self):
        self.midi_manager = MIDIConnectionManager()
        self.received_parameters = {}
        self.midi_log = []
        
        # Set up callbacks
        self.midi_manager.set_callbacks(
            parameter_callback=self.on_parameter_received,
            error_callback=self.on_error,
            midi_log_callback=self.on_midi_log
        )
    
    def on_parameter_received(self, param_id: int, value: int):
        """Handle received parameter updates"""
        self.received_parameters[param_id] = value
        param = get_parameter_by_id(param_id)
        if param:
            human_readable = param.get_human_readable(value)
            print(f"  Received: {param.name} = {value} ({human_readable})")
        else:
            print(f"  Received: Parameter {param_id} = {value}")
    
    def on_error(self, error_message: str):
        """Handle MIDI errors"""
        print(f"ERROR: {error_message}")
    
    def on_midi_log(self, message: str, is_incoming: bool):
        """Log MIDI messages"""
        self.midi_log.append((time.time(), message, is_incoming))
        if len(self.midi_log) > 100:  # Keep only last 100 messages
            self.midi_log = self.midi_log[-100:]
    
    def scan_ports(self):
        """Scan and display available MIDI ports"""
        print("Scanning MIDI ports...")
        ports = self.midi_manager.get_available_ports()
        
        print(f"\nAvailable MIDI Input Ports ({len(ports['inputs'])}):")
        for i, port in enumerate(ports['inputs']):
            print(f"  {i+1}. {port}")
        
        print(f"\nAvailable MIDI Output Ports ({len(ports['outputs'])}):")
        for i, port in enumerate(ports['outputs']):
            print(f"  {i+1}. {port}")
        
        return ports
    
    def select_ports(self, ports: Dict[str, list]) -> tuple:
        """Interactive port selection"""
        if not ports['inputs'] or not ports['outputs']:
            print("ERROR: No MIDI ports available. Check your MIDI setup.")
            return None, None
        
        # Select input port
        while True:
            try:
                choice = input(f"\nSelect MIDI Input Port (1-{len(ports['inputs'])}): ")
                idx = int(choice) - 1
                if 0 <= idx < len(ports['inputs']):
                    input_port = ports['inputs'][idx]
                    break
                else:
                    print("Invalid selection. Please try again.")
            except ValueError:
                print("Please enter a number.")
        
        # Select output port
        while True:
            try:
                choice = input(f"Select MIDI Output Port (1-{len(ports['outputs'])}): ")
                idx = int(choice) - 1
                if 0 <= idx < len(ports['outputs']):
                    output_port = ports['outputs'][idx]
                    break
                else:
                    print("Invalid selection. Please try again.")
            except ValueError:
                print("Please enter a number.")
        
        return input_port, output_port
    
    def test_connection(self, input_port: str, output_port: str) -> bool:
        """Test MIDI connection"""
        print(f"\nConnecting to MIDI ports...")
        print(f"  Input:  {input_port}")
        print(f"  Output: {output_port}")
        
        if not self.midi_manager.connect(input_port, output_port):
            print("Failed to connect to MIDI ports!")
            return False
        
        print("Connected successfully!")
        
        # Test basic communication
        print("\nTesting communication with Matriarch...")
        if self.midi_manager.test_connection():
            print("Communication test PASSED!")
            return True
        else:
            print("Communication test FAILED!")
            print("Make sure:")
            print("  - Matriarch is powered on")
            print("  - MIDI cables are properly connected")
            print("  - Matriarch MIDI settings are correct")
            return False
    
    def query_sample_parameters(self):
        """Query a few sample parameters"""
        print("\nQuerying sample parameters...")
        
        # Test with a few key parameters
        test_params = [0, 3, 10, 37, 55]  # Unit ID, Note Priority, MIDI Channel, Pitch Bend Range, Paraphony Mode
        
        for param_id in test_params:
            param = get_parameter_by_id(param_id)
            if param:
                print(f"\nQuerying: {param.name}")
                value = self.midi_manager.query_parameter_sync(param_id)
                if value is not None:
                    human_readable = param.get_human_readable(value)
                    print(f"  Result: {value} ({human_readable})")
                else:
                    print(f"  Result: FAILED (timeout or error)")
            time.sleep(0.5)  # Small delay between queries
    
    def test_parameter_set(self):
        """Test setting a parameter (non-destructive test)"""
        print("\nTesting parameter setting (Unit ID)...")
        
        # Query current Unit ID
        current_value = self.midi_manager.query_parameter_sync(0)
        if current_value is None:
            print("Cannot test parameter setting - query failed")
            return
        
        print(f"Current Unit ID: {current_value}")
        
        # Set to same value (non-destructive test)
        print("Setting Unit ID to same value...")
        if self.midi_manager.set_parameter(0, current_value):
            print("Parameter set command sent successfully")
            
            # Verify by re-querying
            time.sleep(0.5)
            new_value = self.midi_manager.query_parameter_sync(0)
            if new_value == current_value:
                print("Parameter setting test PASSED!")
            else:
                print(f"Parameter setting test FAILED! Got {new_value}, expected {current_value}")
        else:
            print("Failed to send parameter set command")
    
    def show_midi_log(self):
        """Display recent MIDI log"""
        if not self.midi_log:
            print("\nNo MIDI messages logged.")
            return
        
        print(f"\nRecent MIDI Messages ({len(self.midi_log)}):")
        for timestamp, message, is_incoming in self.midi_log[-10:]:  # Show last 10
            direction = "IN " if is_incoming else "OUT"
            print(f"  {direction}: {message}")
    
    def run_test(self):
        """Run complete test suite"""
        print("=" * 60)
        print("Matriarch MIDI Connection Test")
        print("=" * 60)
        
        try:
            # Scan ports
            ports = self.scan_ports()
            if not ports['inputs'] or not ports['outputs']:
                return False
            
            # Select ports
            input_port, output_port = self.select_ports(ports)
            if not input_port or not output_port:
                return False
            
            # Test connection
            if not self.test_connection(input_port, output_port):
                return False
            
            # Query sample parameters
            self.query_sample_parameters()
            
            # Test parameter setting
            self.test_parameter_set()
            
            # Show MIDI log
            self.show_midi_log()
            
            print("\n" + "=" * 60)
            print("Test completed successfully!")
            print("You can now proceed with building the full application.")
            print("=" * 60)
            
            return True
            
        except KeyboardInterrupt:
            print("\nTest interrupted by user.")
            return False
        except Exception as e:
            print(f"\nTest failed with error: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            # Clean up
            if self.midi_manager.is_connected:
                self.midi_manager.disconnect()

def main():
    """Main test function"""
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print("Usage: python3 test_midi_connection.py")
        print("\nThis script tests MIDI communication with the Moog Matriarch.")
        print("Make sure your Matriarch is:")
        print("  - Powered on")
        print("  - Connected via MIDI (USB or DIN)")
        print("  - Set to receive on MIDI Channel 1 (default)")
        return
    
    tester = MatriarchTester()
    success = tester.run_test()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()