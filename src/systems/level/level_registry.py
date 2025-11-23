"""
level_registry.py
-----------------
Central registry for level metadata, progression, and campaign management.

Responsibilities
----------------
- Load level definitions from config JSON
- Provide O(1) level lookup by ID
- Manage campaign ordering
- Track unlock state
- Support multiple campaigns/modes

Performance
-----------
- Config loaded once at startup (cold path)
- Level lookup: O(1) hash table
- Campaign ordering: O(1) list access
"""

from src.core.services.config_manager import load_config
from src.core.debug.debug_logger import DebugLogger


class LevelConfig:
    """Metadata container for a single level."""

    def __init__(self, level_id: str, data: dict):
        """
        Initialize level configuration.

        Args:
            level_id: Unique identifier for the level
            data: Level config from config
                {
                    "path": "levels/Stage_1.json",
                    "name": "First Contact",
                    "unlocked": false,
                    "campaign": "main"
                }
        """
        self.id = level_id
        path = data["path"]
        if not path.startswith("levels/") and not path.startswith("config/"):
            path = f"levels/{path}"
        self.path = path
        self.name = data.get("name", level_id)
        self.unlocked = data.get("unlocked", False)
        self.campaign = data.get("campaign", None)

        # Optional metadata
        self.duration = data.get("duration", None)
        self.difficulty = data.get("difficulty", "normal")
        self.description = data.get("description", "")


