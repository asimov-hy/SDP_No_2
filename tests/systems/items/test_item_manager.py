"""
test_item_manager.py
--------------------
Unit tests for the ItemManager system.

Responsibilities
----------------
- Verify correct loading of item definitions and loot table construction.
- Test drop probability logic (success/failure scenarios).
- Validate integration with SpawnManager and EventManager.
- Ensure robust handling of missing assets and invalid configurations.
- Verify resource caching mechanisms.
"""

import pytest
from unittest.mock import MagicMock, patch, ANY
import pygame

from src.systems.entity_management.item_manager import ItemManager, ItemType
from src.core.services.event_manager import EnemyDiedEvent

# ===========================================================
# Fixtures
# ===========================================================

@pytest.fixture
def mock_spawn_manager():
    """Mock for the SpawnManager."""
    return MagicMock()


@pytest.fixture
def test_item_config():
    """
    Sample item configuration mimicking items.json.
    Uses valid ItemType keys (e.g., 'heal', 'nuke') to pass enum validation.
    """
    return {
        "heal": {
            "drop_weight": 100,
            "asset_path": "assets/items/health.png",
            "effects": [{"type": "ADD_HEALTH", "amount": 1}],
            "size": [32, 32]
        },
        "nuke": {
            "drop_weight": 50,
            "asset_path": "assets/items/nuke.png",
            "effects": [{"type": "NUKE_ALL"}]
        },
        "quick_fire": {
            "drop_weight": 0,  # Should not be in loot table
            "asset_path": "assets/items/quick_fire.png"
        }
    }


@pytest.fixture
def item_manager(mock_spawn_manager, test_item_config):
    """
    Creates an ItemManager instance with mocked config and file system.
    Crucially uses yield to keep patches active during tests.
    """
    with patch('src.systems.entity_management.item_manager.load_config', return_value=test_item_config), \
            patch('src.systems.entity_management.item_manager.pygame.image.load') as mock_load, \
            patch('src.systems.entity_management.item_manager.pygame.transform.scale') as mock_scale, \
            patch('src.systems.entity_management.item_manager.os.path.exists', return_value=True):
        
        # Setup mocks to return other mocks, satisfying type checks if any
        mock_surf = MagicMock(spec=pygame.Surface)
        mock_load.return_value = mock_surf
        mock_load.return_value.convert_alpha.return_value = mock_surf
        mock_load.return_value.copy.return_value = mock_surf
        
        mock_scale.return_value = mock_surf

        manager = ItemManager(mock_spawn_manager, "fake_path.json")
        yield manager


# ===========================================================
# Initialization & Loot Table Tests
# ===========================================================

def test_loot_table_construction(item_manager):
    """
    Verify that the loot table is built correctly from config weights.
    Items with weight 0 should be excluded.
    """
    # Check IDs
    assert ItemType.HEAL in item_manager._loot_table_ids
    assert ItemType.NUKE in item_manager._loot_table_ids
    assert ItemType.QUICK_FIRE not in item_manager._loot_table_ids  # Weight 0

    # Check Weights
    # Indices correspond to _loot_table_ids order
    heal_idx = item_manager._loot_table_ids.index(ItemType.HEAL)
    nuke_idx = item_manager._loot_table_ids.index(ItemType.NUKE)

    assert item_manager._loot_table_weights[heal_idx] == 100
    assert item_manager._loot_table_weights[nuke_idx] == 50


def test_initialization_empty_config(mock_spawn_manager):
    """
    Test resilience when loaded with empty configuration.
    """
    with patch('src.systems.entity_management.item_manager.load_config', return_value={}):
        manager = ItemManager(mock_spawn_manager, "empty.json")
        assert len(manager._loot_table_ids) == 0
        assert len(manager._loot_table_weights) == 0


# ===========================================================
# Drop Logic Tests
# ===========================================================

@pytest.mark.parametrize("roll, drop_chance, should_spawn", [
    (0.1, 0.35, True),  # Roll (0.1) < Chance (0.35) -> Spawn
    (0.34, 0.35, True),  # Boundary case -> Spawn
    (0.36, 0.35, False),  # Roll > Chance -> No Spawn
    (0.9, 0.35, False),  # High roll -> No Spawn
    (0.1, 0.0, False),  # Zero chance -> No Spawn
    (0.0, 1.0, True),  # 100% chance -> Spawn
])
def test_try_spawn_random_logic(item_manager, roll, drop_chance, should_spawn):
    """
    Test the probability logic for spawning items.
    """
    # Mock random dependencies
    with patch('random.random', return_value=roll), \
            patch('random.choices', return_value=[ItemType.HEAL]):

        item_manager.try_spawn_random_item((100, 200), drop_chance)

        if should_spawn:
            item_manager.spawn_manager.spawn.assert_called_once()
        else:
            item_manager.spawn_manager.spawn.assert_not_called()


