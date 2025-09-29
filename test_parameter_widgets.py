"""
Parameter Widget Tester
Tests all parameter widgets and logs their behavior
"""

import sys
import logging
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QTextEdit
from PyQt5.QtCore import QTimer
from data.parameter_definitions import PARAMETERS, get_parameter_by_id
from ui.parameter_widgets import ParameterWidgetFactory, ParameterType

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ParameterTester(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Parameter Widget Tester")
        self.setGeometry(100, 100, 800, 600)
        
        self.test_results = []
        self.current_param_index = 0
        self.param_ids = sorted(PARAMETERS.keys())
        
        self.init_ui()
        
    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Start test button
        self.start_button = QPushButton("Start Automated Test")
        self.start_button.clicked.connect(self.start_test)
        layout.addWidget(self.start_button)
        
        # Results display
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        layout.addWidget(self.results_text)
        
        # Test container
        self.test_container = QWidget()
        self.test_layout = QVBoxLayout(self.test_container)
        layout.addWidget(self.test_container)
        
    def start_test(self):
        self.test_results = []
        self.current_param_index = 0
        self.results_text.clear()
        self.start_button.setEnabled(False)
        
        self.log_message("=" * 60)
        self.log_message("STARTING PARAMETER WIDGET TEST")
        self.log_message(f"Testing {len(self.param_ids)} parameters")
        self.log_message("=" * 60)
        
        # Start testing
        QTimer.singleShot(100, self.test_next_parameter)
        
    def test_next_parameter(self):
        if self.current_param_index >= len(self.param_ids):
            self.finish_test()
            return
            
        param_id = self.param_ids[self.current_param_index]
        param = get_parameter_by_id(param_id)
        
        if not param:
            self.log_message(f"ERROR: Parameter {param_id} not found")
            self.current_param_index += 1
            QTimer.singleShot(10, self.test_next_parameter)
            return
        
        self.log_message(f"\nTesting Parameter {param_id}: {param.name}")
        self.log_message(f"  Type: {param.param_type.value}")
        self.log_message(f"  Category: {param.category.value}")
        self.log_message(f"  Default: {param.default_value}")
        
        # Clear previous widget
        for i in reversed(range(self.test_layout.count())): 
            self.test_layout.itemAt(i).widget().setParent(None)
        
        # Create widget
        try:
            factory = ParameterWidgetFactory()
            widget = factory.create_widget(param)
            widget.value_changed.connect(lambda pid, val: self.on_value_changed(pid, val))
            self.test_layout.addWidget(widget)
            
            self.log_message(f"  Widget created: {widget.__class__.__name__}")
            
            # Test the widget
            self.test_widget(widget, param)
            
        except Exception as e:
            self.log_message(f"  ERROR creating widget: {str(e)}")
            logger.exception(f"Error creating widget for param {param_id}")
        
        # Move to next
        self.current_param_index += 1
        QTimer.singleShot(500, self.test_next_parameter)
        
    def test_widget(self, widget, param):
        """Test widget functionality"""
        try:
            # Test 1: Set to default value
            widget.set_value_silently(param.default_value)
            self.log_message(f"  ✓ Set to default value: {param.default_value}")
            
            # Test 2: Set to different values based on type
            test_values = self.get_test_values(param)
            for test_val in test_values:
                try:
                    widget.set_value_silently(test_val)
                    self.log_message(f"  ✓ Set to test value: {test_val}")
                except Exception as e:
                    self.log_message(f"  ✗ Failed to set value {test_val}: {str(e)}")
            
            # Test 3: Check if value_changed signal works
            self.value_change_detected = False
            if test_values:
                # Programmatically trigger a change
                if hasattr(widget, 'emit_value_changed'):
                    widget.emit_value_changed(test_values[0])
                    if self.value_change_detected:
                        self.log_message(f"  ✓ value_changed signal works")
                    else:
                        self.log_message(f"  ✗ value_changed signal not detected")
            
        except Exception as e:
            self.log_message(f"  ✗ Test failed: {str(e)}")
            logger.exception(f"Error testing widget for param {param.param_id}")
    
    def get_test_values(self, param):
        """Get appropriate test values for parameter type"""
        if param.param_type == ParameterType.TOGGLE:
            return [0, 1]
        elif param.param_type == ParameterType.CHOICE:
            return list(param.choices.keys())[:3]  # Test first 3 choices
        elif param.param_type == ParameterType.RANGE:
            min_val = param.min_value or 0
            max_val = param.max_value or 127
            mid_val = (min_val + max_val) // 2
            return [min_val, mid_val, max_val]
        elif param.param_type == ParameterType.MIDI_CHANNEL:
            return [0, 7, 15]
        else:
            return [0, 64, 127]
    
    def on_value_changed(self, param_id, value):
        """Callback for value changes"""
        self.value_change_detected = True
        self.log_message(f"  → Value changed: {param_id} = {value}")
    
    def log_message(self, message):
        """Add message to results display"""
        self.results_text.append(message)
        logger.info(message)
    
    def finish_test(self):
        self.log_message("\n" + "=" * 60)
        self.log_message("TEST COMPLETED")
        self.log_message("=" * 60)
        self.start_button.setEnabled(True)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    tester = ParameterTester()
    tester.show()
    sys.exit(app.exec_())