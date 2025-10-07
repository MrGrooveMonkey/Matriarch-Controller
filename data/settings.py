"""
Application settings management for Matriarch Controller.
Handles persistent storage of app settings like recent presets.
"""

import json
import os
from typing import List
from pathlib import Path


class AppSettings:
    """Manages application settings stored in settings.json"""
    
    SETTINGS_FILE = "settings.json"
    MAX_RECENT_PRESETS = 10
    
    def __init__(self):
        self.settings_path = Path(__file__).parent.parent / self.SETTINGS_FILE
        self.settings = self._load_settings()
    
    def _load_settings(self) -> dict:
        """Load settings from JSON file, or create default if not exists"""
        if self.settings_path.exists():
            try:
                with open(self.settings_path, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading settings: {e}. Using defaults.")
                return self._default_settings()
        else:
            return self._default_settings()
    
    def _default_settings(self) -> dict:
        """Return default settings structure"""
        return {
            "recent_presets": []
        }
    
    def _save_settings(self):
        """Save current settings to JSON file"""
        try:
            with open(self.settings_path, 'w') as f:
                json.dump(self.settings, f, indent=2)
        except IOError as e:
            print(f"Error saving settings: {e}")
    
    def get_recent_presets(self) -> List[str]:
        """Get list of recent preset file paths"""
        return self.settings.get("recent_presets", [])
    
    def add_recent_preset(self, preset_path: str):
        """
        Add preset path to recent list.
        Moves to top if already exists, maintains max size.
        
        Args:
            preset_path: Full path to preset file
        """
        recent = self.settings.get("recent_presets", [])
        
        # Remove if already in list
        if preset_path in recent:
            recent.remove(preset_path)
        
        # Add to beginning
        recent.insert(0, preset_path)
        
        # Trim to max size
        self.settings["recent_presets"] = recent[:self.MAX_RECENT_PRESETS]
        
        # Save to disk
        self._save_settings()
    
    def remove_recent_preset(self, preset_path: str):
        """
        Remove preset path from recent list.
        
        Args:
            preset_path: Full path to preset file to remove
        """
        recent = self.settings.get("recent_presets", [])
        if preset_path in recent:
            recent.remove(preset_path)
            self.settings["recent_presets"] = recent
            self._save_settings()
    
    def validate_recent_presets(self):
        """Remove non-existent files from recent presets list"""
        recent = self.settings.get("recent_presets", [])
        valid_presets = [p for p in recent if Path(p).exists()]
        
        if len(valid_presets) != len(recent):
            self.settings["recent_presets"] = valid_presets
            self._save_settings()