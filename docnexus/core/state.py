
import json
import logging
from pathlib import Path
import sys

logger = logging.getLogger(__name__)

class PluginState:
    _instance = None
    
    def __init__(self):
        # Determine config location (next to executable or in root)
        if getattr(sys, 'frozen', False):
             self.config_path = Path(sys.executable).parent / "plugins.json"
        else:
             self.config_path = Path("plugins.json").resolve()
             
        self._ensure_config()
        PluginState._instance = self # Set the instance after successful initialization

    @staticmethod
    def get_instance():
        if PluginState._instance is None:
            PluginState._instance = PluginState() # This will call __init__ and set _instance
            logger.info(f"PluginState: Created NEW instance {id(PluginState._instance)}")
        else:
            logger.debug(f"PluginState: Returning existing instance {id(PluginState._instance)}")
        return PluginState._instance

    def _ensure_config(self):
        """Create empty config if missing."""
        if not self.config_path.exists():
            try:
                with open(self.config_path, 'w') as f:
                    json.dump({"installed": []}, f)
            except Exception as e:
                logger.error(f"Failed to init plugins.json: {e}")

    def get_installed_plugins(self):
        """Return list of installed plugin IDs."""
        try:
            if not self.config_path.exists():
                return []
            with open(self.config_path, 'r') as f:
                data = json.load(f)
                return data.get("installed", [])
        except Exception as e:
            logger.error(f"Error reading plugin state: {e}")
            return []

    def is_plugin_installed(self, plugin_id):
        return plugin_id in self.get_installed_plugins()

    def is_plugin_in_registry(self, plugin_id):
        # In current design, registry tracking (persistence) IS the installed list
        # We don't track "known but uninstalled" in this simple JSON.
        # But loader uses this to decide whether to peek metadata or skip.
        # If it's in the list, we treat it as "known and installed".
        return plugin_id in self.get_installed_plugins()
    
    def set_plugin_installed(self, plugin_id, installed):
        """Update installation status."""
        try:
            current = list(self.get_installed_plugins())
            if installed:
                if plugin_id not in current:
                    current.append(plugin_id)
            else:
                if plugin_id in current:
                    current.remove(plugin_id)
            
            with open(self.config_path, 'w') as f:
                json.dump({"installed": current}, f, indent=4)
            return True
        except Exception as e:
            logger.error(f"Error saving plugin state: {e}")
            return False
