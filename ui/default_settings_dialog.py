"""
Default Settings Dialog - Display all parameter defaults
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QHeaderView, QAbstractItemView
)
from PyQt5.QtCore import Qt
from data.parameter_definitions import PARAMETERS, Parameter


class DefaultSettingsDialog(QDialog):
    """Dialog showing default values for all parameters"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Default Parameter Settings")
        self.setMinimumSize(900, 600)
        self.init_ui()
    
    def init_ui(self):
        """Initialize the dialog UI"""
        layout = QVBoxLayout(self)
        
        # Create table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels([
            "Parameter ID", "Parameter Name", "Default Value", "Values"
        ])
        
        # Configure table
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setAlternatingRowColors(True)
        
        # Populate table
        self.populate_table()
        
        # Resize columns
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        
        layout.addWidget(self.table)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
        
        # Apply styling
        self.apply_styling()
    
    def populate_table(self):
        """Populate table with parameter data"""
        # Sort parameters by ID
        sorted_params = sorted(PARAMETERS.items(), key=lambda x: x[0])
        
        self.table.setRowCount(len(sorted_params))
        
        for row, (param_id, param) in enumerate(sorted_params):
            # Parameter ID
            id_item = QTableWidgetItem(str(param_id))
            id_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 0, id_item)
            
            # Parameter Name
            name_item = QTableWidgetItem(param.name)
            self.table.setItem(row, 1, name_item)
            
            # Default Value
            default_item = QTableWidgetItem(str(param.default_value))
            default_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 2, default_item)
            
            # Values (possible values)
            values_text = self.format_values(param)
            values_item = QTableWidgetItem(values_text)
            self.table.setItem(row, 3, values_item)
    
    def format_values(self, param: Parameter) -> str:
        """Format the possible values for display"""
        # If parameter has choices (discrete values)
        if param.choices:
            choices_list = [f"{val} = {text}" for val, text in sorted(param.choices.items())]
            return ", ".join(choices_list)
        
        # If parameter has CC mapping with specific ranges
        if param.cc:
            cc_num = param.cc.get('number')
            
            # Special cases based on CC number or parameter characteristics
            # Check for binary CC (0-63 = OFF, 64-127 = ON)
            if param.max_value == 1 and param.min_value == 0:
                return "0 = Off, 1 = On"
            
            # Check for octave parameters (based on name pattern)
            if 'octave' in param.name.lower() and 'osc' in param.name.lower():
                return "0-31 = 16', 32-63 = 8', 64-95 = 4', 96-127 = 2'"
            
            # Check for voice mode parameters
            if 'paraphony mode' in param.name.lower():
                return "0 = Mono, 1 = Duo, 2 = Quad"
            
            # Check for frequency range parameters
            if 'frequency' in param.name.lower() and 'knob range' in param.name.lower():
                return "0-24 Semitones"
        
        # Default: show min-max range
        if param.min_value == 0 and param.max_value == 1:
            return "0 = Off, 1 = On"
        elif param.min_value == 0 and param.max_value == 16383:
            return "0-16383 (14-bit)"
        elif param.min_value == 0 and param.max_value == 127:
            return "0-127"
        else:
            return f"{param.min_value}-{param.max_value}"
    
    def apply_styling(self):
        """Apply dark theme styling"""
        self.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QTableWidget {
                background-color: #3c3c3c;
                color: #ffffff;
                gridline-color: #555555;
                border: 1px solid #666666;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QTableWidget::item:alternate {
                background-color: #333333;
            }
            QTableWidget::item:selected {
                background-color: #ff6b35;
            }
            QHeaderView::section {
                background-color: #4a4a4a;
                color: #ffffff;
                padding: 5px;
                border: 1px solid #666666;
                font-weight: bold;
            }
            QPushButton {
                background-color: #4a4a4a;
                color: #ffffff;
                border: 1px solid #666666;
                padding: 8px 20px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #5a5a5a;
            }
            QPushButton:pressed {
                background-color: #ff6b35;
            }
        """)