def test_spawn_selection_weighted(item_manager):
    """
    Verify that random.choices is called with correct weights.
    """
    with patch('random.random', return_value=0.0), \
            patch('random.choices', return_value=[ItemType.NUKE]) as mock_choices:
        item_manager.try_spawn_random_item((0, 0), 1.0)

        mock_choices.assert_called_once_with(
            item_manager._loot_table_ids,
            weights=item_manager._loot_table_weights,
            k=1
        )


# ===========================================================
# Spawning & Resource Tests
# ===========================================================

def test_spawn_item_execution(item_manager, test_item_config):
    """
    Verify that spawn_item calls SpawnManager with correct parameters.
    """
    target_pos = (150, 300)
    item_type = ItemType.HEAL

    item_manager.spawn_item(item_type, target_pos)

    # Check if spawn was called with correct category and type
    item_manager.spawn_manager.spawn.assert_called_once_with(
        "pickup",
        "default",
        150, 300,
        item_data=test_item_config["heal"],
        image=ANY  # Image is mocked/loaded
    )


def test_image_caching(item_manager):
    """
    Verify that images are loaded once and cached for subsequent spawns.
    """
    # Since we are using the fixture's patches, we need to access the mocked load
    # We can re-patch it to get access to the mock object, OR we can trust the fixture.
    # But to assert call count, we need the mock object.
    # The fixture swallows the mock objects.
    # Strategy: Patch it AGAIN. The inner patch will override the fixture's patch temporarily.
    
    with patch('src.systems.entity_management.item_manager.pygame.image.load') as mock_load:
        mock_surf = MagicMock(spec=pygame.Surface)
        mock_load.return_value = mock_surf
        mock_load.return_value.convert_alpha.return_value = mock_surf

        # Clear cache to ensure clean state if fixture pre-loaded anything (it didn't)
        item_manager._image_cache = {}

        # First Spawn: Should trigger load
        item_manager.spawn_item(ItemType.HEAL, (0, 0))
        assert mock_load.call_count == 1

        # Second Spawn (Same type): Should use cache
        item_manager.spawn_item(ItemType.HEAL, (0, 0))
        assert mock_load.call_count == 1  # Count remains 1

        # Third Spawn (Different type): Should trigger load
        item_manager.spawn_item(ItemType.NUKE, (0, 0))
        assert mock_load.call_count == 2


def test_fallback_image_loading(item_manager):
    """
    Verify behavior when asset path does not exist.
    """
    # Force load failure to trigger fallback
    with patch('src.systems.entity_management.item_manager.pygame.image.load', side_effect=Exception("Force Fallback")), \
         patch('src.systems.entity_management.item_manager.pygame.transform.scale', side_effect=lambda img, size: img):
        # Inject a fallback image manually for this test
        fallback_surf = MagicMock(spec=pygame.Surface)
        fallback_surf.copy.return_value = fallback_surf
        item_manager._fallback_image = fallback_surf
        item_manager._image_cache = {} # Clear cache to ensure load is attempted
        
        item_manager.spawn_item(ItemType.HEAL, (0, 0))

        # Should spawn using fallback image
        args, kwargs = item_manager.spawn_manager.spawn.call_args
        # We expect the image kwarg to be derived from fallback (the mocked surf)
        assert kwargs['image'] == fallback_surf
        # Check that scale was called (since fallback uses scale)
        # We can't easily check scale call unless we mock it again or inspect the result
        # But if it didn't crash, it means it worked.


# ===========================================================
# Integration & Edge Case Tests
# ===========================================================

def test_on_enemy_died_integration(item_manager):
    """
    Verify integration flow from Event -> on_enemy_died -> spawn.
    """
    event = EnemyDiedEvent(
        position=(500, 500),
        enemy_type_tag="EnemyStraight",
        exp=10
    )

    # Force drop success
    with patch('random.random', return_value=0.0), \
            patch('random.choices', return_value=[ItemType.NUKE]):
        item_manager.on_enemy_died(event)

        # Should spawn item at event position
        item_manager.spawn_manager.spawn.assert_called_once()
        args, _ = item_manager.spawn_manager.spawn.call_args
        assert args[2] == 500  # x
        assert args[3] == 500  # y