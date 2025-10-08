"""
Performance Tab - Custom layout matching Matriarch hardware
"""

import logging
from typing import Dict, Optional
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, 
    QGroupBox, QLabel, QSlider, QPushButton, QComboBox, QDial, 
    QMainWindow
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont

from data.parameter_definitions import get_parameter_by_id, Parameter
from ui.parameter_widgets import ParameterWidget, ButtonGroupParameterWidget

logger = logging.getLogger(__name__)

class PerformanceTabWidget(QWidget):
    """Custom performance tab with hardware-inspired layout"""
    
    parameter_changed = pyqtSignal(int, int)  # param_id, value
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parameter_widgets: Dict[int, ParameterWidget] = {}
        self.current_bank = 1  # Track current bank (1-3)
        self.current_sequence = 1  # Track current sequence (1-4)
        self.current_mode = 1  # Track current mode: 0=ARP, 1=SEQ, 2=REC (default SEQ)
        self.seq_buttons = []  # Will be initialized in create_arp_seq_section
        self.init_ui()
    
    def init_ui(self):
        """Initialize the performance tab layout"""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)
    
        # ======================
        # TOP ROW SLIDERS
        # ======================
        top_row_widget = QWidget()
        top_row_layout = QHBoxLayout(top_row_widget)
        top_row_layout.setSpacing(20)
        top_row_layout.setContentsMargins(0, 0, 0, 0)
    
        # Left side - Arp controls
        left_group = QWidget()
        left_layout = QVBoxLayout(left_group)
        left_layout.setSpacing(5)
    
        # Arp Gate Length (parameter 15)
        arp_gate_layout = QHBoxLayout()
        arp_gate_label = QLabel("Arp Gate Length")
        arp_gate_label.setStyleSheet("color: white; font-weight: bold; min-width: 120px;")
        arp_gate_layout.addWidget(arp_gate_label)

        arp_gate_param = get_parameter_by_id(115)
        if arp_gate_param:
            # Convert to percentage display (0-16383 → 0-100%)
            def gate_to_percent(v):
                return f"{int(v/163.83)}%"
    
            arp_gate_widget = ParameterSliderWidget(arp_gate_param, convert_display=gate_to_percent)
            arp_gate_widget.value_changed.connect(self.on_widget_value_changed)
            self.parameter_widgets[115] = arp_gate_widget
            arp_gate_layout.addWidget(arp_gate_widget, 1)
    
        # Arp/Seq Swing (parameter 23)
        swing_layout = QHBoxLayout()
        swing_label = QLabel("Arp/Seq Swing")
        swing_label.setStyleSheet("color: white; font-weight: bold; min-width: 120px;")
        swing_layout.addWidget(swing_label)

        swing_param = get_parameter_by_id(23)
        if swing_param:
            # Use parameter's built-in human_readable_func if available
            convert_func = swing_param.human_readable_func if hasattr(swing_param, 'human_readable_func') else None
            swing_widget = ParameterSliderWidget(swing_param, convert_display=convert_func)
            swing_widget.value_changed.connect(self.on_widget_value_changed)
            self.parameter_widgets[23] = swing_widget
            swing_layout.addWidget(swing_widget, 1)
    
        left_layout.addLayout(arp_gate_layout)
        left_layout.addLayout(swing_layout)
    
        # Center - Triplet button
        triplet_button = QPushButton("Triplet (66%)")
        triplet_button.setCheckable(True)
        triplet_button.setFixedSize(120, 60)
        triplet_button.setStyleSheet("""
            QPushButton {
                background-color: #4a4a4a;
                border: 2px solid #666666;
                color: white;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:checked {
                background-color: #228B22;
                border: 2px solid #1a6b1a;
            }
            QPushButton:hover {
                background-color: #5a5a5a;
            }
            QPushButton:checked:hover {
                background-color: #2a9d2a;
            }
        """)
    
        def on_triplet_clicked(checked):
            if checked:
                triplet_value = int((44.0 / 56.0) * 16383)
        
                # Update slider
                if 23 in self.parameter_widgets:
                    widget = self.parameter_widgets[23]
                    if hasattr(widget, 'slider'):
                        widget.slider.blockSignals(True)
                        widget.slider.setValue(triplet_value)
                        widget.current_value = triplet_value
                        widget.update_display()
                        widget.slider.blockSignals(False)
        
                # Send 3 times with delays to ensure Matriarch receives it
                self.parameter_changed.emit(23, triplet_value)
                QTimer.singleShot(20, lambda: self.parameter_changed.emit(23, triplet_value))
                QTimer.singleShot(40, lambda: self.parameter_changed.emit(23, triplet_value))
            else:
                center_value = int((28.0 / 56.0) * 16383)
        
                if 23 in self.parameter_widgets:
                    widget = self.parameter_widgets[23]
                    if hasattr(widget, 'slider'):
                        widget.slider.blockSignals(True)
                        widget.slider.setValue(center_value)
                        widget.current_value = center_value
                        widget.update_display()
                        widget.slider.blockSignals(False)
        
                # Send 3 times
                self.parameter_changed.emit(23, center_value)
                QTimer.singleShot(20, lambda: self.parameter_changed.emit(23, center_value))
                QTimer.singleShot(40, lambda: self.parameter_changed.emit(23, center_value))
        
        triplet_button.clicked.connect(on_triplet_clicked)
        self.triplet_button = triplet_button
    
        # Assemble top row - just left group and triplet button
        top_row_layout.addWidget(left_group, 1)
        top_row_layout.addWidget(triplet_button)
        top_row_layout.addStretch(1)  # Add stretch to balance layout
    
        main_layout.addWidget(top_row_widget)
    
        # ======================
        # MAIN SECTIONS ROW
        # ======================
        sections_widget = QWidget()
        sections_layout = QHBoxLayout(sections_widget)
        sections_layout.setSpacing(10)
        sections_layout.setContentsMargins(0, 0, 0, 0)
    
        # ARP/SEQ section
        arp_seq_section = self.create_arp_seq_section()
        sections_layout.addWidget(arp_seq_section)
    
        # OSCILLATORS section
        osc_group = self.create_oscillators_section()
        sections_layout.addWidget(osc_group, 2)  # Give more width
    
        # STEREO DELAY section
        delay_group = self.create_stereo_delay_section()
        sections_layout.addWidget(delay_group)
    
        # OUTPUT section
        output_group = self.create_output_section()
        sections_layout.addWidget(output_group)
    
        main_layout.addWidget(sections_widget, 1)
    
        # Bottom row controls
        bottom_row = self.create_bottom_controls()
        main_layout.addWidget(bottom_row)
    
    def create_arp_seq_section(self) -> QGroupBox:
        """Create the ARP/SEQ section (yellow box)"""
        group = QGroupBox("ARP/SEQ")
        group.setStyleSheet("""
            QGroupBox {
                background-color: #E8ED9E;
                border: 2px solid #666;
                border-radius: 5px;
                margin-top: 0px;
                font-weight: bold;
                font-size: 14pt;
                padding: 15px;
                padding-top: 30px;
            }
            QGroupBox::title {
                subcontrol-origin: padding;
                subcontrol-position: top center;
                padding: 5px 10px;
                color: black;
            }
        """)
        
        layout = QGridLayout(group)
        layout.setSpacing(8)
        layout.setContentsMargins(10, 20, 10, 10)
        
        # Row 0-1: Rate control (knob) - centered
        rate_param = get_parameter_by_id(108)
        if rate_param:
            rate_widget = ArpRateKnobWidget(rate_param)
            rate_widget.value_changed.connect(self.on_widget_value_changed)
            self.parameter_widgets[108] = rate_widget
            # Create a container to properly center the knob
            rate_container = QWidget()
            rate_container_layout = QHBoxLayout(rate_container)
            rate_container_layout.addStretch()
            rate_container_layout.addWidget(rate_widget)
            rate_container_layout.addStretch()
            layout.addWidget(rate_container, 0, 0, 2, 4)
        
        # Row 2: Mode selector (parameter 191 - Arp Mode)
        mode_label = QLabel("MODE")
        mode_label.setStyleSheet("font-weight: normal; color: #4a4a2a;")
        layout.addWidget(mode_label, 2, 0)

        mode_layout = QHBoxLayout()
        mode_layout.setSpacing(2)
        mode_buttons = []
        mode_texts = ["ARP", "SEQ", "REC"]
        for idx, text in enumerate(mode_texts):
            btn = QPushButton(text)
            btn.setCheckable(True)
            btn.setMinimumHeight(30)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #999999;
                    border: 1px solid #666666;
                    color: white;
                }
                QPushButton:checked {
                    background-color: #6B8E23;
                    border: 2px solid #556B2F;
                    font-weight: bold;
                }
            """)
            if idx == 0:  # Default to ARP
                btn.setChecked(True)
            mode_buttons.append(btn)
            mode_layout.addWidget(btn)

        # Make mutually exclusive and track mode selection
        for idx, btn in enumerate(mode_buttons):
            btn.clicked.connect(lambda checked, i=idx, buttons=mode_buttons: self.on_mode_clicked(buttons, i))

        layout.addLayout(mode_layout, 2, 1, 1, 3)
        
        # Disable MODE buttons - hardware switch only, no MIDI control
        for btn in mode_buttons:
            btn.setEnabled(False)
            btn.setToolTip("Hardware switch only - MIDI control not supported by firmware")
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #666666;
                    border: 1px solid #444444;
                    color: #999999;
                }
                QPushButton:checked {
                    background-color: #4a4a4a;
                    border: 2px solid #333333;
                    color: #888888;
                    font-weight: bold;
                }
            """)
        
        # Row 3: Pattern selector (parameter 192 - Arp Pattern)
        pattern_label = QLabel("Pattern")
        pattern_label.setStyleSheet("font-weight: normal; color: #4a4a2a;")
        layout.addWidget(pattern_label, 3, 0)

        pattern_layout = QHBoxLayout()
        pattern_layout.setSpacing(2)
        pattern_buttons = []
        pattern_texts = ["ORDER", "FW/BW", "RANDOM"]
        for idx, text in enumerate(pattern_texts):
            btn = QPushButton(text)
            btn.setCheckable(True)
            btn.setMinimumHeight(30)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #999999;
                    border: 1px solid #666666;
                    color: white;
                }
                QPushButton:checked {
                    background-color: #6B8E23;
                    border: 2px solid #556B2F;
                    font-weight: bold;
                }
            """)
            if idx == 0:  # Default to ORDER
                btn.setChecked(True)
            pattern_buttons.append(btn)
            pattern_layout.addWidget(btn)

        # Make mutually exclusive and emit parameter changes
        for idx, btn in enumerate(pattern_buttons):
            btn.clicked.connect(lambda checked, i=idx, buttons=pattern_buttons: self.on_pattern_clicked(buttons, i))

        layout.addLayout(pattern_layout, 3, 1, 1, 3)
        
        # Disable Pattern buttons - requires hardware MODE switch in ARP position
        for btn in pattern_buttons:
            btn.setEnabled(False)
            btn.setToolTip("Requires hardware MODE switch in ARP - MIDI control unreliable")
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #666666;
                    border: 1px solid #444444;
                    color: #999999;
                }
                QPushButton:checked {
                    background-color: #4a4a4a;
                    border: 2px solid #333333;
                    color: #888888;
                    font-weight: bold;
                }
            """)
        
        # Row 4: FW/BW Repeat (parameter 22)
        repeat_param = get_parameter_by_id(22)
        if repeat_param:
            repeat_widget = ToggleButton(repeat_param)
            repeat_widget.value_changed.connect(self.on_widget_value_changed)
            self.parameter_widgets[22] = repeat_widget
            repeat_widget.setEnabled(False)
            repeat_widget.setToolTip("MIDI control not supported by firmware")
            # Override styling to show disabled state
            repeat_widget.button.setStyleSheet("""
                QPushButton {
                    background-color: #666666;
                    border: 1px solid #444444;
                    color: #999999;
                }
            """)
            layout.addWidget(repeat_widget, 4, 1, 1, 3)
        
        # Row 5: Oct/Bank (parameter 193)
        octbank_label = QLabel("Oct/Bank")
        octbank_label.setStyleSheet("font-weight: normal; color: #4a4a2a;")
        layout.addWidget(octbank_label, 5, 0)

        octbank_layout = QHBoxLayout()
        octbank_layout.setSpacing(2)
        octbank_buttons = []
        octbank_texts = ["1", "2", "3"]
        for idx, text in enumerate(octbank_texts):
            btn = QPushButton(text)
            btn.setCheckable(True)
            btn.setMinimumHeight(30)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #999999;
                    border: 1px solid #666666;
                    color: white;
                }
                QPushButton:checked {
                    background-color: #6B8E23;
                    border: 2px solid #556B2F;
                    font-weight: bold;
                }
            """)
            if idx == 0:  # Default to 1
                btn.setChecked(True)
            octbank_buttons.append(btn)
            octbank_layout.addWidget(btn)

        # Make mutually exclusive AND track bank selection
        for idx, btn in enumerate(octbank_buttons):
            btn.clicked.connect(lambda checked, i=idx, buttons=octbank_buttons: self.on_bank_clicked(buttons, i))

        layout.addLayout(octbank_layout, 5, 1, 1, 3)
        
        # Row 6: Sequence selector
        seq_label = QLabel("Sequence")
        seq_label.setStyleSheet("font-weight: normal; color: #4a4a2a;")
        layout.addWidget(seq_label, 6, 0)

        # Sequence selector buttons (1, 2, 3, 4) - mutually exclusive
        seq_layout = QHBoxLayout()
        seq_layout.setSpacing(2)
        self.seq_buttons = []  # Store as instance variable
        for i in range(1, 5):
            btn = QPushButton(str(i))
            btn.setCheckable(True)
            btn.setMinimumHeight(30)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #999999;
                    border: 1px solid #666666;
                    color: white;
                }
                QPushButton:checked {
                    background-color: #6B8E23;
                    border: 2px solid #556B2F;
                    font-weight: bold;
                }
            """)
            if i == 1:  # Default to first sequence
                btn.setChecked(True)
            self.seq_buttons.append(btn)
            seq_layout.addWidget(btn)

        # Make mutually exclusive and handle sequence selection
        for idx, btn in enumerate(self.seq_buttons):
            btn.clicked.connect(lambda checked, i=idx: self.on_sequence_selected(i))

        layout.addLayout(seq_layout, 6, 1, 1, 3)
        
        # Row 7: Play and Hold buttons (these aren't parameters, they're transport controls)
        play_hold_layout = QHBoxLayout()
        play_hold_layout.setSpacing(5)
        
        self.play_btn = QPushButton("Play")
        self.play_btn.setCheckable(True)
        self.play_btn.setMinimumHeight(35)
        self.play_btn.setStyleSheet("""
            QPushButton {
                background-color: #4a4a4a;
                border: 2px solid #666666;
                color: white;
                font-weight: bold;
            }
            QPushButton:checked {
                background-color: #228B22;
                border: 2px solid #1a6b1a;
            }
        """)
        
        def on_play_changed():
            value = 1 if self.play_btn.isChecked() else 0
            self.parameter_changed.emit(173, value)  # Parameter 173 = Arp Play (CC 73)

        self.play_btn.clicked.connect(on_play_changed)
        
        self.hold_btn = QPushButton("Hold")
        self.hold_btn.setCheckable(True)
        self.hold_btn.setMinimumHeight(35)
        self.hold_btn.setStyleSheet("""
            QPushButton {
                background-color: #4a4a4a;
                border: 2px solid #666666;
                color: white;
                font-weight: bold;
            }
            QPushButton:checked {
                background-color: #4169E1;
                border: 2px solid #315bb3;
            }
        """)
        
        play_hold_layout.addWidget(self.play_btn)
        play_hold_layout.addWidget(self.hold_btn)
        layout.addLayout(play_hold_layout, 7, 0, 1, 4)
        
        def on_hold_changed():
            value = 1 if self.hold_btn.isChecked() else 0
            self.parameter_changed.emit(169, value)  # Parameter 169 = Arp Latch (CC 69)

        self.hold_btn.clicked.connect(on_hold_changed)
        
        return group
    
    def create_oscillators_section(self) -> QGroupBox:
        """Create the OSCILLATORS section (cyan box)"""
        group = QGroupBox("OSCILLATORS")
        group.setStyleSheet("""
            QGroupBox {
                background-color: #7FCDFF;
                border: 2px solid #666;
                border-radius: 5px;
                margin-top: 0px;
                font-weight: bold;
                font-size: 14pt;
                padding: 15px;
                padding-top: 30px;
            }
            QGroupBox::title {
                subcontrol-origin: padding;
                subcontrol-position: top center;
                padding: 5px 10px;
                color: black;
            }
        """)
    
        layout = QVBoxLayout(group)
        layout.setSpacing(5) #changed from 10
        layout.setContentsMargins(10, 20, 10, 10)
    
        # Row 1: Octave buttons for all oscillators - same height
        octave_row = QWidget()
        octave_row_layout = QHBoxLayout(octave_row)
        octave_row_layout.setSpacing(15)
        octave_row_layout.setContentsMargins(0, 0, 0, 0)
    
        # Create octave buttons for each oscillator
        # Hardcoded text to avoid encoding issues
        for osc_num in range(1, 5):
            octave_container = QWidget()
            octave_layout = QHBoxLayout(octave_container)
            octave_layout.setSpacing(2)
            octave_layout.setContentsMargins(0, 0, 0, 0)

            # Get parameter for this oscillator (174-177 for OSC 1-4)
            param_id = 173 + osc_num
            octave_param = get_parameter_by_id(param_id)
    
            if octave_param:
                # Value map: button index -> MIDI CC value (mid-point of ranges)
                # 0-31=16', 32-63=8', 64-95=4', 96-127=2'
                value_map = {0: 15, 1: 47, 2: 79, 3: 111}
        
                # Create parameter widget wrapper
                octave_widget = ParameterButtonGroupWidget(octave_param, value_map=value_map)
                octave_widget.value_changed.connect(self.on_widget_value_changed)
                self.parameter_widgets[param_id] = octave_widget
        
                # Apply custom styling to the buttons
                for button, _ in octave_widget.buttons:
                    button.setFixedSize(45, 25)
                    button.setStyleSheet("""
                        QPushButton {
                            background-color: #228B22;
                            border: 1px solid #1a6b1a;
                            color: white;
                            font-weight: bold;
                            font-size: 10px;
                            border-radius: 3px;
                            font-family: Arial, Helvetica, sans-serif;
                        }
                        QPushButton:checked {
                            background-color: #32CD32;
                            border: 2px solid #228B22;
                        }
                        QPushButton:hover {
                            background-color: #2a9d2a;
                        }
                    """)
                    # Set button text
                    if button.text() == "0":
                        button.setText("16'")
                    elif button.text() == "1":
                        button.setText("8'")
                    elif button.text() == "2":
                        button.setText("4'")
                    elif button.text() == "3":
                        button.setText("2'")
        
                octave_layout.addWidget(octave_widget)
    
            octave_row_layout.addWidget(octave_container)
    
        layout.addWidget(octave_row)
    
        # Row 2: Hard Sync Enable button and Frequency knobs
        controls_row = QWidget()
        controls_layout = QHBoxLayout(controls_row)
        controls_layout.setSpacing(15)
        controls_layout.setContentsMargins(0, 0, 0, 0)
    
        # Container for Hard Sync Enable with label below
        sync_enable_container = QWidget()
        sync_enable_container.setFixedWidth(95)  # Match freq knob container width
        sync_enable_layout = QVBoxLayout(sync_enable_container)
        sync_enable_layout.setSpacing(5)
        sync_enable_layout.setContentsMargins(0, 0, 0, 0)
    
        # Hard Sync Enable button (parameter 46)
        sync_enable_param = get_parameter_by_id(46)
        if sync_enable_param:
            sync_enable_btn = QPushButton()
            sync_enable_btn.setCheckable(True)
            sync_enable_btn.setFixedSize(70, 70)
            sync_enable_btn.setStyleSheet("""
                QPushButton {
                    background-color: #4a4a4a;
                    border: 2px solid #666666;
                    border-radius: 5px;
                }
                QPushButton:checked {
                    background-color: #CC0000;
                    border: 2px solid #990000;
                }
                QPushButton:hover {
                    background-color: #5a5a5a;
                }
                QPushButton:checked:hover {
                    background-color: #DD0000;
                }
            """)
    
            # Connect to parameter change
            def on_sync_enable_changed():
                value = 1 if sync_enable_btn.isChecked() else 0
                self.parameter_changed.emit(46, value)
    
            sync_enable_btn.clicked.connect(on_sync_enable_changed)
            sync_enable_layout.addWidget(sync_enable_btn, alignment=Qt.AlignCenter)
    
            # Store button reference for external updates
            self.sync_enable_btn = sync_enable_btn
    
            sync_enable_layout.addWidget(sync_enable_btn, alignment=Qt.AlignCenter)
    
        # Label below button
        sync_enable_label = QLabel("Hard Sync\nEnable")
        sync_enable_label.setStyleSheet("font-weight: bold; color: black; font-size: 9px;")
        sync_enable_label.setAlignment(Qt.AlignCenter)
        sync_enable_layout.addWidget(sync_enable_label, alignment=Qt.AlignCenter)
    
        #sync_enable_layout.addStretch()
    
        controls_layout.addWidget(sync_enable_container)
    
        # Frequency knobs for oscillators 2, 3, 4
        for osc_num in range(2, 5):
            # Parameter IDs: 116 (OSC2), 117 (OSC3), 118 (OSC4)
            param_id = 114 + osc_num
            freq_param = get_parameter_by_id(param_id)
    
            if freq_param:
                # Create display conversion function for this oscillator
                convert_func = lambda v, osc=osc_num: self.convert_freq_to_semitones(v, osc)
        
                freq_widget = ParameterDialWidget(freq_param, convert_display=convert_func)
                freq_widget.value_changed.connect(self.on_widget_value_changed)
                self.parameter_widgets[param_id] = freq_widget
                controls_layout.addWidget(freq_widget)
    
        layout.addWidget(controls_row)
        layout.setSpacing(0)  # Remove spacing before sync buttons

        # Row 3: Sync buttons
        sync_row = QWidget()
        sync_row_layout = QHBoxLayout(sync_row)
        sync_row_layout.setSpacing(15)  # Same as controls_layout
        sync_row_layout.setContentsMargins(0, 0, 0, 0)

        # Spacer matching Hard Sync container width
        spacer = QWidget()
        spacer.setFixedWidth(95)
        sync_row_layout.addWidget(spacer)

        # Sync buttons for oscillators 2, 3, 4 (params 47, 48, 49)
        for osc_num in range(2, 5):
            # Parameter IDs: 47 (OSC2 sync), 48 (OSC3 sync), 49 (OSC4 sync)
            param_id = 45 + osc_num
            sync_param = get_parameter_by_id(param_id)
    
            sync_btn = QPushButton(f"{osc_num-1}<--Sync")
            sync_btn.setCheckable(True)
            sync_btn.setFixedWidth(95)
            sync_btn.setMinimumHeight(30)
            sync_btn.setStyleSheet("""
                QPushButton {
                    background-color: #4a4a4a;
                    border: 2px solid #666666;
                    color: white;
                    font-weight: bold;
                    border-radius: 5px;
                    font-size: 10px;
                }
                QPushButton:checked {
                    background-color: #CC0000;
                    border: 2px solid #990000;
                }
                QPushButton:hover {
                    background-color: #5a5a5a;
                }
                QPushButton:checked:hover {
                    background-color: #DD0000;
                }
            """)
    
            if sync_param:
                # Connect to parameter change only if param exists
                def on_sync_changed(checked, pid=param_id):
                    value = 1 if checked else 0
                    self.parameter_changed.emit(pid, value)
        
                sync_btn.clicked.connect(on_sync_changed)
                
                # Store button references for updates
                if param_id == 47:
                    self.osc2_sync_btn = sync_btn
                elif param_id == 48:
                    self.osc3_sync_btn = sync_btn
                elif param_id == 49:
                    self.osc4_sync_btn = sync_btn
    
            sync_row_layout.addWidget(sync_btn)

        layout.addWidget(sync_row)
        layout.setSpacing(5)  # Restore normal spacing
    
        return group

    def create_stereo_delay_section(self) -> QGroupBox:
        """Create the STEREO DELAY section (purple box)"""
        group = QGroupBox("STEREO DELAY")
        group.setStyleSheet("""
            QGroupBox {
                background-color: #B89EED;
                border: 2px solid #666;
                border-radius: 5px;
                margin-top: 0px;
                font-weight: bold;
                font-size: 14pt;
                padding: 15px;
                padding-top: 30px;
            }
            QGroupBox::title {
                subcontrol-origin: padding;
                subcontrol-position: top center;
                padding: 5px 10px;
                color: black;
            }
        """)
        #group.setMinimumHeight(350) #DONT THINK WE NEED THIS
    
        layout = QVBoxLayout(group)
        layout.setSpacing(5)
        layout.setContentsMargins(10, 20, 10, 5)
    
        # Row 1: Dropdown controls
        dropdowns_layout = QVBoxLayout()
        dropdowns_layout.setSpacing(5) # Changed from 8 to 5
    
        # Delay Filter Brightness (parameter 52)
        brightness_layout = QHBoxLayout()
        brightness_label = QLabel("Delay Filter Brightness")
        brightness_label.setStyleSheet("font-weight: bold; color: black; font-size: 10px;")
        brightness_layout.addWidget(brightness_label)

        brightness_param = get_parameter_by_id(52)
        if brightness_param:
            # Create button group with value map: Dark=0, Bright=1
            value_map = {0: 0, 1: 1}
            brightness_widget = ParameterButtonGroupWidget(brightness_param, value_map=value_map)
            brightness_widget.value_changed.connect(self.on_widget_value_changed)
            self.parameter_widgets[52] = brightness_widget
    
            # Apply custom styling
            for button, _ in brightness_widget.buttons:
                button.setFixedHeight(30)
                button.setStyleSheet("""
                    QPushButton {
                        background-color: #999999;
                        border: 1px solid #666666;
                        color: white;
                        font-weight: bold;
                        border-radius: 3px;
                    }
                    QPushButton:checked {
                        background-color: #228B22;
                        border: 2px solid #1a6b1a;
                    }
                    QPushButton:hover {
                        background-color: #aaaaaa;
                    }
                """)
                # Set proper button text
                if button.text() == "0":
                    button.setText("Dark")
                elif button.text() == "1":
                    button.setText("Bright")
    
            brightness_layout.addWidget(brightness_widget)

        dropdowns_layout.addLayout(brightness_layout)
    
        # Delay CV Sync-Bend (parameter 53)
        syncbend_layout = QHBoxLayout()
        syncbend_label = QLabel("Delay CV Sync-Bend")
        syncbend_label.setStyleSheet("font-weight: bold; color: black; font-size: 10px;")
        syncbend_layout.addWidget(syncbend_label)

        syncbend_param = get_parameter_by_id(53)
        if syncbend_param:
            syncbend_btn = QPushButton("Off")
            syncbend_btn.setCheckable(True)
            syncbend_btn.setFixedHeight(30)
            syncbend_btn.setStyleSheet("""
                QPushButton {
                    background-color: #4a4a4a;
                    border: 2px solid #666666;
                    color: white;
                    font-weight: bold;
                    border-radius: 5px;
                }
                QPushButton:checked {
                    background-color: #228B22;
                    border: 2px solid #1a6b1a;
                }
                QPushButton:hover {
                    background-color: #5a5a5a;
                }
                QPushButton:checked:hover {
                    background-color: #2a9d2a;
                }
            """)
    
            def on_syncbend_changed():
                value = 1 if syncbend_btn.isChecked() else 0
                syncbend_btn.setText("On" if value else "Off")
                self.parameter_changed.emit(53, value)
    
            syncbend_btn.clicked.connect(on_syncbend_changed)
            self.syncbend_btn = syncbend_btn  # Store reference for updates
            syncbend_layout.addWidget(syncbend_btn)

        dropdowns_layout.addLayout(syncbend_layout)
    
        layout.addLayout(dropdowns_layout)
    
        # Row 2: Knobs
        knobs_layout = QHBoxLayout()
        knobs_layout.setSpacing(10)  # Changed from 15 to 10
    
        # Delay Spacing knob (parameter 13)
        spacing_param = get_parameter_by_id(113)
        if spacing_param:
            spacing_widget = ParameterDialWidget(spacing_param, convert_display=self.convert_spacing_to_percentage)
            spacing_widget.value_changed.connect(self.on_widget_value_changed)
            self.parameter_widgets[113] = spacing_widget
            knobs_layout.addWidget(spacing_widget, alignment=Qt.AlignCenter)

        # Delay Time knob (parameter 12)
        time_param = get_parameter_by_id(112)
        if time_param:
            time_widget = ParameterDialWidget(time_param, convert_display=self.convert_delay_time_to_ms)
            time_widget.value_changed.connect(self.on_widget_value_changed)
            self.parameter_widgets[112] = time_widget
            knobs_layout.addWidget(time_widget, alignment=Qt.AlignCenter)
    
        layout.addLayout(knobs_layout)
    
        # Row 3: Buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)
    
        # Delay Sync button (parameter 89)
        sync_param = get_parameter_by_id(51)
        if sync_param:
            sync_btn = QPushButton("Delay Sync")
            sync_btn.setCheckable(True)
            sync_btn.setMinimumHeight(35)
            sync_btn.setStyleSheet("""
                QPushButton {
                    background-color: #4a4a4a;
                    border: 2px solid #666666;
                    color: white;
                    font-weight: bold;
                    border-radius: 5px;
                }
                QPushButton:checked {
                    background-color: #228B22;
                    border: 2px solid #1a6b1a;
                }
                QPushButton:hover {
                    background-color: #5a5a5a;
                }
                QPushButton:checked:hover {
                    background-color: #2a9d2a;
                }
            """)
    
            def on_delay_sync_changed():
                value = 1 if sync_btn.isChecked() else 0
                self.parameter_changed.emit(51, value)
    
            sync_btn.clicked.connect(on_delay_sync_changed)
            self.delay_sync_btn = sync_btn
            buttons_layout.addWidget(sync_btn)

        # Delay Ping Pong button (parameter 88)
        pingpong_param = get_parameter_by_id(50)
        if pingpong_param:
            pingpong_btn = QPushButton("Delay Ping Pong")
            pingpong_btn.setCheckable(True)
            pingpong_btn.setMinimumHeight(35)
            pingpong_btn.setStyleSheet("""
                QPushButton {
                    background-color: #4a4a4a;
                    border: 2px solid #666666;
                    color: white;
                    font-weight: bold;
                    border-radius: 5px;
                }
                QPushButton:checked {
                    background-color: #228B22;
                    border: 2px solid #1a6b1a;
                }
                QPushButton:hover {
                    background-color: #5a5a5a;
                }
                QPushButton:checked:hover {
                    background-color: #2a9d2a;
                }
            """)
    
            def on_pingpong_changed():
                value = 1 if pingpong_btn.isChecked() else 0
                self.parameter_changed.emit(50, value)
    
            pingpong_btn.clicked.connect(on_pingpong_changed)
            self.delay_pingpong_btn = pingpong_btn
            buttons_layout.addWidget(pingpong_btn)
    
        layout.addLayout(buttons_layout)
    
        return group

    def create_output_section(self) -> QGroupBox:
        """Create the OUTPUT section (cyan box)"""
        group = QGroupBox("OUTPUT")
        group.setStyleSheet("""
            QGroupBox {
                background-color: #7FCDFF;
                border: 2px solid #666;
                border-radius: 5px;
                margin-top: 0px;
                font-weight: bold;
                font-size: 14pt;
                padding: 15px;
                padding-top: 30px;
            }
            QGroupBox::title {
                subcontrol-origin: padding;
                subcontrol-position: top center;
                padding: 5px 10px;
                color: black;
            }
        """)
    
        layout = QVBoxLayout(group)
        layout.setSpacing(15)
        layout.setContentsMargins(10, 20, 10, 10)
    
        # Paraphonic Unison (parameter 56)
        unison_layout = QHBoxLayout()
        unison_label = QLabel("Paraphonic Unison")
        unison_label.setStyleSheet("font-weight: bold; color: black; font-size: 10px;")
        unison_layout.addWidget(unison_label)

        unison_param = get_parameter_by_id(56)
        if unison_param:
            unison_btn = QPushButton("Off")
            unison_btn.setCheckable(True)
            unison_btn.setFixedHeight(30)
            unison_btn.setStyleSheet("""
                QPushButton {
                    background-color: #4a4a4a;
                    border: 2px solid #666666;
                    color: white;
                    font-weight: bold;
                    border-radius: 5px;
                }
                QPushButton:checked {
                    background-color: #228B22;
                    border: 2px solid #1a6b1a;
                }
                QPushButton:hover {
                    background-color: #5a5a5a;
                }
                QPushButton:checked:hover {
                    background-color: #2a9d2a;
                }
            """)
    
            def on_unison_changed():
                value = 1 if unison_btn.isChecked() else 0
                unison_btn.setText("On" if value else "Off")
                self.parameter_changed.emit(56, value)
    
            unison_btn.clicked.connect(on_unison_changed)
            self.unison_btn = unison_btn  # Store reference for updates
            unison_layout.addWidget(unison_btn)

        layout.addLayout(unison_layout)
    
        # Paraphony Mode (parameter 55)
        mode_layout = QVBoxLayout()
        mode_layout.setSpacing(5)

        mode_label = QLabel("Paraphony Mode")
        mode_label.setStyleSheet("font-weight: bold; color: black; font-size: 10px;")
        mode_label.setAlignment(Qt.AlignCenter)
        mode_layout.addWidget(mode_label)

        para_mode_param = get_parameter_by_id(55)
        if para_mode_param:
            # Value map: button text "1"→21, "2"→63, "4"→106
            # Create buttons manually since we need custom text
            mode_buttons_layout = QHBoxLayout()
            mode_buttons_layout.setSpacing(5)
    
            mode_buttons = []
            button_configs = [("1", 0), ("2", 1), ("4", 2)]
    
            for text, value in button_configs:
                btn = QPushButton(text)
                btn.setCheckable(True)
                btn.setFixedSize(40, 40)
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #228B22;
                        border: 1px solid #1a6b1a;
                        color: white;
                        font-weight: bold;
                        font-size: 14px;
                        border-radius: 3px;
                    }
                    QPushButton:checked {
                        background-color: #32CD32;
                        border: 2px solid #228B22;
                    }
                    QPushButton:hover {
                        background-color: #2a9d2a;
                    }
                """)
                if value == 21:  # Default to "1" (mono)
                    btn.setChecked(True)
                mode_buttons.append((btn, value))
                mode_buttons_layout.addWidget(btn)
    
            # Make mutually exclusive and handle parameter changes
            def on_para_mode_clicked(clicked_btn, clicked_value):
                for btn, _ in mode_buttons:
                    if btn == clicked_btn:
                        if not btn.isChecked():
                            btn.setChecked(True)
                    else:
                        btn.setChecked(False)
                self.parameter_changed.emit(55, clicked_value)
    
            # Connect each button explicitly to avoid closure issues
            btn1, val1 = mode_buttons[0]
            btn2, val2 = mode_buttons[1]
            btn3, val3 = mode_buttons[2]

            logger.info(f"Paraphony button setup: btn1={val1}, btn2={val2}, btn3={val3}")

            def handler1(checked):
                logger.info(f"Button 1 clicked, sending value {val1}")
                on_para_mode_clicked(btn1, val1)

            def handler2(checked):
                logger.info(f"Button 2 clicked, sending value {val2}")
                on_para_mode_clicked(btn2, val2)

            def handler3(checked):
                logger.info(f"Button 3 clicked, sending value {val3}")
                on_para_mode_clicked(btn3, val3)

            btn1.clicked.connect(handler1)
            btn2.clicked.connect(handler2)
            btn3.clicked.connect(handler3)
    
            mode_buttons_layout.addStretch()
            mode_layout.addLayout(mode_buttons_layout)

        layout.addLayout(mode_layout)
    
        # Multi Trig (parameter 57)
        multitrig_param = get_parameter_by_id(57)
        if multitrig_param:
            multitrig_btn = QPushButton("Multi Trig")
            multitrig_btn.setCheckable(True)
            multitrig_btn.setMinimumHeight(40)
            multitrig_btn.setStyleSheet("""
                QPushButton {
                    background-color: #4a4a4a;
                    border: 2px solid #666666;
                    color: white;
                    font-weight: bold;
                    border-radius: 5px;
                    font-size: 12px;
                }
                QPushButton:checked {
                    background-color: #CC0000;
                    border: 2px solid #990000;
                }
                QPushButton:hover {
                    background-color: #5a5a5a;
                }
                QPushButton:checked:hover {
                    background-color: #DD0000;
                }
            """)
    
            def on_multitrig_changed():
                value = 1 if multitrig_btn.isChecked() else 0
                self.parameter_changed.emit(57, value)
    
            multitrig_btn.clicked.connect(on_multitrig_changed)
            self.multitrig_btn = multitrig_btn  # Store reference for updates
            layout.addWidget(multitrig_btn)
    
        layout.addStretch()
    
        return group
    
    def create_bottom_controls(self) -> QWidget:
        """Create the bottom row of global controls"""
        container = QWidget()
        container.setStyleSheet("background-color: #3a3a3a; border-radius: 5px;")
    
        main_layout = QHBoxLayout(container)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(15, 15, 15, 15)
    
        # COLUMN 1: Keyboard Octave Transpose and Delayed KB Octave Shift
        col1 = QWidget()
        col1_layout = QVBoxLayout(col1)
        col1_layout.setSpacing(10)
    
        # Keyboard Octave Transpose label
        kot_label = QLabel("Keyboard Octave Transpose")
        kot_label.setStyleSheet("color: white; font-weight: bold; font-size: 10px;")
        col1_layout.addWidget(kot_label)
    
        # Radio buttons for octave transpose
        kot_buttons_layout = QHBoxLayout()
        kot_buttons_layout.setSpacing(3)
        kot_buttons = []
        for i, val in enumerate(["-2", "-1", "0", "+1", "+2"]):
            btn = QPushButton(val)
            btn.setCheckable(True)
            btn.setFixedSize(45, 30)  # Increased width from 35 to 45
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #228B22;
                    border: 1px solid #1a6b1a;
                    color: white;
                    font-weight: bold;
                    font-size: 11px;
                    border-radius: 3px;
                }
                QPushButton:checked {
                    background-color: #32CD32;
                    border: 2px solid #228B22;
                }
                QPushButton:hover {
                    background-color: #2a9d2a;
                }
            """)
            if i == 2:  # Default to 0
                btn.setChecked(True)
            kot_buttons.append(btn)
            kot_buttons_layout.addWidget(btn)
    
        # Make mutually exclusive and wire to parameter 38
        for i, btn in enumerate(kot_buttons):
            btn.clicked.connect(lambda checked, idx=i, buttons=kot_buttons: self.on_kot_clicked(buttons, idx))
    
        col1_layout.addLayout(kot_buttons_layout)
    
        # Delayed Keyboard Octave Shift toggle
        dkos_btn = QPushButton("Off")
        dkos_btn.setCheckable(True)
        dkos_btn.setFixedHeight(35)
        dkos_btn.setStyleSheet("""
            QPushButton {
                background-color: #4a4a4a;
                border: 2px solid #666666;
                color: white;
                font-weight: bold;
                border-radius: 5px;
                font-size: 9px;
            }
            QPushButton:checked {
                background-color: #228B22;
                border: 2px solid #1a6b1a;
            }
            QPushButton:hover {
                background-color: #5a5a5a;
            }
        """)
        def on_dkos_changed(checked):
            dkos_btn.setText("On" if checked else "Off")
            self.parameter_changed.emit(39, 1 if checked else 0)

        dkos_btn.toggled.connect(on_dkos_changed)
        self.dkos_btn = dkos_btn
    
        dkos_label = QLabel("Delayed Keyboard Octave Shift")
        dkos_label.setStyleSheet("color: white; font-weight: bold; font-size: 9px;")
    
        col1_layout.addWidget(dkos_label)
        col1_layout.addWidget(dkos_btn)
        col1_layout.addStretch()
    
        main_layout.addWidget(col1)
    
        # COLUMN 2: Glide controls
        col2 = QWidget()
        col2_layout = QVBoxLayout(col2)
        col2_layout.setSpacing(8)
    
        # Glide toggle
        glide_label = QLabel("Glide")
        glide_label.setStyleSheet("color: white; font-weight: bold; font-size: 10px;")
        col2_layout.addWidget(glide_label)
    
        glide_btn = QPushButton("Off")
        glide_btn.setCheckable(True)
        glide_btn.setFixedHeight(30)
        glide_btn.setStyleSheet("""
            QPushButton {
                background-color: #4a4a4a;
                border: 2px solid #666666;
                color: white;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:checked {
                background-color: #228B22;
                border: 2px solid #1a6b1a;
            }
            QPushButton:hover {
                background-color: #5a5a5a;
            }
        """)
        def on_glide_changed(checked):
            glide_btn.setText("On" if checked else "Off")
            if checked:
                # Glide turned ON - send current Glide Time value
                current_glide_time = self.gt_slider.value() if hasattr(self, 'gt_slider') else 0
                self.parameter_changed.emit(105, current_glide_time)
            else:
                # Glide turned OFF - set slider to 0 and send Glide Time = 0
                if hasattr(self, 'gt_slider'):
                    self.gt_slider.blockSignals(True)
                    self.gt_slider.setValue(0)
                    self.gt_value_label.setText("0")
                    self.gt_slider.blockSignals(False)
                self.parameter_changed.emit(105, 0)
            
            # Also send the Glide On/Off CC
            self.parameter_changed.emit(65, 1 if checked else 0)

        glide_btn.toggled.connect(on_glide_changed)
        self.glide_btn = glide_btn
        col2_layout.addWidget(glide_btn)
    
        # Glide Type radio buttons
        glide_type_label = QLabel("Glide Type")
        glide_type_label.setStyleSheet("color: white; font-weight: bold; font-size: 10px;")
        col2_layout.addWidget(glide_type_label)
    
        glide_type_buttons = []
        for text in ["Linear Constant Rate", "Linear Constant Time", "Exponential"]:
            btn = QPushButton(text)
            btn.setCheckable(True)
            btn.setFixedHeight(25)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #999999;
                    border: 1px solid #666666;
                    color: white;
                    font-weight: bold;
                    font-size: 9px;
                    border-radius: 3px;
                }
                QPushButton:checked {
                    background-color: #228B22;
                    border: 2px solid #1a6b1a;
                }
                QPushButton:hover {
                    background-color: #aaaaaa;
                }
            """)
            if text == "Linear Constant Rate":  # Default
                btn.setChecked(True)
            glide_type_buttons.append(btn)
            col2_layout.addWidget(btn)
    
        # Make mutually exclusive and wire to parameter 40
        for i, btn in enumerate(glide_type_buttons):
            btn.clicked.connect(lambda checked, idx=i, buttons=glide_type_buttons: self.on_glide_type_clicked(buttons, idx))
            
        self.glide_type_buttons = glide_type_buttons
    
        # Gated Glide toggle
        gated_glide_label = QLabel("Gated Glide")
        gated_glide_label.setStyleSheet("color: white; font-weight: bold; font-size: 10px;")
        col2_layout.addWidget(gated_glide_label)
    
        gated_glide_btn = QPushButton("On")
        gated_glide_btn.setCheckable(True)
        gated_glide_btn.setChecked(True)
        gated_glide_btn.setFixedHeight(25)
        gated_glide_btn.setStyleSheet("""
            QPushButton {
                background-color: #4a4a4a;
                border: 2px solid #666666;
                color: white;
                font-weight: bold;
                border-radius: 5px;
                font-size: 9px;
            }
            QPushButton:checked {
                background-color: #228B22;
                border: 2px solid #1a6b1a;
            }
            QPushButton:hover {
                background-color: #5a5a5a;
            }
        """)
        def on_gated_glide_changed(checked):
            gated_glide_btn.setText("On" if checked else "Off")
            self.parameter_changed.emit(41, 1 if checked else 0)

        gated_glide_btn.toggled.connect(on_gated_glide_changed)
        self.gated_glide_btn = gated_glide_btn
        col2_layout.addWidget(gated_glide_btn)
    
        # Legato Glide toggle
        legato_glide_label = QLabel("Legato Glide")
        legato_glide_label.setStyleSheet("color: white; font-weight: bold; font-size: 10px;")
        col2_layout.addWidget(legato_glide_label)
    
        legato_glide_btn = QPushButton("Off")
        legato_glide_btn.setCheckable(True)
        legato_glide_btn.setFixedHeight(25)
        legato_glide_btn.setStyleSheet("""
            QPushButton {
                background-color: #4a4a4a;
                border: 2px solid #666666;
                color: white;
                font-weight: bold;
                border-radius: 5px;
                font-size: 9px;
            }
            QPushButton:checked {
                background-color: #228B22;
                border: 2px solid #1a6b1a;
            }
            QPushButton:hover {
                background-color: #5a5a5a;
            }
        """)
        def on_legato_glide_changed(checked):
            legato_glide_btn.setText("On" if checked else "Off")
            self.parameter_changed.emit(42, 1 if checked else 0)

        legato_glide_btn.toggled.connect(on_legato_glide_changed)
        self.legato_glide_btn = legato_glide_btn
        col2_layout.addWidget(legato_glide_btn)
    
        col2_layout.addStretch()
        main_layout.addWidget(col2)
    
        # COLUMN 3: Sliders
        col3 = QWidget()
        col3_layout = QVBoxLayout(col3)
        col3_layout.setSpacing(10)
    
        # Pitch Bend Range
        pbr_label = QLabel("Pitch Bend Range")
        pbr_label.setStyleSheet("color: white; font-weight: bold; font-size: 10px;")
        col3_layout.addWidget(pbr_label)
    
        pbr_container = QHBoxLayout()
        pbr_slider = QSlider(Qt.Horizontal)
        pbr_slider.setMinimum(0)
        pbr_slider.setMaximum(12)
        pbr_slider.setValue(2)
        pbr_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                background: #2a2a2a;
                height: 6px;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #666;
                width: 14px;
                margin: -4px 0;
                border-radius: 7px;
            }
            QSlider::handle:horizontal:hover {
                background: #888;
            }
        """)
        pbr_value = QLabel("2")
        pbr_value.setStyleSheet("color: white; min-width: 50px;")
        def on_pbr_changed(v):
            pbr_value.setText(str(v))
            self.parameter_changed.emit(37, v)

        pbr_slider.valueChanged.connect(on_pbr_changed)
        self.install_slider_double_click_reset(pbr_slider, 2)
        self.pbr_slider = pbr_slider  
        self.pbr_value_label = pbr_value  
        pbr_container.addWidget(pbr_slider)
        pbr_container.addWidget(pbr_value)
        col3_layout.addLayout(pbr_container)
    
        # Pitch Variance
        pv_label = QLabel("Pitch Variance")
        pv_label.setStyleSheet("color: white; font-weight: bold; font-size: 10px;")
        col3_layout.addWidget(pv_label)
    
        pv_container = QHBoxLayout()
        pv_slider = QSlider(Qt.Horizontal)
        pv_slider.setMinimum(0)
        pv_slider.setMaximum(40)
        pv_slider.setValue(0)
        pv_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                background: #2a2a2a;
                height: 6px;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #666;
                width: 14px;
                margin: -4px 0;
                border-radius: 7px;
            }
            QSlider::handle:horizontal:hover {
                background: #888;
            }
        """)
        pv_value = QLabel("0 cents")
        pv_value.setStyleSheet("color: white; min-width: 70px;")  # Increased width for " cents"
        def on_pv_changed(v):
            pv_value.setText(f"{v} cents")
            # Multiply by 10 for parameter (slider 0-40 → param 0-400)
            self.parameter_changed.emit(58, v * 10)

        pv_slider.valueChanged.connect(on_pv_changed)
        self.install_slider_double_click_reset(pv_slider, 0)
        self.pv_slider = pv_slider
        self.pv_value_label = pv_value
        pv_container.addWidget(pv_slider)
        pv_container.addWidget(pv_value)
        col3_layout.addLayout(pv_container)
    
        # Noise Filter Cutoff
        nfc_label = QLabel("Noise Filter Cutoff")
        nfc_label.setStyleSheet("color: white; font-weight: bold; font-size: 10px;")
        col3_layout.addWidget(nfc_label)
    
        nfc_container = QHBoxLayout()
        nfc_slider = QSlider(Qt.Horizontal)
        nfc_slider.setMinimum(0)
        nfc_slider.setMaximum(16383)
        nfc_slider.setValue(16383)
        nfc_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                background: #2a2a2a;
                height: 6px;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #666;
                width: 14px;
                margin: -4px 0;
                border-radius: 7px;
            }
            QSlider::handle:horizontal:hover {
                background: #888;
            }
        """)
        nfc_value = QLabel("16383")
        nfc_value.setStyleSheet("color: white; min-width: 50px;")
        def on_nfc_changed(v):
            nfc_value.setText(str(v))
            self.parameter_changed.emit(71, v)

        nfc_slider.valueChanged.connect(on_nfc_changed)
        self.install_slider_double_click_reset(nfc_slider, 16383)
        self.nfc_slider = nfc_slider
        self.nfc_value_label = nfc_value
        nfc_container.addWidget(nfc_slider)
        nfc_container.addWidget(nfc_value)
        col3_layout.addLayout(nfc_container)
    
        # Glide Time
        gt_label = QLabel("Glide Time")
        gt_label.setStyleSheet("color: white; font-weight: bold; font-size: 10px;")
        col3_layout.addWidget(gt_label)
    
        gt_container = QHBoxLayout()
        gt_slider = QSlider(Qt.Horizontal)
        gt_slider.setMinimum(0)
        gt_slider.setMaximum(16383)
        gt_slider.setValue(0)
        gt_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                background: #2a2a2a;
                height: 6px;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #666;
                width: 14px;
                margin: -4px 0;
                border-radius: 7px;
            }
            QSlider::handle:horizontal:hover {
                background: #888;
            }
        """)
        gt_value = QLabel("0")
        gt_value.setStyleSheet("color: white; min-width: 50px;")
        
        def on_gt_changed(v):
            gt_value.setText(str(v))
            # Always send parameter change when slider moves
            # The coordination with Glide On/Off happens at the button level
            self.parameter_changed.emit(105, v)

        gt_slider.valueChanged.connect(on_gt_changed)
        self.install_slider_double_click_reset(gt_slider, 0)
        self.gt_slider = gt_slider  # Store reference
        self.gt_value_label = gt_value  # Store reference
        gt_container.addWidget(gt_slider)
        gt_container.addWidget(gt_value)
        col3_layout.addLayout(gt_container)
    
        col3_layout.addStretch()
        main_layout.addWidget(col3)
    
        # COLUMN 4: Note Priority, LFO Polarity, Tap-Tempo
        col4 = QWidget()
        col4_layout = QVBoxLayout(col4)
        col4_layout.setSpacing(8)
    
        # Note Priority radio buttons
        np_label = QLabel("Note Priority")
        np_label.setStyleSheet("color: white; font-weight: bold; font-size: 10px;")
        col4_layout.addWidget(np_label)
    
        np_buttons = []
        for text in ["Last Note", "Low Note", "High Note"]:
            btn = QPushButton(text)
            btn.setCheckable(True)
            btn.setFixedHeight(25)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #999999;
                    border: 1px solid #666666;
                    color: white;
                    font-weight: bold;
                    font-size: 9px;
                    border-radius: 3px;
                }
                QPushButton:checked {
                    background-color: #228B22;
                    border: 2px solid #1a6b1a;
                }
                QPushButton:hover {
                    background-color: #aaaaaa;
                }
            """)
            if text == "Last Note":  # Default
                btn.setChecked(True)
            np_buttons.append(btn)
            col4_layout.addWidget(btn)
    
        # Make mutually exclusive and wire to parameter 3
        # Value map: Last Note=2, Low Note=0, High Note=1
        value_map = [2, 0, 1]  # Button indices 0,1,2 map to param values 2,0,1
        for i, btn in enumerate(np_buttons):
            btn.clicked.connect(lambda checked, idx=i, buttons=np_buttons, val=value_map[i]: 
                               self.on_np_clicked(buttons, idx, val))
        self.np_buttons = np_buttons  
        self.np_value_map = value_map  
        
        # LFO Polarity radio buttons
        lfo_label = QLabel("LFO Polarity")
        lfo_label.setStyleSheet("color: white; font-weight: bold; font-size: 10px;")
        col4_layout.addWidget(lfo_label)
    
        lfo_buttons = []
        for text in ["Unipolar", "Bipolar"]:
            btn = QPushButton(text)
            btn.setCheckable(True)
            btn.setFixedHeight(25)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #999999;
                    border: 1px solid #666666;
                    color: white;
                    font-weight: bold;
                    font-size: 9px;
                    border-radius: 3px;
                }
                QPushButton:checked {
                    background-color: #228B22;
                    border: 2px solid #1a6b1a;
                }
                QPushButton:hover {
                    background-color: #aaaaaa;
                }
            """)
            if text == "Bipolar":  # Default
                btn.setChecked(True)
            lfo_buttons.append(btn)
            col4_layout.addWidget(btn)
    
        # Make mutually exclusive and wire to parameter 70 (Unipolar=0, Bipolar=1)
        for i, btn in enumerate(lfo_buttons):
            btn.clicked.connect(lambda checked, idx=i, buttons=lfo_buttons: 
                               self.on_lfo_polarity_clicked(buttons, idx))
                               
        self.lfo_buttons = lfo_buttons
    
        # Tap-Tempo Clock Division Persistence toggle
        ttcdp_label = QLabel("Tap-Tempo Clock Division Persistence")
        ttcdp_label.setStyleSheet("color: white; font-weight: bold; font-size: 9px;")
        col4_layout.addWidget(ttcdp_label)
    
        ttcdp_btn = QPushButton("Off")
        ttcdp_btn.setCheckable(True)
        ttcdp_btn.setFixedHeight(35)
        ttcdp_btn.setStyleSheet("""
            QPushButton {
                background-color: #4a4a4a;
                border: 2px solid #666666;
                color: white;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:checked {
                background-color: #228B22;
                border: 2px solid #1a6b1a;
            }
            QPushButton:hover {
                background-color: #5a5a5a;
            }
        """)
        def on_ttcdp_changed(checked):
            ttcdp_btn.setText("On" if checked else "Off")
            self.parameter_changed.emit(54, 1 if checked else 0)

        ttcdp_btn.toggled.connect(on_ttcdp_changed)
        self.ttcdp_btn = ttcdp_btn 
        col4_layout.addWidget(ttcdp_btn)
    
        col4_layout.addStretch()
        main_layout.addWidget(col4)
    
        return container

    def select_exclusive_button(self, buttons, selected_idx):
        """Make buttons mutually exclusive"""
        if buttons[selected_idx].isChecked():
            for i, btn in enumerate(buttons):
                if i != selected_idx:
                    btn.setChecked(False)
        else:
            buttons[selected_idx].setChecked(True)
    
    def create_delay_knob(self, label_text: str) -> QWidget:
        """Create a knob for the delay section"""
        container = QWidget()
        container.setFixedWidth(95)
        layout = QVBoxLayout(container)
        layout.setSpacing(2)
        layout.setContentsMargins(0, 0, 0, 0)
    
        # Label
        label = QLabel(label_text)
        label.setStyleSheet("font-weight: bold; color: black; font-size: 11px;")
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)
    
        # Knob
        dial = SmoothDial()
        dial.setMinimum(0)
        dial.setMaximum(16383)
        dial.setValue(8192)
        dial.setNotchesVisible(True)
        dial.setFixedSize(70, 70)
        dial.setStyleSheet("""
            QDial {
                background-color: #2a2a2a;
                border-radius: 35px;
            }
        """)
        layout.addWidget(dial, alignment=Qt.AlignCenter)
    
        # Value display
        value_label = QLabel("8192")
        value_label.setStyleSheet("font-weight: bold; color: black; font-size: 11px;")
        value_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(value_label)
    
        # Update value display when knob changes
        dial.valueChanged.connect(lambda v: value_label.setText(str(v)))
    
        return container
    
    def create_oscillator_column(self, osc_num: int) -> QWidget:
        """Create a single oscillator column"""
        column = QWidget()
        layout = QVBoxLayout(column)
        layout.setSpacing(8)
        layout.setContentsMargins(5, 5, 5, 5)
    
        # Octave selector buttons (16', 8', 4', 2')
        octave_container = QWidget()
        octave_layout = QHBoxLayout(octave_container)
        octave_layout.setSpacing(2)
        octave_layout.setContentsMargins(0, 0, 0, 0)
    
        octave_values = ["16'", "8'", "4'", "2'"]
        for octave in octave_values:
            btn = QPushButton(octave)
            btn.setCheckable(True)
            btn.setFixedSize(35, 25)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #228B22;
                    border: 1px solid #1a6b1a;
                    color: white;
                    font-weight: bold;
                    font-size: 10px;
                    border-radius: 3px;
                }
                QPushButton:checked {
                    background-color: #32CD32;
                    border: 2px solid #228B22;
                }
                QPushButton:hover {
                    background-color: #2a9d2a;
                }
            """)
            # Default to 8' selected
            if octave == "8'":
                btn.setChecked(True)
            octave_layout.addWidget(btn)
    
        layout.addWidget(octave_container, alignment=Qt.AlignCenter)
    
        # Frequency knob (only for oscillators 2, 3, 4)
        if osc_num > 1:
            freq_knob = self.create_frequency_knob(osc_num)
            layout.addWidget(freq_knob, alignment=Qt.AlignCenter)
        
            # Sync button
            sync_btn = QPushButton(f"{osc_num-1}<->Sync")
            sync_btn.setCheckable(True)
            sync_btn.setFixedWidth(120)
            sync_btn.setMinimumHeight(30)
            sync_btn.setStyleSheet("""
                QPushButton {
                    background-color: #4a4a4a;
                    border: 2px solid #666666;
                    color: white;
                    font-weight: bold;
                    border-radius: 5px;
                    font-size: 10px;
                }
                QPushButton:checked {
                    background-color: #CC0000;
                    border: 2px solid #990000;
                }
                QPushButton:hover {
                    background-color: #5a5a5a;
                }
                QPushButton:checked:hover {
                    background-color: #DD0000;
                }
            """)
            layout.addWidget(sync_btn, alignment=Qt.AlignCenter)
        else:
            # Oscillator 1: just add spacing to align with other columns
            layout.addStretch()
    
        return column

    def create_frequency_knob(self, osc_num: int) -> QWidget:
        """Create a frequency knob for an oscillator"""
        container = QWidget()
        container.setFixedWidth(95)  # Set fixed width for alignment
        layout = QVBoxLayout(container)
        layout.setSpacing(2)
        layout.setContentsMargins(0, 0, 0, 0)
    
        # Label
        label = QLabel("Frequency")
        label.setStyleSheet("font-weight: bold; color: black; font-size: 11px;")
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)
    
        # Knob
        dial = SmoothDial()
        dial.setMinimum(0)
        dial.setMaximum(16383)
        dial.setValue(8192)
        dial.setNotchesVisible(True)
        dial.setFixedSize(70, 70)
        dial.setStyleSheet("""
            QDial {
                background-color: #2a2a2a;
                border-radius: 35px;
            }
        """)
        layout.addWidget(dial, alignment=Qt.AlignCenter)
    
        # Value display
        value_label = QLabel("0")
        value_label.setStyleSheet("font-weight: bold; color: black; font-size: 11px;")
        value_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(value_label)
    
        # Update value display when knob changes
        dial.valueChanged.connect(lambda v: value_label.setText(str(v)))
        value_label.setText(str(dial.value()))
    
        #layout.addStretch()
    
        return container
    
    def on_widget_value_changed(self, param_id: int, value: int):
        """Forward parameter changes from widgets"""
        logger.info(f"on_widget_value_changed called: param_id={param_id}, value={value}")
        # Special handling for Arp/Seq Swing (param 23) - turn off Triplet button if manually adjusted
        if param_id == 23 and hasattr(self, 'triplet_button') and self.triplet_button.isChecked():
            triplet_value = int((44.0 / 56.0) * 16383)  # 12873
            if abs(value - triplet_value) > 50:  # Tolerance for rounding
                self.triplet_button.blockSignals(True)
                self.triplet_button.setChecked(False)
                self.triplet_button.blockSignals(False)
        
        self.parameter_changed.emit(param_id, value)
    
    def set_parameter_value(self, param_id: int, value: int):
        """Update a parameter widget's value"""
        if param_id in self.parameter_widgets:
            self.parameter_widgets[param_id].set_value_silently(value)

    def convert_display_to_swing(self, percentage: int) -> int:
        """Convert 22-78% display to 0-16383"""
        return int(((percentage - 22) / 56.0) * 16383)

    def convert_delay_time_to_ms(self, value: int) -> str:
        """Convert 0-16383 to 35-780ms"""
        ms = 35 + (value / 16383.0) * 745
        return f"{int(ms)}ms"

    def convert_spacing_to_percentage(self, value: int) -> str:
        """Convert 0-16383 to -100% to +100% (center=0)"""
        percentage = ((value / 16383.0) - 0.5) * 200
        if percentage > 0:
            return f"+{int(percentage)}%"
        elif percentage < 0:
            return f"{int(percentage)}%"
        else:
            return "0%"

    def convert_freq_to_semitones(self, value: int, osc_num: int) -> str:
        """Convert frequency value to semitones based on range setting"""
        # Get range setting for this oscillator (params 143, 144, 145)
        range_param_id = 142 + osc_num  # OSC2=143, OSC3=144, OSC4=145
        range_setting = 7  # Default
    
        # Try to get actual range from global settings
        if range_param_id in self.parameter_widgets:
            range_setting = self.parameter_widgets[range_param_id].get_value()
    
        # Convert value to semitones relative to center
        semitones = ((value / 16383.0) - 0.5) * 2 * range_setting
    
        if semitones > 0:
            return f"+{int(semitones)}"
        elif semitones < 0:
            return f"{int(semitones)}"
        else:
            return "0"

    def send_program_change(self, bank: int, sequence: int):
        """Send MIDI Program Change for sequence selection"""
        program = (bank - 1) * 4 + sequence
        logger.info(f"Send Program Change: {program} (Bank {bank}, Seq {sequence})")
    
        # Program Change uses parameter IDs 300-311 (for programs 1-12)
        # Parameter ID = 299 + program number
        param_id = 299 + program
    
        # Get the main window's MIDI manager
        main_window = self.window()
        while main_window and not isinstance(main_window, QMainWindow):
            main_window = main_window.parent()
    
        if main_window and hasattr(main_window, 'midi_manager'):
            # Value should be the program number (the connection.py code will handle conversion)
            main_window.midi_manager.set_parameter(param_id, program)
        
    def on_sequence_selected(self, seq_index: int):
        """Handle sequence button selection"""
        # Make buttons mutually exclusive
        self.select_exclusive_button(self.seq_buttons, seq_index)
    
        # Update current sequence (1-based)
        self.current_sequence = seq_index + 1
    
        # Only send program change if MODE is SEQ (value = 1)
        if self.current_mode == 1:
            self.send_program_change(self.current_bank, self.current_sequence)
    
    def on_mode_clicked(self, buttons, mode_index: int):
        """Handle mode button click"""
        self.select_exclusive_button(buttons, mode_index)
        self.current_mode = mode_index
        value_map = [21, 63, 106]  # CC ranges for ARP/SEQ/REC
        self.parameter_changed.emit(191, value_map[mode_index])  # Changed from 91 to 191

    def on_pattern_clicked(self, buttons, pattern_index: int):
        """Handle pattern button click"""
        self.select_exclusive_button(buttons, pattern_index)
        value_map = [21, 63, 106]  # CC ranges for ORDER/FW-BW/RANDOM
        self.parameter_changed.emit(192, value_map[pattern_index])  # Changed from 92 to 192

    def on_bank_clicked(self, buttons, bank_index: int):
        """Handle bank button click"""
        self.select_exclusive_button(buttons, bank_index)
        self.current_bank = bank_index + 1
        value_map = [21, 63, 106]  # CC ranges for banks 1/2/3
        self.parameter_changed.emit(193, value_map[bank_index])  # Changed from 93 to 193
        
    def on_kot_clicked(self, buttons, index: int):
        """Handle keyboard octave transpose button click"""
        self.select_exclusive_button(buttons, index)
        # Emit parameter change (index 0-4 maps to values 0-4 for -2,-1,0,+1,+2)
        self.parameter_changed.emit(38, index)

    def on_glide_type_clicked(self, buttons, index: int):
        """Handle glide type button click - LCR=0, LCT=1, Exp=2"""
        self.select_exclusive_button(buttons, index)
        self.parameter_changed.emit(40, index)

    def on_np_clicked(self, buttons, index: int, value: int):
        """Handle note priority button click"""
        self.select_exclusive_button(buttons, index)
        self.parameter_changed.emit(3, value)

    def on_lfo_polarity_clicked(self, buttons, index: int):
        """Handle LFO polarity button click - Unipolar=0, Bipolar=1"""
        self.select_exclusive_button(buttons, index)
        self.parameter_changed.emit(70, index)

    def install_slider_double_click_reset(self, slider, default_value):
        """Install event filter on slider to reset to default on double-click"""
        from PyQt5.QtCore import QObject, QEvent
        
        class SliderEventFilter(QObject):
            def __init__(self, slider_widget, default_val, parent=None):
                super().__init__(parent)
                self.slider_widget = slider_widget
                self.default_val = default_val
            
            def eventFilter(self, obj, event):
                if obj == self.slider_widget and event.type() == QEvent.MouseButtonDblClick:
                    self.slider_widget.setValue(self.default_val)
                    return True
                return False
        
        filter_obj = SliderEventFilter(slider, default_value, self)
        slider.installEventFilter(filter_obj)
        
        # Store reference so it doesn't get garbage collected
        if not hasattr(self, '_slider_filters'):
            self._slider_filters = []
        self._slider_filters.append(filter_obj)

    def get_parameter_widgets(self) -> Dict[int, 'ParameterWidget']:
        """Return the dictionary of parameter widgets for external access"""
        return self.parameter_widgets

    def update_parameter_value(self, param_id: int, value: int):
        """Update a parameter's UI widget with a new value"""
        # Handle widgets that use the standard ParameterWidget interface
        if param_id in self.parameter_widgets:
            widget = self.parameter_widgets[param_id]
            if hasattr(widget, 'set_value_silently'):
                widget.set_value_silently(value)
                return
        
        # Handle special widgets created directly without ParameterWidget wrapper
        
        # Multi Trig (param 57)
        if param_id == 57 and hasattr(self, 'multitrig_btn'):
            self.multitrig_btn.blockSignals(True)
            self.multitrig_btn.setChecked(bool(value))
            self.multitrig_btn.blockSignals(False)
        
        # Hard Sync Enable (param 46)
        elif param_id == 46 and hasattr(self, 'sync_enable_btn'):
            self.sync_enable_btn.blockSignals(True)
            self.sync_enable_btn.setChecked(bool(value))
            self.sync_enable_btn.blockSignals(False)
        
        # Delay CV Sync-Bend (param 53)
        elif param_id == 53 and hasattr(self, 'syncbend_btn'):
            self.syncbend_btn.blockSignals(True)
            self.syncbend_btn.setChecked(bool(value))
            self.syncbend_btn.setText("On" if value else "Off")
            self.syncbend_btn.blockSignals(False)
        
        # Paraphonic Unison (param 56)
        elif param_id == 56 and hasattr(self, 'unison_btn'):
            self.unison_btn.blockSignals(True)
            self.unison_btn.setChecked(bool(value))
            self.unison_btn.setText("On" if value else "Off")
            self.unison_btn.blockSignals(False)
        
        # Delay Sync (param 51)
        elif param_id == 51 and hasattr(self, 'delay_sync_btn'):
            self.delay_sync_btn.blockSignals(True)
            self.delay_sync_btn.setChecked(bool(value))
            self.delay_sync_btn.blockSignals(False)
        
        # Delay Ping Pong (param 50)
        elif param_id == 50 and hasattr(self, 'delay_pingpong_btn'):
            self.delay_pingpong_btn.blockSignals(True)
            self.delay_pingpong_btn.setChecked(bool(value))
            self.delay_pingpong_btn.blockSignals(False)
        
        # Osc 2 Sync (param 47)
        elif param_id == 47 and hasattr(self, 'osc2_sync_btn'):
            self.osc2_sync_btn.blockSignals(True)
            self.osc2_sync_btn.setChecked(bool(value))
            self.osc2_sync_btn.blockSignals(False)
        
        # Osc 3 Sync (param 48)
        elif param_id == 48 and hasattr(self, 'osc3_sync_btn'):
            self.osc3_sync_btn.blockSignals(True)
            self.osc3_sync_btn.setChecked(bool(value))
            self.osc3_sync_btn.blockSignals(False)
        
        # Osc 4 Sync (param 49)
        elif param_id == 49 and hasattr(self, 'osc4_sync_btn'):
            self.osc4_sync_btn.blockSignals(True)
            self.osc4_sync_btn.setChecked(bool(value))
            self.osc4_sync_btn.blockSignals(False)
        
        # Delayed KB Octave Shift (param 39)
        elif param_id == 39 and hasattr(self, 'dkos_btn'):
            self.dkos_btn.blockSignals(True)
            self.dkos_btn.setChecked(bool(value))
            self.dkos_btn.setText("On" if value else "Off")
            self.dkos_btn.blockSignals(False)
        
        # Gated Glide (param 41)
        elif param_id == 41 and hasattr(self, 'gated_glide_btn'):
            self.gated_glide_btn.blockSignals(True)
            self.gated_glide_btn.setChecked(bool(value))
            self.gated_glide_btn.setText("On" if value else "Off")
            self.gated_glide_btn.blockSignals(False)
        
        # Legato Glide (param 42)
        elif param_id == 42 and hasattr(self, 'legato_glide_btn'):
            self.legato_glide_btn.blockSignals(True)
            self.legato_glide_btn.setChecked(bool(value))
            self.legato_glide_btn.setText("On" if value else "Off")
            self.legato_glide_btn.blockSignals(False)
        
        # Tap-Tempo Clock Division Persistence (param 54)
        elif param_id == 54 and hasattr(self, 'ttcdp_btn'):
            self.ttcdp_btn.blockSignals(True)
            self.ttcdp_btn.setChecked(bool(value))
            self.ttcdp_btn.setText("On" if value else "Off")
            self.ttcdp_btn.blockSignals(False)
        
        # Glide Type (param 40)
        elif param_id == 40 and hasattr(self, 'glide_type_buttons'):
            for i, btn in enumerate(self.glide_type_buttons):
                btn.blockSignals(True)
                btn.setChecked(i == value)
                btn.blockSignals(False)
        
        # Note Priority (param 3)
        elif param_id == 3 and hasattr(self, 'np_buttons'):
            # Reverse lookup: find button index from value
            try:
                idx = self.np_value_map.index(value)
                for i, btn in enumerate(self.np_buttons):
                    btn.blockSignals(True)
                    btn.setChecked(i == idx)
                    btn.blockSignals(False)
            except (ValueError, AttributeError):
                pass
        
        # LFO Polarity (param 70)
        elif param_id == 70 and hasattr(self, 'lfo_buttons'):
            for i, btn in enumerate(self.lfo_buttons):
                btn.blockSignals(True)
                btn.setChecked(i == value)
                btn.blockSignals(False)
        
        # Pitch Bend Range (param 37)
        elif param_id == 37 and hasattr(self, 'pbr_slider'):
            self.pbr_slider.blockSignals(True)
            self.pbr_slider.setValue(value)
            self.pbr_value_label.setText(str(value))
            self.pbr_slider.blockSignals(False)
        
        # Pitch Variance (param 58)
        elif param_id == 58 and hasattr(self, 'pv_slider'):
            # Value comes in as 0-400, slider is 0-40
            slider_value = value // 10
            self.pv_slider.blockSignals(True)
            self.pv_slider.setValue(slider_value)
            self.pv_value_label.setText(f"{slider_value} cents")
            self.pv_slider.blockSignals(False)
        
        # Noise Filter Cutoff (param 71)
        elif param_id == 71 and hasattr(self, 'nfc_slider'):
            self.nfc_slider.blockSignals(True)
            self.nfc_slider.setValue(value)
            self.nfc_value_label.setText(str(value))
            self.nfc_slider.blockSignals(False)

        # Glide Time (param 105)
        elif param_id == 105 and hasattr(self, 'gt_slider'):
            self.gt_slider.blockSignals(True)
            self.gt_slider.setValue(value)
            self.gt_value_label.setText(str(value))
            self.gt_slider.blockSignals(False)
            
            # If value is 0, turn off Glide button
            if value == 0 and hasattr(self, 'glide_btn'):
                self.glide_btn.blockSignals(True)
                self.glide_btn.setChecked(False)
                self.glide_btn.setText("Off")
                self.glide_btn.blockSignals(False)

        # Arp/Seq Controls
        elif param_id == 173:  # Arp Play
            self.play_btn.blockSignals(True)
            self.play_btn.setChecked(bool(value))
            self.play_btn.blockSignals(False)
        elif param_id == 169:  # Arp Latch (Hold)
            self.hold_btn.blockSignals(True)
            self.hold_btn.setChecked(bool(value))
            self.hold_btn.blockSignals(False)

