import sys
import os
import importlib.util
import logging
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)

# Constants
PLUGIN_FILE_NAME = "plugin.py"
DEV_PLUGIN_DIR_NAME = "plugins_dev"
PROD_PLUGIN_DIR_NAME = "plugins"

def get_base_path() -> Path:
    """
    Determine the base path of the application.
    Handles PyInstaller's sys._MEIPASS logic.
    """
    if getattr(sys, 'frozen', False):
        # Running as compiled EXE
        # For plugins adjacent to EXE, we use sys.executable dir
        # For plugins embedded (if any), we'd use sys._MEIPASS
        # Strategy: Look for 'plugins' folder next to EXE
        return Path(sys.executable).parent
    else:
        # Running as source
        # Base path is the project root (assuming run.py is at root)
        return Path(os.path.abspath("."))

def get_plugin_paths() -> List[Path]:
    """
    Return a list of directories to scan for plugins based on environment.
    """
    paths = []
    base_path = get_base_path()
    
    
    # 1. Check for Prod Plugins folder (dist/plugins) - External User Plugins
    prod_plugins = base_path / PROD_PLUGIN_DIR_NAME
    if prod_plugins.exists() and prod_plugins.is_dir():
        paths.append(prod_plugins)
        
    # 2. Check for Bundled Plugins (PyInstaller _MEIPASS)
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        bundled_plugins = Path(sys._MEIPASS) / "docnexus" / DEV_PLUGIN_DIR_NAME
        if bundled_plugins.exists() and bundled_plugins.is_dir():
            paths.append(bundled_plugins)

    # 3. Check for Dev Plugins folder (Source mode)
    # Note: In source, 'docnexus' is usually a subdir of CWD
    dev_plugins = base_path / "docnexus" / DEV_PLUGIN_DIR_NAME
    if dev_plugins.exists() and dev_plugins.is_dir():
        paths.append(dev_plugins)

    # 4. Check for Internal Prod Plugins (docnexus/plugins)
    internal_plugins = base_path / "docnexus" / PROD_PLUGIN_DIR_NAME
    if internal_plugins.exists() and internal_plugins.is_dir():
         paths.append(internal_plugins)
        
    logger.debug(f"Plugin scan paths: {[str(p) for p in paths]}")
    return paths

def load_plugins_from_path(plugin_dir: Path, registry_instance=None) -> None:
    """
    Scan a specific directory for plugins and load them.
    Expects structure: plugin_dir/my_plugin/plugin.py
    """
    if not plugin_dir.exists():
        logger.warning(f"Plugin directory not found: {plugin_dir}")
        return

    logger.info(f"Scanning for plugins in: {plugin_dir}")

    # Iterate over subdirectories
    count = 0
    for item in plugin_dir.iterdir():
        # debug_log(f"Scanning item: {item}")
        if item.is_dir():
            plugin_path = item / PLUGIN_FILE_NAME
            # debug_log(f"Checking for {plugin_path}")
            if plugin_path.exists():
                logger.error(f"DEBUG: Found plugin at {plugin_path}")
                load_single_plugin(item.name, plugin_path, registry_instance)
                count += 1
            else:
                 pass
    logger.error(f"DEBUG: Scanned {plugin_dir}, found {count} plugins.")

def load_single_plugin(name: str, path: Path, registry_instance=None) -> None:
    """
    Loads a single plugin from a path, injecting dependencies to ensure
    it shares the same registry and class definitions as the core app.
    """
    try:
        logger.info(f"Loading plugin '{name}' from {path}")
        
        # Use a unique name for the module based on file path to avoid conflicts
        module_name = f"docnexus_plugin_{name}"
        spec = importlib.util.spec_from_file_location(module_name, str(path))
        
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            
            # --------------------------------------------------------------------
            # DEPENDENCY INJECTION TO FIX SPLIT-BRAIN & IMPORT ERRORS
            # --------------------------------------------------------------------
            from docnexus.features.registry import Feature, FeatureType, FeatureState, PluginRegistry
            
            # Determine correct registry instance
            # If injected from app, use it. Otherwise fall back to Singleton (riskier but supported).
            actual_registry = registry_instance if registry_instance else PluginRegistry()
            
            # Inject classes directly into module namespace
            module.Feature = Feature
            module.FeatureType = FeatureType
            module.FeatureState = FeatureState
            
            # Mock PluginRegistry constructor to return our instance
            module.PluginRegistry = lambda: actual_registry
            # --------------------------------------------------------------------
            
            # Execute module
            spec.loader.exec_module(module)
            logger.info(f"Successfully executed module: {name}")

            # Verify and Register Features
            if hasattr(module, 'get_features'):
                features = module.get_features()
                if not features:
                    logger.warning(f"Plugin {name} returned no features.")
                else:
                    count = 0
                    for f in features:
                        try:
                            actual_registry.register(f)
                            logger.info(f"Loader: Registered feature '{f.name}' (Type: {f.type}) from {name}")
                            count += 1
                        except Exception as reg_err:
                            logger.error(f"Loader: Failed to register feature {f.name} from {name}: {reg_err}")
                    
                    if count > 0:
                        logger.info(f"Loader: Successfully registered {count} features from {name}")
            else:
                logger.info(f"Loader: No get_features() found in {name}")
                
    except Exception as e:
        logger.error(f"Failed to load plugin '{name}': {e}", exc_info=True)

def load_plugins(registry_instance=None) -> None:
    """
    Main entry point to discover and load all available plugins.
    """
    search_paths = get_plugin_paths()
    logger.error(f"DEBUG: Loader search paths: {[str(p) for p in search_paths]}")
    
    for path in search_paths:
        if path.exists():
            logger.error(f"DEBUG: Scanning path: {path}")
            load_plugins_from_path(path, registry_instance)
        else:
             logger.error(f"DEBUG: Search path does not exist: {path}")
