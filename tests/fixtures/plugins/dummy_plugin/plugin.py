from docnexus.core.plugin_interface import PluginInterface
from docnexus.features.registry import PluginRegistry
from docnexus.features.registry import Feature, FeatureType, FeatureState
import logging

logger = logging.getLogger(__name__)

class DummyPlugin(PluginInterface):
    def get_meta(self):
        return {
            'name': 'dummy_plugin',
            'version': '0.1.0',
            'description': 'A dummy plugin for verifying the plugin architecture',
            'author': 'Developer'
        }

    def initialize(self):
        registry = PluginRegistry()
        logger.info("DummyPlugin: Initializing...")
        # Register a UI Slot extension
        registry.register_slot(
            "HEADER_RIGHT", 
            '<button class="btn btn-sm btn-outline-success" onclick="alert(\'Plugin System Verified!\')">Refactor OK</button>'
        )

    def shutdown(self):
        logger.info("DummyPlugin: Shutting down...")

    def get_features(self):
        # Register a Test Algorithm
        return [
            Feature(
                name="UPPERCASE_TEST",
                handler=lambda content: content.replace("<!-- UPPERCASE_ME -->", "I WAS UPPERCASED BY PIPELINE!"),
                state=FeatureState.EXPERIMENTAL,
                feature_type=FeatureType.ALGORITHM
            )
        ]

# Register the plugin instance
instance = DummyPlugin()
PluginRegistry().register(instance)

# Expose features for Loader to find
def get_features():
    return instance.get_features()