class ArpRateWidget(ParameterWidget):
    """Custom widget for Arp Rate with BPM display"""
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(2)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Value display
        self.value_label = QLabel("120 BPM")
        self.value_label.setStyleSheet("font-weight: bold; color: #4a4a2a; font-size: 14px;")
        self.value_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.value_label)
        
        # Slider
        self.slider = QSlider(Qt.Vertical)
        self.slider.setMinimum(0)
        self.slider.setMaximum(16383)
        self.slider.setValue(8192)
        self.slider.setMinimumHeight(80)
        self.slider.valueChanged.connect(self.on_slider_changed)
        layout.addWidget(self.slider, alignment=Qt.AlignCenter)
        
        self.update_display()
    
    def update_display(self):
        """Update the BPM display"""
        # TODO: Convert value to BPM (20-280 range)
        # For now, simple mapping
        bpm = int(20 + (self.current_value / 16383.0) * 260)
        self.value_label.setText(f"{bpm} BPM")
    
    def on_slider_changed(self, value: int):
        """Handle slider changes"""
        self.emit_value_changed(value)
        self.current_value = value
        self.update_display()

class ArpRateKnobWidget(ParameterWidget):
    """Custom knob widget for Arp Rate with BPM display"""
    
    def init_ui(self):
        from PyQt5.QtWidgets import QDial
        
        layout = QVBoxLayout(self)
        layout.setSpacing(5)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Label
        label = QLabel("Rate")
        label.setStyleSheet("font-weight: bold; color: black; font-size: 12px;")
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)
        
        # Knob (QDial) with custom mouse tracking
        self.dial = SmoothDial()
        self.dial.setMinimum(0)
        self.dial.setMaximum(16383)
        self.dial.setValue(8192)
        self.dial.setNotchesVisible(True)
        self.dial.setFixedSize(80, 80)
        self.dial.setStyleSheet("""
            QDial {
                background-color: #2a2a2a;
                border-radius: 40px;
            }
        """)
        self.dial.valueChanged.connect(self.on_dial_changed)
        layout.addWidget(self.dial, alignment=Qt.AlignCenter)
        
        # Value display
        self.value_label = QLabel("120 BPM")
        self.value_label.setStyleSheet("font-weight: bold; color: black; font-size: 13px;")
        self.value_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.value_label)
        
        self.update_display()
    
    def update_display(self):
        """Update the BPM display"""
        # Convert value to BPM (20-280 range)
        bpm = int(20 + (self.current_value / 16383.0) * 260)
        self.value_label.setText(f"{bpm} BPM")
    
    def on_dial_changed(self, value: int):
        """Handle dial changes"""
        self.emit_value_changed(value)
        self.current_value = value
        self.update_display()


