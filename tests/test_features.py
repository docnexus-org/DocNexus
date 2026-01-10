import unittest
import sys
from unittest.mock import MagicMock
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from docnexus.features.registry import FeatureManager, Feature, FeatureState, FeatureType, Pipeline

class TestFeatures(unittest.TestCase):
    def setUp(self):
        self.manager = FeatureManager()

    def test_pipeline_execution(self):
        """Test that a pipeline executes steps in order."""
        pipeline = Pipeline("TestPipeline")
        
        def step1(content): return content + " Step1"
        def step2(content): return content + " Step2"
        
        pipeline.add_step(step1)
        pipeline.add_step(step2)
        
        result = pipeline.run("Start")
        self.assertEqual(result, "Start Step1 Step2")

    def test_feature_manager_refresh(self):
        """Test that FeatureManager pulls algorithms from registry."""
        mock_registry = MagicMock()
        
        # Create a mock plugin that acts as a Feature (Duck Typing)
        mock_plugin = MagicMock()
        mock_plugin.name = "TEST_ALGO"
        mock_plugin.type = FeatureType.ALGORITHM
        mock_plugin.state = FeatureState.STANDARD
        mock_plugin.handler = lambda x: x
        
        mock_registry.get_all_plugins.return_value = [mock_plugin]
        
        self.manager._registry = mock_registry
        self.manager.refresh()
        
        features = self.manager._features
        self.assertEqual(len(features), 1)
        self.assertEqual(features[0].name, "TEST_ALGO")

    def test_build_pipeline(self):
        """Test building a pipeline from registered features."""
        f1 = Feature("F1", lambda x: "1", FeatureState.STANDARD, FeatureType.ALGORITHM)
        f2 = Feature("F2", lambda x: "2", FeatureState.EXPERIMENTAL, FeatureType.ALGORITHM)
        f3 = Feature("UI", lambda x: "UI", FeatureState.STANDARD, FeatureType.UI_EXTENSION)
        
        self.manager.register(f1)
        self.manager.register(f2)
        self.manager.register(f3)
        
        # Standard only
        p_std = self.manager.build_pipeline(enable_experimental=False)
        self.assertEqual(len(p_std._steps), 1) # Only F1
        
        # With experimental
        p_exp = self.manager.build_pipeline(enable_experimental=True)
        self.assertEqual(len(p_exp._steps), 2) # F1 + F2

if __name__ == '__main__':
    unittest.main()
