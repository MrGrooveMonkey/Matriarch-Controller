# Matriarch Controller

A real-time MIDI controller application for the Moog Matriarch synthesizer, built with Python and PyQt5.

## Features

- Real-time parameter control via MIDI SysEx and CC messages
- Complete global settings management for all 79+ Matriarch parameters
- Preset save/load system with JSON format
- MIDI logging with filtering capabilities
- Cross-platform support (macOS, Windows, Linux)
- Tabbed interface organized by functional categories
- Automatic parameter validation and dependency management

## Requirements

### Python Version
- Python 3.7 or higher

### Required Libraries
Install the following packages using pip:

```bash
pip3 install PyQt5 mido python-rtmidi
```

### System Requirements

#### macOS
- macOS 10.12 or later
- No additional setup required - python-rtmidi uses the built-in CoreMIDI

#### Windows
- Windows 7 or later
- python-rtmidi uses the built-in Windows MIDI API

#### Linux
- ALSA development libraries (usually pre-installed)
- For Ubuntu/Debian: `sudo apt-get install libasound2-dev`

### Hardware Requirements
- Moog Matriarch synthesizer
- MIDI interface (USB or traditional DIN MIDI)
- Properly configured MIDI connections between computer and Matriarch

## Installation

1. Clone or download this repository
2. Install the required Python packages (see above)
3. Connect your Matriarch via MIDI
4. Run the application:

```bash
python3 main.py
```

## MIDI Setup

### Matriarch MIDI Configuration
Ensure your Matriarch has:
- MIDI Input/Output channels set (default Channel 1)
- USB or DIN MIDI connected to your computer
- Power on and functioning normally

### Computer MIDI Setup
- Verify MIDI ports are recognized by your operating system
- On macOS: Check Audio MIDI Setup utility
- On Windows: Check Device Manager under "Sound, video and game controllers"
- On Linux: Use `aconnect -l` to list available MIDI ports

## First Run

1. Launch the application
2. Go to File → MIDI Settings
3. Select your MIDI Input and Output ports
4. Click "Test Connection" to verify communication with Matriarch
5. The app will automatically query all global parameters on successful connection

## Usage Notes

- Parameter changes are sent to the Matriarch immediately
- Use File → Query All Parameters to refresh all settings from the Matriarch
- Presets are saved as JSON files and can be shared between users
- MIDI logging can be enabled via View → MIDI Log Window

## Troubleshooting

### MIDI Connection Issues
- Verify MIDI cables are properly connected
- Check that Matriarch is powered on and responding
- Try different MIDI ports if multiple are available
- On macOS, restart Audio MIDI Setup if ports don't appear

### Application Issues
- Ensure all required Python packages are installed
- Check Python version is 3.7+
- Try running from command line to see error messages

### Performance Issues
- Increase query delay in Settings → MIDI Timing if communication is unreliable
- Close other MIDI applications that might conflict

## Support

This application is designed to work with Matriarch firmware version 1.2.3 and later.
Refer to your Matriarch manual for detailed information about global parameters.

## File Locations

- Presets: Saved in `presets/` directory alongside the application
- Logs: Saved in the same directory as the application
- Settings: Stored in system-appropriate location via Qt settings