class SmoothDial(QDial):
    """QDial subclass with smooth drag behavior (no jumping)"""
    
    double_clicked = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.last_mouse_y = 0
        self.is_dragging = False
    
    def mousePressEvent(self, event):
        """Start dragging without jumping"""
        self.last_mouse_y = event.y()
        self.is_dragging = True
        event.accept()
        # Don't call super() to prevent jumping
    
    def mouseMoveEvent(self, event):
        """Handle smooth dragging"""
        if self.is_dragging:
            delta_y = self.last_mouse_y - event.y()
            self.last_mouse_y = event.y()
            
            # Calculate new value based on mouse movement
            range_size = self.maximum() - self.minimum()
            sensitivity = range_size / 400.0  # Reduced from 200.0 to make it slower
            new_value = self.value() + int(delta_y * sensitivity)
            
            # Clamp to valid range
            new_value = max(self.minimum(), min(self.maximum(), new_value))
            self.setValue(new_value)
            event.accept()
    
    def mouseReleaseEvent(self, event):
        """Stop dragging"""
        self.is_dragging = False
        event.accept()
        # Don't call super() to prevent any jump on release
    
    def wheelEvent(self, event):
        """Handle mouse wheel for fine adjustment"""
        delta = event.angleDelta().y()
        step = (self.maximum() - self.minimum()) // 100
        new_value = self.value() + (step if delta > 0 else -step)
        new_value = max(self.minimum(), min(self.maximum(), new_value))
        self.setValue(new_value)
        event.accept()
        
    def mouseDoubleClickEvent(self, event):
        """Handle double-click to reset to default"""
        self.double_clicked.emit()
        event.accept()