class LevelRegistry:
    """
    Global registry for level config and progression.

    Manages level metadata, campaign ordering, and unlock state.
    """

    _levels = {}  # {level_id: LevelConfig}
    _campaigns = {}  # {campaign_name: {"name": str, "levels": [level_ids]}}
    _default_campaign = None
    _initialized = False

    # ===========================================================
    # Initialization
    # ===========================================================

    @classmethod
    def load_config(cls, config_path: str = "config/campaigns.json"):
        """
        Load level definitions from JSON config.

        Should be called once at game startup.

        Args:
            config_path: Path to levels configuration file
        """
        if cls._initialized:
            DebugLogger.warn("[LevelRegistry] Already initialized, skipping reload")
            return

        DebugLogger.init_entry("Loading Level Registry")

        try:
            data = load_config(config_path, {"levels": {}, "campaigns": {}})

            # Register levels
            level_count = 0
            for level_id, level_data in data.get("levels", {}).items():
                cls._levels[level_id] = LevelConfig(level_id, level_data)
                level_count += 1

            DebugLogger.init_sub(f"Registered {level_count} levels")

            # Register campaigns
            campaign_count = 0
            for campaign_name, campaign_data in data.get("campaigns", {}).items():
                campaign_levels = campaign_data.get("levels", [])
                start_level = campaign_data.get("start_level")

                invalid_levels = [lvl for lvl in campaign_levels if lvl not in cls._levels]
                if invalid_levels:
                    DebugLogger.warn(
                        f"Campaign '{campaign_name}' references unknown levels: {invalid_levels}",
                        category="loading"
                    )

                if start_level and start_level not in cls._levels:
                    DebugLogger.warn(
                        f"Campaign '{campaign_name}' has invalid start_level: '{start_level}'",
                        category="loading"
                    )

                cls._campaigns[campaign_name] = {
                    "name": campaign_data.get("name", campaign_name),
                    "start_level": start_level,
                    "levels": campaign_levels
                }
                campaign_count += 1

            DebugLogger.init_sub(f"Registered {campaign_count} campaigns")

            # Set default start
            cls._default_campaign = data.get("default_campaign")
            if cls._default_campaign:
                if cls._default_campaign not in cls._campaigns:
                    DebugLogger.warn(
                        f"default_campaign '{cls._default_campaign}' does not exist",
                        category="loading"
                    )
                else:
                    DebugLogger.init_sub(f"Default Campaign: {cls._default_campaign}")

            cls._initialized = True
            DebugLogger.init_entry("Level Registry Loaded")

        except Exception as e:
            DebugLogger.fail(f"Failed to load config: {e}")
            cls._initialized = False

    # ===========================================================
    # Lookup Methods
    # ===========================================================

    @classmethod
    def get(cls, level_id: str):
        """
        Retrieve level configuration by ID.

        Args:
            level_id: Unique level identifier

        Returns:
            LevelConfig or None if not found
        """
        return cls._levels.get(level_id)

    @classmethod
    def get_campaign(cls, campaign_name: str):
        """
        Get ordered list of levels for a campaign.

        Args:
            campaign_name: Campaign identifier (e.g., "main", "test")

        Returns:
            list[LevelConfig]: Ordered campaign levels
        """
        campaign = cls._campaigns.get(campaign_name)
        if not campaign:
            DebugLogger.warn(f"[LevelRegistry] Unknown campaign: {campaign_name}")
            return []

        level_ids = campaign["levels"]
        return [cls._levels[lid] for lid in level_ids if lid in cls._levels]

    @classmethod
    def get_default_start(cls):
        """
        Get the default starting level from default campaign.

        Returns:
            LevelConfig or None
        """
        if not cls._default_campaign:
            return None

        campaign = cls._campaigns.get(cls._default_campaign)
        if not campaign:
            return None

        start_level_id = campaign.get("start_level")
        if start_level_id:
            return cls.get(start_level_id)

        # Fallback: first level in campaign
        levels = campaign.get("levels", [])
        return cls.get(levels[0]) if levels else None

    @classmethod
    def get_unlocked(cls):
        """
        Get all unlocked levels.

        Returns:
            list[LevelConfig]: All unlocked levels
        """
        return [lvl for lvl in cls._levels.values() if lvl.unlocked]

    @classmethod
    def list_campaigns(cls):
        """
        Get list of all campaign names.

        Returns:
            list[str]: Campaign names
        """
        return list(cls._campaigns.keys())

    # ===========================================================
    # Progression Methods
    # ===========================================================

    @classmethod
    def unlock(cls, level_id: str):
        """
        Mark a level as unlocked.

        Args:
            level_id: Level to unlock

        Returns:
            bool: True if unlocked, False if level doesn't exist
        """
        if level_id in cls._levels:
            cls._levels[level_id].unlocked = True
            DebugLogger.state(f"[LevelRegistry] Unlocked: {level_id}")
            return True

        DebugLogger.warn(f"[LevelRegistry] Cannot unlock unknown level: {level_id}")
        return False

    @classmethod
    def lock(cls, level_id: str):
        """
        Mark a level as locked.

        Args:
            level_id: Level to lock

        Returns:
            bool: True if locked, False if level doesn't exist
        """
        if level_id in cls._levels:
            cls._levels[level_id].unlocked = False
            return True
        return False

    @classmethod
    def is_unlocked(cls, level_id: str):
        """
        Check if a level is unlocked.

        Args:
            level_id: Level to check

        Returns:
            bool: True if unlocked
        """
        level = cls.get(level_id)
        return level.unlocked if level else False

    # ===========================================================
    # Debug & Inspection
    # ===========================================================

    @classmethod
    def debug_print_all(cls):
        """Print all registered levels and campaigns for debugging."""
        DebugLogger.section("=== Level Registry ===")

        DebugLogger.system(f"Total Levels: {len(cls._levels)}")
        for level_id, config in cls._levels.items():
            status = "UNLOCKED" if config.unlocked else "LOCKED"
            DebugLogger.system(f"  [{status}] {level_id}: {config.name} ({config.path})")

        DebugLogger.system(f"\nTotal Campaigns: {len(cls._campaigns)}")
        for campaign_name, campaign_data in cls._campaigns.items():
            DebugLogger.system(f"  {campaign_name}: {campaign_data['name']}")
            DebugLogger.system(f"    Levels: {', '.join(campaign_data['levels'])}")

        if cls._default_campaign:
            DebugLogger.system(f"\nDefault Start: {cls._default_campaign}")

    @classmethod
    def reset(cls):
        """Clear all registry config (for testing)."""
        cls._levels.clear()
        cls._campaigns.clear()
        cls._default_campaign = None
        cls._initialized = False