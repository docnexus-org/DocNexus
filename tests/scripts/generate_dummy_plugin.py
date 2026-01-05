import os
from pathlib import Path

def create_dummy_plugin():
    base_dir = Path("docnexus/plugins_dev/dummy_plugin")
    base_dir.mkdir(parents=True, exist_ok=True)
    
    plugin_content = '''from typing import Dict, Any, List
from docnexus.core.plugin_interface import PluginInterface
from docnexus.features.registry import Feature, FeatureState, FeatureType

def uppercase_content(content: str) -> str:
    """Test Algorithm: Uppercases a specific placeholder."""
    import logging
    logging.getLogger(__name__).info("DummyPlugin: executing uppercase_content algorithm")
    return content.replace("<!-- UPPERCASE_ME -->", "I WAS UPPERCASED BY PIPELINE!")

class DummyPlugin(PluginInterface):
    def get_meta(self) -> Dict[str, Any]:
        return {
            "name": "Dummy Plugin",
            "version": "1.0.0",
            "description": "Refactor Test",
            "author": "Dev"
        }

    def initialize(self, registry: Any) -> None:
        # Test UI Slot registration (Legacy/Standard)
        if hasattr(registry, "register_slot"):
            registry.register_slot("HEADER_RIGHT", \'<button class="btn btn-sm btn-warning">Refactor OK</button>\')

    def shutdown(self) -> None:
        pass

    def get_features(self) -> List[Any]:
        # Test Pipeline Registration (New Facade)
        return [
            Feature("UPPERCASE_TEST", uppercase_content, FeatureState.STANDARD, FeatureType.ALGORITHM)
        ]

# Register the plugin instance
try:
    from docnexus.core.registry import PluginRegistry
    PluginRegistry().register(DummyPlugin())
except Exception as e:
    import logging
    logging.getLogger(__name__).error(f"Failed to register DummyPlugin: {e}")
'''
    
    with open(base_dir / "plugin.py", "w", encoding="utf-8") as f:
        f.write(plugin_content)
        
    print(f"Created dummy plugin at {base_dir}")

if __name__ == "__main__":
    create_dummy_plugin()