class CustomButtonGroup(ParameterWidget):
    """Button group with custom styling"""
    
    def __init__(self, parameter: Parameter, selected_color: str = "#6B8E23", parent=None):
        self.selected_color = selected_color
        super().__init__(parameter, parent)
    
    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setSpacing(2)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.buttons = {}
        for value, text in sorted(self.parameter.choices.items()):
            button = QPushButton(text)
            button.setCheckable(True)
            button.setMinimumHeight(30)
            button.clicked.connect(lambda checked, v=value: self.on_button_clicked(v))
            
            self.buttons[value] = button
            layout.addWidget(button)
        
        self.update_display()
    
    def update_display(self):
        """Update button states"""
        for value, button in self.buttons.items():
            button.blockSignals(True)
            button.setChecked(value == self.current_value)
            
            if button.isChecked():
                button.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {self.selected_color};
                        border: 2px solid #556B2F;
                        color: white;
                        font-weight: bold;
                    }}
                """)
            else:
                button.setStyleSheet("""
                    QPushButton {
                        background-color: #999999;
                        border: 1px solid #666666;
                        color: white;
                    }
                    QPushButton:hover {
                        background-color: #aaaaaa;
                    }
                """)
            button.blockSignals(False)
    
    def on_button_clicked(self, value: int):
        """Handle button click"""
        self.emit_value_changed(value)


class ToggleButton(ParameterWidget):
    """Simple toggle button"""
    
    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.button = QPushButton(self.parameter.name)
        self.button.setCheckable(True)
        self.button.setMinimumHeight(30)
        self.button.clicked.connect(self.on_clicked)
        layout.addWidget(self.button)
        
        self.update_display()
    
    def update_display(self):
        """Update button state"""
        self.button.blockSignals(True)
        self.button.setChecked(bool(self.current_value))
        
        if self.button.isChecked():
            self.button.setStyleSheet("""
                QPushButton {
                    background-color: #6B8E23;
                    border: 2px solid #556B2F;
                    color: white;
                    font-weight: bold;
                }
            """)
        else:
            self.button.setStyleSheet("""
                QPushButton {
                    background-color: #999999;
                    border: 1px solid #666666;
                    color: white;
                }
            """)
        self.button.blockSignals(False)
    
    def on_clicked(self):
        """Handle button click"""
        value = 1 if self.button.isChecked() else 0
        self.emit_value_changed(value)
        
        
class ParameterSliderWidget(ParameterWidget):
    """Horizontal slider for parameters with optional value conversion"""
    
    def __init__(self, parameter: Parameter, convert_display=None, parent=None):
        self.convert_display = convert_display  # Optional function to convert value for display
        self.slider = None
        self.value_label = None
        super().__init__(parameter, parent)
    
    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setSpacing(5)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create slider
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(self.parameter.min_value)
        self.slider.setMaximum(self.parameter.max_value)
        self.slider.setValue(self.parameter.default_value)
        self.slider.setStyleSheet("""
            QSlider::groove:horizontal {
                background: #2a2a2a;
                height: 8px;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #666;
                width: 16px;
                margin: -4px 0;
                border-radius: 8px;
            }
            QSlider::handle:horizontal:hover {
                background: #888;
            }
        """)
        self.slider.valueChanged.connect(self.on_slider_changed)
        self.slider.installEventFilter(self)
        
        # Create value label
        self.value_label = QLabel()
        self.value_label.setStyleSheet("color: white; min-width: 70px;")
        self.value_label.setAlignment(Qt.AlignCenter)
        
        layout.addWidget(self.slider, 1)
        layout.addWidget(self.value_label)
        
        self.update_display()
    
    def update_display(self):
        """Update the value label"""
        if self.convert_display:
            display_text = self.convert_display(self.current_value)
        else:
            display_text = str(self.current_value)
        self.value_label.setText(display_text)
    
    def on_slider_changed(self, value: int):
        """Handle slider value changes"""
        self.emit_value_changed(value)
        self.current_value = value
        self.update_display()

    def eventFilter(self, obj, event):
        """Event filter to catch double-clicks on slider"""
        if obj == self.slider and event.type() == event.MouseButtonDblClick:
            self.reset_to_default()
            return True
        return super().eventFilter(obj, event)
    
    def reset_to_default(self):
        """Reset slider to parameter's default value"""
        default_value = self.parameter.default_value
        # Don't call setValue - it triggers valueChanged
        # Instead, set directly and emit once
        self.slider.blockSignals(True)
        self.slider.setValue(default_value)
        self.slider.blockSignals(False)
        self.current_value = default_value
        self.update_display()
        self.emit_value_changed(default_value)

