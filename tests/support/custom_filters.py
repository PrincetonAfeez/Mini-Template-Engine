"""Custom filters used by CLI integration tests."""

from template_engine import FilterRegistry, default_filter_registry

filter_registry: FilterRegistry = default_filter_registry()
filter_registry.register("exclaim", lambda value: str(value) + "!")
