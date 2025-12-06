"""
conftest.py
-----------
Shared pytest configuration and fixtures for SDP-202X tests.

Contains:
- Common fixtures used across multiple test modules
- Pytest configuration and hooks
- Shared mock utilities and test helpers
"""

import pytest
import sys
import os
from unittest.mock import MagicMock

# Add src directory to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

# Mock pygame globally before any imports that might use it
mock_pygame = MagicMock()
sys.modules["pygame"] = mock_pygame
sys.modules["pygame.font"] = MagicMock()
sys.modules["pygame.display"] = MagicMock()
sys.modules["pygame.transform"] = MagicMock()
sys.modules["pygame.Surface"] = MagicMock
sys.modules["pygame.Rect"] = MagicMock
sys.modules["pygame.Vector2"] = MagicMock
sys.modules["pygame.mouse"] = MagicMock()
sys.modules["pygame.event"] = MagicMock()
sys.modules["pygame.key"] = MagicMock()

# Mock pygame constants
mock_pygame.MOUSEBUTTONDOWN = 1
mock_pygame.MOUSEBUTTONUP = 0
mock_pygame.K_LEFT = 276
mock_pygame.K_RIGHT = 275
mock_pygame.K_RETURN = 13
mock_pygame.SRCALPHA = 32


@pytest.fixture(scope="session")
def pygame_mocks():
    """Session-wide pygame mocking to avoid import issues."""
    with pytest.MonkeyPatch().context() as m:
        # Mock pygame modules that might cause issues in testing
        m.setattr("pygame", MagicMock())
        m.setattr("pygame.font", MagicMock())
        m.setattr("pygame.display", MagicMock())
        m.setattr("pygame.transform", MagicMock())
        m.setattr("pygame.Surface", MagicMock())
        m.setattr("pygame.Rect", MagicMock)
        m.setattr("pygame.Vector2", MagicMock)
        m.setattr("pygame.mouse", MagicMock())
        m.setattr("pygame.event", MagicMock())

        # Mock pygame constants
        m.setattr("pygame", "MOUSEBUTTONDOWN", 1)
        m.setattr("pygame", "MOUSEBUTTONUP", 0)
        m.setattr("pygame", "K_LEFT", 276)
        m.setattr("pygame", "K_RIGHT", 275)
        m.setattr("pygame", "K_RETURN", 13)
        m.setattr("pygame", "SRCALPHA", 32)

        yield


# Common mock fixtures
@pytest.fixture
def mock_draw_manager():
    """Mock for DrawManager with common methods."""
    draw_manager = MagicMock()
    draw_manager.queue_draw = MagicMock()
    draw_manager.draw = MagicMock()
    return draw_manager


@pytest.fixture
def mock_input_manager():
    """Mock for InputManager with action system."""
    input_manager = MagicMock()
    input_manager.action_pressed.return_value = False
    input_manager.action_released.return_value = False
    input_manager.action_held.return_value = False
    input_manager.get_normalized_move.return_value = (0, 0)
    return input_manager


@pytest.fixture
def mock_event_manager():
    """Mock for EventManager."""
    event_manager = MagicMock()
    event_manager.subscribe = MagicMock()
    event_manager.dispatch = MagicMock()
    event_manager.unsubscribe = MagicMock()
    return event_manager


# Test utilities
def create_mock_surface(width=50, height=50):
    """Create a mock pygame.Surface with common methods."""
    surface = MagicMock()
    surface.get_width.return_value = width
    surface.get_height.return_value = height
    surface.get_rect.return_value = MagicMock(x=0, y=0, width=width, height=height)
    surface.center = (width // 2, height // 2)
    surface.centerx = width // 2
    surface.centery = height // 2
    return surface


def create_mock_rect(x=0, y=0, width=50, height=50):
    """Create a mock pygame.Rect with common properties."""
    rect = MagicMock()
    rect.x = x
    rect.y = y
    rect.width = width
    rect.height = height
    rect.center = (x + width // 2, y + height // 2)
    rect.centerx = x + width // 2
    rect.centery = y + height // 2
    rect.collidepoint = lambda point: (
        x <= point[0] <= x + width and y <= point[1] <= y + height
    )
    return rect


# Pytest configuration
def pytest_configure(config):
    """Custom pytest configuration."""
    # Add custom markers
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "unit: marks tests as unit tests")
    config.addinivalue_line("markers", "regression: marks tests as regression tests")


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers automatically."""
    for item in items:
        # Add unit marker to files in test_*.py
        if "test_" in item.nodeid and "integration" not in item.nodeid:
            item.add_marker(pytest.mark.unit)

        # Add regression marker to tests that verify existing functionality
        if "regression" in item.nodeid or "test_" in item.nodeid:
            item.add_marker(pytest.mark.regression)
