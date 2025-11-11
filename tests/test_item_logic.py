"""
test_item_logic.py
------------------
Pytest-style unit tests for the current implementation of Item and ItemManager.
"""
import pytest
import json
import os
from unittest.mock import patch

# Adjust the path to import modules from src
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.entities.items.item import Item
from src.systems.item_manager import ItemManager

# Mock item definitions for testing, reflecting the current simple structure
MOCK_ITEM_DEFINITIONS = {
    "test_potion": {
        "name": "Test Potion",
        "asset_path": "assets/images/items/test_potion.png",
        "conditions": [{"type": "COLLECTIBLE", "value": True}],
        "effects": [{"type": "HEAL", "amount": 10}]
    },
    "test_rock": {
        "name": "Test Rock",
        "asset_path": "assets/images/items/rock.png",
        "conditions": [{"type": "COLLECTIBLE", "value": False}],
        "effects": []
    }
}

# --- Fixtures ---

@pytest.fixture(scope="module")
def mock_item_data_file():
    """Fixture to create a temporary item data JSON file for tests."""
    path = os.path.join(os.path.dirname(__file__), 'temp_pytest_items.json')
    with open(path, 'w') as f:
        json.dump(MOCK_ITEM_DEFINITIONS, f)
    yield path
    # Teardown: remove the file after tests are done
    os.remove(path)

@pytest.fixture
def mock_debug_logger():
    """Fixture to patch DebugLogger for the duration of a test."""
    with patch('src.systems.item_manager.DebugLogger') as mock_logger:
        yield mock_logger

@pytest.fixture
def item_manager(mock_item_data_file, mock_debug_logger):
    """Fixture to get a clean ItemManager instance for each test."""
    # Pass a mock game_state, as the __init__ expects it
    mock_game_state = object()
    manager = ItemManager(game_state=mock_game_state, item_data_path=mock_item_data_file)
    return manager

# --- Tests for Item Class ---

def test_item_initialization():
    """Test that an Item instance correctly loads all data from item_data."""
    item_id = "test_potion"
    position = (100, 200)
    item_data = MOCK_ITEM_DEFINITIONS[item_id]
    
    item = Item(item_id, position, item_data)

    assert item.item_id == item_id
    assert item.position == position
    assert item.name == "Test Potion"
    assert item.asset_path == "assets/images/items/test_potion.png"
    assert item.conditions == [{"type": "COLLECTIBLE", "value": True}]
    assert item.effects == [{"type": "HEAL", "amount": 10}]
    assert item.instance_id is not None

# --- Tests for ItemManager Class ---

def test_item_manager_initialization(item_manager, mock_item_data_file, mock_debug_logger):
    """Test the initialization of the ItemManager."""
    assert item_manager._item_definitions is not None
    assert "test_potion" in item_manager._item_definitions
    assert item_manager._item_definitions == MOCK_ITEM_DEFINITIONS # New assertion
    assert len(item_manager.active_items) == 0
    mock_debug_logger.system.assert_called_once_with(
        f"Loaded {len(MOCK_ITEM_DEFINITIONS)} item definitions from '{mock_item_data_file}'."
    )

def test_spawn_known_item(item_manager, mock_debug_logger):
    """Test that a known item can be spawned successfully."""
    item_manager.spawn_item("test_potion", (50, 50))
    
    assert len(item_manager.active_items) == 1
    spawned_item = item_manager.active_items[0]
    
    assert isinstance(spawned_item, Item)
    assert spawned_item.item_id == "test_potion"
    assert spawned_item.position == (50, 50)
    mock_debug_logger.info.assert_called_with("Spawned item 'test_potion' at (50, 50).")

def test_spawn_unknown_item(item_manager, mock_debug_logger):
    """Test that an unknown item is not spawned and a warning is logged."""
    item_manager.spawn_item("unknown_item", (10, 10))
    
    assert len(item_manager.active_items) == 0
    mock_debug_logger.warn.assert_called_with(
        "Attempted to spawn an unknown item_id: 'unknown_item'"
    )