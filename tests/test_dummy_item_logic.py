import pytest
import pygame
from src.entities.player import Player
from src.entities.items.dummy_item import DummyItem
from src.core.game_state import GameState

@pytest.fixture(scope="module")
def pygame_init():
    pygame.init()
    yield
    pygame.quit()

@pytest.fixture
def game_state():
    gs = GameState()
    gs.lives = 3
    return gs

@pytest.fixture
def dummy_surface(pygame_init):
    return pygame.Surface((10, 10))

# @pytest.fixture
# def player(dummy_surface):
#     return Player(x=100, y=100, image=dummy_surface)

@pytest.fixture
def item(dummy_surface, game_state):
    return DummyItem(x=120, y=120, image=dummy_surface, game_state=game_state)

def test_dummy_item_lives_change(item, game_state):
    """
    Tests if DummyItem correctly changes player lives in GameState using pytest.
    """
    # 1. Arrange
    initial_lives = game_state.lives
    lives_change_amount = item.lives_change
    expected_lives = initial_lives + lives_change_amount

    # 2. Act
    # Apply the item's effect directly, passing the player.
    item.apply_effect()

    # 3. Assert
    # Verify that player lives in GameState have changed as expected.
    assert game_state.lives == expected_lives