class ParameterDialWidget(ParameterWidget):
    """Dial/knob widget for parameters with optional value conversion"""
    
    def __init__(self, parameter: Parameter, convert_display=None, parent=None):
        self.convert_display = convert_display  # Optional function to convert value for display
        self.dial = None
        self.value_label = None
        super().__init__(parameter, parent)
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(2)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Label
        label = QLabel(self.parameter.name)
        label.setStyleSheet("font-weight: bold; color: black; font-size: 11px;")
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)
        
        # Dial
        self.dial = SmoothDial()
        self.dial.setMinimum(self.parameter.min_value)
        self.dial.setMaximum(self.parameter.max_value)
        self.dial.setValue(self.parameter.default_value)
        self.dial.setNotchesVisible(True)
        self.dial.setFixedSize(70, 70)
        self.dial.setStyleSheet("""
            QDial {
                background-color: #2a2a2a;
                border-radius: 35px;
            }
        """)
        self.dial.valueChanged.connect(self.on_dial_changed)
        self.dial.double_clicked.connect(self.reset_to_default)
        layout.addWidget(self.dial, alignment=Qt.AlignCenter)
        
        # Value display
        self.value_label = QLabel()
        self.value_label.setStyleSheet("font-weight: bold; color: black; font-size: 11px;")
        self.value_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.value_label)
        
        self.update_display()
    
    def update_display(self):
        """Update the value display"""
        if self.convert_display:
            display_text = self.convert_display(self.current_value)
        else:
            display_text = str(self.current_value)
        self.value_label.setText(display_text)
    
    def on_dial_changed(self, value: int):
        """Handle dial changes"""
        self.emit_value_changed(value)
        self.current_value = value
        self.update_display()
    
    def reset_to_default(self):
        """Reset dial to parameter's default value"""
        default_value = self.parameter.default_value
        self.dial.setValue(default_value)
        self.current_value = default_value
        self.emit_value_changed(default_value)
        self.update_display()

