from enum import Enum, auto
from typing import Callable, List, Optional, Any, Dict
import logging

logger = logging.getLogger(__name__)

class FeatureState(Enum):
    STANDARD = auto()
    EXPERIMENTAL = auto()

class FeatureType(Enum):
    ALGORITHM = auto() # Markdown processing, text transformation
    UI_EXTENSION = auto() # Legacy/Other
    EXPORT_HANDLER = auto()

class Feature:
    def __init__(self, name: str, handler: Callable[[str], Any], state: FeatureState, feature_type: FeatureType = FeatureType.ALGORITHM):
        self.name = name
        self.handler = handler
        self.state = state
        self.type = feature_type

class Pipeline:
    """
    A sequence of algorithms (Features) to be executed in order.
    The 'Backbone' of document processing.
    """
    def __init__(self, name: str):
        self.name = name
        self._steps: List[Callable[[str], str]] = []

    def add_step(self, handler: Callable[[str], str]):
        self._steps.append(handler)

    def run(self, content: str) -> str:
        """Execute the pipeline on the content."""
        for step in self._steps:
            try:
                content = step(content)
            except Exception as e:
                logger.error(f"Pipeline {self.name} step {step.__name__ if hasattr(step, '__name__') else 'unknown'} failed: {e}")
                # specific strategy for failure? For now, log and continue with partial content
        return content
    
    def __iter__(self):
        """Allow iteration for backward compatibility if needed."""
        return iter(self._steps)

class PluginRegistry:
    """
    Singleton Registry to hold all discovered plugin modules/features.
    Ensure shared state across the application.
    """
    _instance = None
    _plugins = []
    _custom_slots: Dict[str, List[str]] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PluginRegistry, cls).__new__(cls)
            cls._instance._plugins = []
            cls._instance._custom_slots = {}
        return cls._instance

    def register(self, plugin_or_feature: Any):
        """Register a plugin module or feature."""
        # Avoid duplicate registration
        if plugin_or_feature not in self._plugins:
            self._plugins.append(plugin_or_feature)
            logger.info(f"PluginRegistry: Registered {plugin_or_feature}")

    def register_slot(self, slot_name: str, content: str) -> None:
        """
        Register content for a specific UI slot.
        Appends the content to the list for that slot.
        """
        if slot_name not in self._custom_slots:
            self._custom_slots[slot_name] = []
        self._custom_slots[slot_name].append(content)
        logger.debug(f"Registered content for slot: {slot_name}")

    def get_slots(self, slot_name: str) -> List[str]:
        """
        Retrieve all content registered for a specific slot.
        Returns a list of safe HTML strings.
        """
        return self._custom_slots.get(slot_name, [])

    def get_all_plugins(self) -> List[Any]:
        return self._plugins
    
    def initialize_all(self):
        """
        Optional: Trigger initialization logic on all plugins if they have it.
        """
        for plugin in self._plugins:
            # Check for standard initialize
            if hasattr(plugin, 'initialize'):
                try:
                    plugin.initialize()
                except Exception as e:
                    logger.error(f"Failed to initialize plugin {plugin}: {e}")
            # Check for legacy initialize(registry) if strictly needed, though we moved to DI
                except Exception as e:
                    logger.error(f"Failed to initialize plugin {plugin}: {e}")

class FeatureManager:
    """
    Facade that aggregates features from the PluginRegistry and manages Pipelines.
    """
    def __init__(self, registry: Optional[Any] = None):
        self._features: List[Feature] = []
        self._registry = registry

    def register(self, feature: Feature):
        """Register a feature manually (Core features)."""
        self._features.append(feature)

    def refresh(self):
        """Pull features from the attached PluginRegistry."""
        if not self._registry:
            return
        
        logger.info("FeatureManager: Refreshing features from Registry...")
        # Clear existing plugin features to avoid duplicates (preserving core if mixed, but here simpler)
        # Actually, self._features grows indefinitely? Let's reset it to safe core state? 
        # For now, just logging.
        plugins = self._registry.get_all_plugins()
        count = 0
        for plugin in plugins:
            # Duck typing check instead of strict isinstance to survive import/reload cycles
            if hasattr(plugin, 'name') and hasattr(plugin, 'type') and hasattr(plugin, 'handler'):
                 # Check for duplicates by name
                 if not any(f.name == plugin.name for f in self._features):
                    self._features.append(plugin)
                    count += 1
                    logger.debug(f"Registered plugin feature (duck-typed): {plugin.name}")
            elif hasattr(plugin, 'get_features'):
                 # Legacy path (should be unused now)
                 pass

        logger.info(f"FeatureManager: Loaded {count} features. Total: {len(self._features)}")

    def get_export_handler(self, format_ext: str) -> Optional[Callable]:
        """
        Retrieve a registered export handler for a specific format extension.
        """
        logger.debug(f"FeatureManager: Looking for export handler for '{format_ext}'...")
        for feature in self._features:
            # Flexible type checking
            ft_type = str(feature.type) # e.g. "FeatureType.EXPORT_HANDLER"
            
            if "EXPORT_HANDLER" in ft_type and feature.name == format_ext:
                logger.info(f"FeatureManager: Found handler for {format_ext}")
                return feature.handler
        
        logger.warning(f"FeatureManager: No handler found for {format_ext}. Available: {[f.name for f in self._features]}")
        return None

    def build_pipeline(self, enable_experimental: bool) -> Pipeline:
        """
        Build the standard processing pipeline.
        Returns a Pipeline object.
        """
        pipeline = Pipeline("StandardPipeline")
        
        # Sort or prioritize? 
        # Currently we rely on insertion order: Core features first (registered in app.py), then Plugins.
        for f in self._features:
            if f.type != FeatureType.ALGORITHM:
                continue

            if f.state == FeatureState.STANDARD:
                pipeline.add_step(f.handler)
            elif enable_experimental and f.state == FeatureState.EXPERIMENTAL:
                pipeline.add_step(f.handler)
        
        return pipeline
