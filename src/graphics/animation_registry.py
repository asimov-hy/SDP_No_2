"""
animation_registry.py
---------------------
Global animation registry used by AnimationManager to resolve animation handlers dynamically.

Responsibilities
----------------
- Store and retrieve animation handler classes by entity tag.
- Provide decorator-based registration for automatic integration.
- Ensure decoupling between entity code and animation system.
"""


registry = {}

def register(tag):
    """Decorator for registering animation classes by their entity collision tag."""
    def decorator(cls):
        registry[tag] = cls
        return cls
    return decorator
