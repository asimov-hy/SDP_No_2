class GameState:
    def __init__(self):
        # Scene control
        self.current_scene = "start"
        self.previous_scene = None

        # Session statistics (isolated data container)
        self.stats = {
            "score": 0,
            "high_score": 0,
            "total_score": 0,
            "enemies_killed": 0,
            "items_collected": 0,
            "run_time": 0.0,
        }

        # Global entity registry for cross-system access
        # Used by debug systems, analytics, etc.
        self.entities = {}

    # ===========================================================
    # Stats Accessors
    # ===========================================================
    def get_stat(self, key, default=None):
        """Retrieve a stat value safely."""
        return self.stats.get(key, default)

    def set_stat(self, key, value):
        """Set or overwrite a stat value."""
        self.stats[key] = value

    def add_stat(self, key, amount):
        """Increment a numerical stat. Initializes if missing."""
        self.stats[key] = self.stats.get(key, 0) + amount

    def has_stat(self, key):
        """Check if a stat exists."""
        return key in self.stats

    def remove_stat(self, key):
        """Delete a stat if present."""
        if key in self.stats:
            del self.stats[key]

    def reset(self):
        """Reset state to defaults when starting a new game."""
        # Clear entity registry without reinitializing entire object
        self.entities.clear()
        self.stats = {
            "score": 0,
            "high_score": 0,
            "total_score": 0,
            "enemies_killed": 0,
            "items_collected": 0,
            "run_time": 0.0,
        }

    # ===========================================================
    # Entity Registry
    # ===========================================================
    def register_entity(self, key, entity):
        """
        Register an entity for global access.

        Args:
            key: String identifier (e.g., "player", "boss")
            entity: Entity reference
        """
        self.entities[key] = entity

    def get_entity(self, key, default=None):
        """
        Retrieve a registered entity safely.

        Args:
            key: String identifier
            default: Value to return if key not found
        """
        return self.entities.get(key, default)

    def unregister_entity(self, key):
        """Remove an entity from registry."""
        if key in self.entities:
            del self.entities[key]


# Global singleton instance for shared access
STATE = GameState()
