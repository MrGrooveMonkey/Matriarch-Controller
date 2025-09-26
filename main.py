#!/usr/bin/env python3
"""
Matriarch Controller - Main Application Entry Point
"""

import sys
import os
import logging
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon

# Add the project directory to Python path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_dir)

# Set up logging
log_level = logging.DEBUG if '--debug' in sys.argv else logging.INFO
logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('matriarch_controller.log')
    ]
)

logger = logging.getLogger(__name__)

def check_dependencies():
    """Check if required libraries are installed"""
    missing_deps = []
    
    try:
        import mido
    except ImportError:
        missing_deps.append('mido')
    
    try:
        import rtmidi
    except ImportError:
        missing_deps.append('python-rtmidi')
    
    try:
        from PyQt5 import QtWidgets, QtCore, QtGui
    except ImportError:
        missing_deps.append('PyQt5')
    
    if missing_deps:
        error_msg = "Missing required dependencies:\n\n"
        error_msg += "\n".join(f"  - {dep}" for dep in missing_deps)
        error_msg += "\n\nPlease install them using:\n"
        error_msg += f"pip3 install {' '.join(missing_deps)}"
        
        print(error_msg)
        
        # Show GUI error if PyQt5 is available
        if 'PyQt5' not in missing_deps:
            app = QApplication(sys.argv)
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Missing Dependencies")
            msg.setText("Required Python libraries are missing.")
            msg.setDetailedText(error_msg)
            msg.exec_()
        
        return False
    
    return True

def check_midi_system():
    """Check if MIDI system is working"""
    try:
        import mido
        # Try to get available ports
        input_ports = mido.get_input_names()
        output_ports = mido.get_output_names()
        
        if not input_ports and not output_ports:
            logger.warning("No MIDI ports detected. Check your MIDI setup.")
            return True  # Don't block app startup, just warn
        
        logger.info(f"MIDI system OK: {len(input_ports)} inputs, {len(output_ports)} outputs")
        return True
        
    except Exception as e:
        logger.error(f"MIDI system error: {e}")
        return False

def main():
    """Main application entry point"""
    logger.info("Starting Matriarch Controller...")
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Check MIDI system
    if not check_midi_system():
        logger.error("MIDI system check failed")
        sys.exit(1)
    
    # Create QApplication
    app = QApplication(sys.argv)
    app.setApplicationName("Matriarch Controller")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("Matriarch Controller")
    
    # Set application properties
    app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    try:
        # Import and create main window
        if '--test' in sys.argv:
            # Run test mode
            from test_midi_connection import MatriarchTester
            print("Running in test mode...")
            tester = MatriarchTester()
            result = tester.run_test()
            return 0 if result else 1
        else:
            # Create and show main window
            from ui.main_window import MatriarchMainWindow
            
            main_window = MatriarchMainWindow()
            main_window.show()
            
            logger.info("Main window created and shown")
            return app.exec_()
        
    except ImportError as e:
        logger.error(f"Import error: {e}")
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowTitle("Import Error")
        msg.setText(f"Failed to import required modules: {e}")
        msg.setDetailedText(str(e))
        msg.exec_()
        return 1
    
    except Exception as e:
        logger.exception("Unexpected error in main application")
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowTitle("Application Error")
        msg.setText(f"Unexpected error: {e}")
        msg.setDetailedText(str(e))
        msg.exec_()
        return 1

if __name__ == "__main__":
    # Handle command line arguments
    if '--help' in sys.argv or '-h' in sys.argv:
        print("Matriarch Controller")
        print("Usage: python3 main.py [options]")
        print("\nOptions:")
        print("  --help, -h     Show this help message")
        print("  --test         Run MIDI connection test")
        print("  --debug        Enable debug logging")
        print("\nFor MIDI testing:")
        print("  python3 test_midi_connection.py")
        sys.exit(0)
    
    sys.exit(main())