class ParameterToggleWidget(ParameterWidget):
    """Toggle button for on/off parameters"""
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.button = QPushButton("Off")
        self.button.setCheckable(True)
        self.button.clicked.connect(self.on_clicked)
        layout.addWidget(self.button)
        
        self.update_display()
    
    def update_display(self):
        """Update button state and text"""
        self.button.blockSignals(True)
        is_on = bool(self.current_value)
        self.button.setChecked(is_on)
        self.button.setText("On" if is_on else "Off")
        self.button.blockSignals(False)
    
    def on_clicked(self):
        """Handle button click"""
        value = 1 if self.button.isChecked() else 0
        self.emit_value_changed(value)


class ParameterButtonGroupWidget(ParameterWidget):
    """Button group for parameters with multiple choice values"""
    
    def __init__(self, parameter: Parameter, value_map: dict = None, parent=None):
        """
        value_map: dict mapping button index to parameter value
        Example: {0: 0, 1: 1, 2: 2} or {0: 15, 1: 47, 2: 79, 3: 111}
        """
        self.value_map = value_map or {}
        self.buttons = []
        super().__init__(parameter, parent)
    
    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setSpacing(2)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create buttons based on parameter choices or value_map
        if self.parameter.choices:
            # Use parameter choices
            for value, text in sorted(self.parameter.choices.items()):
                button = self.create_button(text)
                self.buttons.append((button, value))
                layout.addWidget(button)
        elif self.value_map:
            # Use value map (for cases like octave buttons)
            for idx, param_value in sorted(self.value_map.items()):
                button = self.create_button(str(idx))
                self.buttons.append((button, param_value))
                layout.addWidget(button)
        
        self.update_display()
    
    def create_button(self, text: str) -> QPushButton:
        """Create a styled button"""
        button = QPushButton(text)
        button.setCheckable(True)
        button.setMinimumHeight(30)
        button.clicked.connect(lambda: self.on_button_clicked(button))
        return button
    
    def update_display(self):
        """Update button states"""
        for button, value in self.buttons:
            button.blockSignals(True)
            button.setChecked(value == self.current_value)
            button.blockSignals(False)
    
    def on_button_clicked(self, clicked_button: QPushButton):
        """Handle button click - make mutually exclusive"""
        # Find the value for clicked button
        for button, value in self.buttons:
            if button == clicked_button:
                if not button.isChecked():
                    button.setChecked(True)  # Can't uncheck
                else:
                    # Uncheck all others
                    for other_button, _ in self.buttons:
                        if other_button != button:
                            other_button.setChecked(False)
                    self.emit_value_changed(value)
                break