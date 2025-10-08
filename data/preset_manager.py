"""
Preset management for Matriarch Controller.
Handles saving/loading presets and managing preset directories.
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, List, Set

def get_preset_parameter_ids() -> Dict[str, set]:
    """
    Get parameter IDs that should be included in presets, categorized by type.
    
    Returns:
        Dict with 'sysex', 'cc_active', 'cc_inactive' keys containing sets of param IDs
    """
    from data.parameter_definitions import PARAMETERS
    
    # Parameters to exclude completely
    EXCLUDED = {76}  # Load Default Settings
    
    # CC parameters that are defined but currently inactive in UI
    INACTIVE_CC = {103, 191, 192, 193}  # Mod Rate, Arp Mode, Pattern, Range/Bank
    
    sysex_params = set()
    cc_active = set()
    cc_inactive = set()
    
    for param_id in PARAMETERS.keys():
        if param_id in EXCLUDED:
            continue
            
        # SysEx parameters (0-75)
        if 0 <= param_id <= 75:
            sysex_params.add(param_id)
        # CC parameters (101+, below 300 to exclude Program Change)
        elif 101 <= param_id < 300:
            if param_id in INACTIVE_CC:
                cc_inactive.add(param_id)
            else:
                cc_active.add(param_id)
    
    return {
        'sysex': sysex_params,
        'cc_active': cc_active,
        'cc_inactive': cc_inactive
    }

class PresetManager:
    """Manages preset file operations and directory structure"""
    
    PRESETS_DIR = "Presets"
    PRESET_EXTENSION = ".matpatch"
    
    # Default subdirectories
    DEFAULT_SUBDIRS = [
        "Ambient",
        "Bass",
        "Keys",
        "Lead",
        "Pad",
        "Experimental",
        "Other"
    ]
    
    # Parameters to exclude from presets
    EXCLUDED_PARAMS = [76]  # Load Default Settings parameter
    
    def __init__(self, app_version: str):
        """
        Initialize PresetManager
        
        Args:
            app_version: Current application version string
        """
        self.app_version = app_version
        self.presets_path = Path(__file__).parent.parent / self.PRESETS_DIR
        self._ensure_preset_directories()
    
    def _ensure_preset_directories(self):
        """Create preset directory structure if it doesn't exist"""
        # Create main Presets directory
        self.presets_path.mkdir(exist_ok=True)
        
        # Create default subdirectories
        for subdir in self.DEFAULT_SUBDIRS:
            (self.presets_path / subdir).mkdir(exist_ok=True)
    
    def get_presets_directory(self) -> str:
        """Get the full path to the Presets directory"""
        return str(self.presets_path)
    
    def save_preset(self, filepath: str, parameters: Dict[int, int]) -> bool:
        """
        Save preset to JSON file
        
        Args:
            filepath: Full path where to save the preset
            parameters: Dictionary of parameter_id: value
            
        Returns:
            True if successful, False otherwise
        """
        try:
            from data.parameter_definitions import PARAMETERS
            
            # Get categorized parameter IDs
            param_categories = get_preset_parameter_ids()
            
            # Build parameters dict with names and types
            filtered_params = {}
            
            for param_id, value in parameters.items():
                # Determine parameter type
                param_type = None
                if param_id in param_categories['sysex']:
                    param_type = 'sysex'
                elif param_id in param_categories['cc_active']:
                    param_type = 'cc'
                elif param_id in param_categories['cc_inactive']:
                    param_type = 'cc_inactive'
                
                # Only include if it's a valid preset parameter
                if param_type:
                    param_name = PARAMETERS[param_id].name if param_id in PARAMETERS else f"Parameter {param_id}"
                    filtered_params[str(param_id)] = {
                        "name": param_name,
                        "value": value,
                        "type": param_type
                    }
            
            # Create preset structure
            preset_data = {
                "metadata": {
                    "saved_date": datetime.now().isoformat(),
                    "app_version": self.app_version
                },
                "parameters": filtered_params
            }
            
            # Ensure filepath has correct extension
            if not filepath.endswith(self.PRESET_EXTENSION):
                filepath += self.PRESET_EXTENSION
            
            # Write to file
            with open(filepath, 'w') as f:
                json.dump(preset_data, f, indent=2)
            
            return True
            
        except (IOError, OSError) as e:
            print(f"Error saving preset: {e}")
            return False
    
    def load_preset(self, filepath: str) -> Optional[Dict]:
        """
        Load preset from JSON file
        
        Args:
            filepath: Full path to preset file
            
        Returns:
            Dictionary with 'parameters', 'metadata', and 'parameter_types', or None if error
        """
        try:
            with open(filepath, 'r') as f:
                preset_data = json.load(f)
            
            # Validate structure
            if not isinstance(preset_data, dict):
                raise ValueError("Invalid preset format: root must be an object")
            
            if "parameters" not in preset_data:
                raise ValueError("Invalid preset format: missing 'parameters'")
            
            # Convert parameter IDs back to integers and extract types
            parameters = {}
            parameter_types = {}
            
            for param_id_str, param_data in preset_data["parameters"].items():
                try:
                    param_id = int(param_id_str)
                    
                    # Handle both old format (direct value) and new format (dict with name, value, type)
                    if isinstance(param_data, dict):
                        value = param_data.get("value")
                        param_type = param_data.get("type", "sysex")  # Default to sysex for old presets
                    else:
                        # Old format compatibility
                        value = param_data
                        param_type = "sysex" if param_id <= 75 else "cc"
                    
                    if value is not None:
                        parameters[param_id] = value
                        parameter_types[param_id] = param_type
                        
                except (ValueError, TypeError) as e:
                    print(f"Warning: Invalid parameter data for ID '{param_id_str}': {e}")
            
            return {
                "parameters": parameters,
                "metadata": preset_data.get("metadata", {}),
                "parameter_types": parameter_types
            }
            
        except (IOError, OSError) as e:
            print(f"Error loading preset file: {e}")
            return None
        except (json.JSONDecodeError, ValueError) as e:
            print(f"Error parsing preset: {e}")
            return None
    
    def validate_preset_parameters(self, parameters: Dict[int, int], parameter_types: Dict[int, str] = None) -> Dict:
        """
        Validate preset parameters against expected parameters.
        
        Args:
            parameters: Dictionary of parameter_id: value from preset
            parameter_types: Dictionary of parameter_id: type (optional)
            
        Returns:
            Dictionary with 'valid', 'missing_sysex', 'missing_cc', 'extra' keys
        """
        param_categories = get_preset_parameter_ids()
        
        # All expected parameters (SysEx + CC active + CC inactive)
        all_expected = param_categories['sysex'] | param_categories['cc_active'] | param_categories['cc_inactive']
        loaded_params = set(parameters.keys())
        
        # Separate missing parameters by type
        missing_sysex = param_categories['sysex'] - loaded_params
        missing_cc = (param_categories['cc_active'] | param_categories['cc_inactive']) - loaded_params
        
        # Extra parameters (not in our expected list)
        extra = loaded_params - all_expected
        
        # Valid parameters
        valid = loaded_params & all_expected
        
        return {
            "valid": valid,
            "missing_sysex": sorted(missing_sysex),
            "missing_cc": sorted(missing_cc),
            "extra": sorted(extra)
        }
    
    def get_preset_display_name(self, filepath: str) -> str:
        """
        Get display name for preset (filename + parent folder)
        
        Args:
            filepath: Full path to preset file
            
        Returns:
            Display string like "WarmPad.matpatch (Bass/)"
        """
        path = Path(filepath)
        filename = path.name
        parent = path.parent.name
        
        # If parent is the main Presets directory, don't show it
        if parent == self.PRESETS_DIR:
            return filename
        else:
            return f"{filename} ({parent}/)"