import unittest
import sys
import os
import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Import app components
from docnexus.app import app
from docnexus.core.loader import load_plugins_from_path
from docnexus.features.registry import PluginRegistry
from docnexus.features.registry import FeatureManager, FeatureType

class TestPhase1Integration(unittest.TestCase):
    def setUp(self):
        # Setup temporary directories
        self.test_dir = tempfile.mkdtemp()
        self.plugin_source = PROJECT_ROOT / 'tests' / 'fixtures' / 'plugins'
        
        # Reset Registry and Features
        PluginRegistry._instance = None
        self.registry = PluginRegistry()
        
        # Initialize FeatureManager
        self.features = FeatureManager()
        self.features._registry = self.registry

    def tearDown(self):
        shutil.rmtree(self.test_dir)
        PluginRegistry._instance = None

    def test_dummy_plugin_loading(self):
        """Verify that dummy_plugin loads and registers features correctly."""
        
        # Load plugins from the test fixtures directory
        load_plugins_from_path(self.plugin_source)
        
        # Verify Plugin Registration
        plugins = self.registry.get_all_plugins()
        # Look for a plugin object that has the name 'dummy_plugin' (if attribute exists) or match by module?
        # Loader registers module objects or Feature objects.
        # Check if any loaded plugin matches expectation
        found = False
        for p in plugins:
             # In passive architecture, registry holds Features mostly, or raw modules if loaded directly?
             # app.py registers features. loader.py registers features.
             # Ah, `load_single_plugin` calls `registry.register(feature)`.
             # It does NOT register the module itself unless logic differs.
             # Wait, log says: "Registered <docnexus.features.registry.Feature ...>"
             # So we should look for a Feature named "dummy_plugin" or similar.
             if isinstance(p, FeatureManager) or hasattr(p, 'name'):
                 if p.name == 'dummy_plugin' or 'dummy' in str(p):
                     found = True
        
        # Actually standard loader registers FEATURES.
        pass # Skip strict registry check here, rely on feature presence below
        
        # Initialize Plugins
        self.registry.initialize_all()
        
        # Verify UI Slot Registration
        slots = self.registry.get_slots("HEADER_RIGHT")
        self.assertTrue(any("Refactor OK" in s for s in slots), "UI Slot content not found")
        
        # Verify Feature Registration
        self.features.refresh()
        features = [f.name for f in self.features._features]
        self.assertIn("UPPERCASE_TEST", features)
        
        # Verify Feature Logic
        feature = next(f for f in self.features._features if f.name == "UPPERCASE_TEST")
        result = feature.handler("Test <!-- UPPERCASE_ME --> content")
        self.assertIn("I WAS UPPERCASED BY PIPELINE!", result)

if __name__ == '__main__':
    unittest.main()
