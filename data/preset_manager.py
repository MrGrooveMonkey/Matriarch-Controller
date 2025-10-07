"""
Preset management for Matriarch Controller.
Handles saving/loading presets and managing preset directories.
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, List


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
            
            # Filter out excluded parameters (76 and 100+) and add parameter names
            filtered_params = {}
            for param_id, value in parameters.items():
                if param_id not in self.EXCLUDED_PARAMS and param_id < 100:
                    param_name = PARAMETERS[param_id].name if param_id in PARAMETERS else f"Parameter {param_id}"
                    filtered_params[str(param_id)] = {
                        "name": param_name,
                        "value": value
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
            Dictionary with 'parameters' and 'metadata', or None if error
        """
        try:
            with open(filepath, 'r') as f:
                preset_data = json.load(f)
            
            # Validate structure
            if not isinstance(preset_data, dict):
                raise ValueError("Invalid preset format: root must be an object")
            
            if "parameters" not in preset_data:
                raise ValueError("Invalid preset format: missing 'parameters'")
            
            # Convert parameter IDs back to integers
            parameters = {}
            for param_id_str, param_data in preset_data["parameters"].items():
                try:
                    param_id = int(param_id_str)
                    # Handle both old format (direct value) and new format (dict with name and value)
                    if isinstance(param_data, dict):
                        value = param_data.get("value")
                    else:
                        value = param_data  # Old format compatibility
                    
                    if value is not None:
                        parameters[param_id] = value
                except (ValueError, TypeError) as e:
                    print(f"Warning: Invalid parameter data for ID '{param_id_str}': {e}")
            
            return {
                "parameters": parameters,
                "metadata": preset_data.get("metadata", {})
            }
            
        except (IOError, OSError) as e:
            print(f"Error loading preset file: {e}")
            return None
        except (json.JSONDecodeError, ValueError) as e:
            print(f"Error parsing preset: {e}")
            return None
    
    def validate_preset_parameters(self, parameters: Dict[int, int]) -> Dict:
        """
        Validate preset parameters against expected range (0-75, excluding 76)
        
        Args:
            parameters: Dictionary of parameter_id: value from preset
            
        Returns:
            Dictionary with 'valid', 'missing', 'extra' keys
        """
        expected_params = set(range(76)) - set(self.EXCLUDED_PARAMS)
        loaded_params = set(parameters.keys())
        
        missing = expected_params - loaded_params
        extra = loaded_params - expected_params - set(range(100, 200))  # Exclude 100+ range
        
        return {
            "valid": loaded_params & expected_params,
            "missing": sorted(missing),
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