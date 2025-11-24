"""
test_base_item.py
-----------------
Regression tests for BaseItem entity.

Covers:
- Initialization and configuration
- Movement and Physics (velocity, bouncing)
- Lifecycle management (lifetime, despawning)
- Collision handling and effects
- Object pooling reset
"""

import pytest
from unittest.mock import MagicMock, patch
import pygame
from src.entities.items.base_item import BaseItem
from src.entities.entity_state import LifecycleState
from src.core.runtime.game_settings import Display

# ===========================================================
# Fixtures
# ===========================================================

@pytest.fixture
def mock_pygame_surface():
    """Mock for pygame.Surface."""
    surface = MagicMock(spec=pygame.Surface)
    surface.get_rect.return_value = pygame.Rect(0, 0, 48, 48)
    surface.get_width.return_value = 48
    surface.get_height.return_value = 48
    return surface

@pytest.fixture
def mock_draw_manager():
    """Mock for DrawManager."""
    return MagicMock()

@pytest.fixture
def basic_item_data():
    """Standard item configuration for testing."""
    return {
        "effects": [{"type": "heal", "value": 10}],
        "physics": {"velo_x": 100, "velo_y": 100},
        "scale": 1.0
    }

@pytest.fixture
def item(mock_pygame_surface, mock_draw_manager, basic_item_data):
    """Fixture creating a standard BaseItem instance."""
    # Patch pygame.transform.scale to avoid actual image processing
    with patch('pygame.transform.scale', return_value=mock_pygame_surface):
        item = BaseItem(
            x=100,
            y=100,
            item_data=basic_item_data,
            image=mock_pygame_surface,
            draw_manager=mock_draw_manager,
            bounce=False # Disable bounce for deterministic movement tests by default
        )
    return item

# ===========================================================
# Test Suites
# ===========================================================

class TestBaseItemInitialization:
    def test_init_defaults(self, mock_pygame_surface, mock_draw_manager):
        """Test initialization with minimal arguments."""
        with patch('pygame.transform.scale', return_value=mock_pygame_surface):
            item = BaseItem(x=50, y=50, image=mock_pygame_surface, draw_manager=mock_draw_manager)
        
        assert item.pos.x == 50
        assert item.pos.y == 50
        assert item.lifetime == 5.0 # Default
        assert item.speed == 500 # Default speed setting
        # With bounce=True (default), velocity is randomized but magnitude should match speed
        assert pytest.approx(item.velocity.length(), rel=1e-3) == 500
        assert item.category == "pickup" # From EntityCategory.PICKUP
        
    def test_init_with_data(self, item, basic_item_data):
        """Test initialization with provided item_data."""
        assert item.item_data == basic_item_data
        # Check physics applied
        assert item.velocity.x == 100
        assert item.velocity.y == 100

class TestBaseItemMovement:
    def test_update_movement(self, item):
        """Test that update moves the item based on velocity."""
        dt = 0.1
        initial_x, initial_y = item.pos.x, item.pos.y
        vx, vy = item.velocity.x, item.velocity.y
        
        item.update(dt)
        
        assert item.pos.x == initial_x + vx * dt
        assert item.pos.y == initial_y + vy * dt
        
    def test_bounce_logic(self, mock_pygame_surface, mock_draw_manager):
        """Test that item bounces off screen edges."""
        with patch('pygame.transform.scale', return_value=mock_pygame_surface):
            # Force bounce enabled
            item = BaseItem(x=10, y=10, image=mock_pygame_surface, draw_manager=mock_draw_manager, bounce=True)
        
        # Manually set position and velocity to test bounce
        # Test Left Wall
        item.pos.x = -1
        item.velocity.x = -100
        item.update(0.01) # Trigger logic
        assert item.velocity.x == 100 # Should flip
        
        # Test Right Wall
        item.pos.x = Display.WIDTH + 1
        item.velocity.x = 100
        item.update(0.01)
        assert item.velocity.x == -100 # Should flip

class TestBaseItemLifecycle:
    def test_lifetime_expiry(self, item):
        """Test that item marks itself dead after lifetime expires."""
        item.lifetime = 1.0
        item.update(0.5)
        assert item.death_state == LifecycleState.ALIVE
        
        item.update(0.6) # Total 1.1 > 1.0
        assert item.death_state != LifecycleState.ALIVE # Should be dead/dying

class TestBaseItemCollision:
    @patch('src.entities.items.base_item.get_events')
    @patch('src.entities.items.base_item.apply_item_effects')
    def test_collision_with_player(self, mock_apply_effects, mock_get_events, item):
        """Test collision with player triggers effects and event."""
        mock_player = MagicMock()
        mock_player.collision_tag = "player"
        
        # Setup event dispatcher mock
        mock_event_dispatcher = MagicMock()
        mock_get_events.return_value = mock_event_dispatcher
        
        item.on_collision(mock_player)
        
        # Check effects applied
        mock_apply_effects.assert_called_once_with(mock_player, item.get_effects())
        
        # Check event dispatched
        assert mock_event_dispatcher.dispatch.called
        
        # Check item died
        assert item.death_state != LifecycleState.ALIVE

    def test_collision_with_non_player(self, item):
        """Test collision with non-player does nothing."""
        mock_other = MagicMock()
        mock_other.collision_tag = "enemy"
        
        initial_state = item.death_state
        item.on_collision(mock_other)
        
        assert item.death_state == initial_state # Should stay alive

class TestBaseItemReset:
    def test_reset_functionality(self, item):
        """Test resetting the item for object pooling."""
        # Change state
        item.lifetime_timer = 2.0
        item.pos.x = 999
        
        item.reset(x=200, y=200, speed=300)
        
        assert item.pos.x == 200
        assert item.pos.y == 200
        assert item.speed == 300
        assert item.velocity.y == 300
        assert item.lifetime_timer == 0.0