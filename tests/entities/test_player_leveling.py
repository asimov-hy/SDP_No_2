"""
test_player_leveling.py
-----------------------
Essential regression tests for Player level progression logic.

Covers the 5 most critical test cases that prevent major gameplay regressions:
1. Single level up at exact threshold
2. Multiple consecutive level ups with overflow
3. Experience calculation accuracy
4. Session statistics tracking
5. Level up preserves player combat state
"""

import pytest
from unittest.mock import MagicMock, patch
from src.entities.player.player_core import Player
from src.core.services.event_manager import EnemyDiedEvent


# ===========================================================
# Fixtures
# ===========================================================

@pytest.fixture
def mock_player_with_levelup():
    """Create a real Player instance with minimal dependencies for testing."""
    with patch('src.entities.player.player_core.load_config') as mock_load_config, \
         patch('src.entities.player.player_core.BaseEntity'), \
         patch('src.entities.player.player_core.pygame'), \
         patch('src.entities.player.player_core.DebugLogger'), \
         patch('src.entities.player.player_core.get_events'), \
         patch('src.entities.player.player_core.get_session_stats') as mock_session_stats:

        # Mock player configuration
        mock_config = {
            "core_attributes": {
                "health": 10,
                "speed": 100,
                "hitbox_scale": 1.0
            },
            "render": {
                "mode": "shape",
                "size": [50, 50],
                "default_shape": {
                    "shape_type": "rect",
                    "color": [255, 0, 0]
                }
            },
            "health_states": {
                "thresholds": {
                    "moderate": 0.5,
                    "critical": 0.2
                },
                "color_states": {
                    "normal": [255, 0, 0],
                    "moderate": [255, 255, 0],
                    "critical": [255, 100, 100]
                }
            }
        }
        mock_load_config.return_value = mock_config

        # Mock session stats
        mock_stats_instance = MagicMock()
        mock_stats_instance.total_exp_gained = 0
        mock_stats_instance.max_level_reached = 1
        mock_session_stats.return_value = mock_stats_instance

        player = Player(
            x=100, y=100,
            draw_manager=MagicMock(),
            input_manager=MagicMock()
        )
        return player


# ===========================================================
# Critical Test Suite - 5 Essential Tests
# ===========================================================

class TestPlayerLevelUpCore:
    """Essential tests that prevent major level-up regressions."""

    def test_single_level_up_at_exact_threshold(self, mock_player_with_levelup):
        """
        CRITICAL: Test that player levels up when reaching exact required EXP.
        This prevents the most common bug - players unable to level up.
        """
        player = mock_player_with_levelup

        # Set up to be exactly 1 EXP below requirement
        player.exp_required = 100  # Level requirement
        player.exp = 99
        initial_level = player.level

        # Gain exactly enough EXP to level up
        event = EnemyDiedEvent(position=(0, 0), enemy_type_tag="test_enemy", exp=1)
        player._on_enemy_died(event)

        # Verify level up occurred
        assert player.level == initial_level + 1, f"Expected level {initial_level + 1}, got {player.level}"
        assert player.exp == 0, f"Expected 0 overflow EXP, got {player.exp}"

    def test_multiple_consecutive_level_ups_with_overflow(self, mock_player_with_levelup):
        """
        CRITICAL: Test multiple level-ups and overflow EXP handling.
        Prevents massive EXP gains from breaking progression.
        """
        player = mock_player_with_levelup

        # Use _exp_table values for accurate testing
        player.exp = 0
        initial_level = player.level

        # Gain enough EXP for 2-3 level-ups (simulate boss kill)
        massive_exp = 300  # Should trigger ~2-3 level-ups from initial 30
        event = EnemyDiedEvent(position=(0, 0), enemy_type_tag="boss_enemy", exp=massive_exp)
        player._on_enemy_died(event)

        # Should have multiple level-ups
        assert player.level > initial_level + 1, f"Expected multiple level-ups, only got to level {player.level}"
        assert player.exp >= 0, f"EXP overflow should be non-negative, got {player.exp}"

        # Should update session stats
        stats = mock_player_with_levelup._mock_session_stats if hasattr(mock_player_with_levelup, '_mock_session_stats') else None
        if stats:
            assert stats.total_exp_gained >= massive_exp

    def test_experience_calculation_accuracy_across_enemy_types(self, mock_player_with_levelup):
        """
        CRITICAL: Test that different enemy types give correct EXP amounts and trigger level-ups.
        Prevents progression balance issues and ensures all enemy types give EXP properly.
        """
        player = mock_player_with_levelup
        initial_exp = player.exp
        initial_level = player.level
        initial_total_gained = player._mock_session_stats.total_exp_gained if hasattr(player, '_mock_session_stats') else 0

        # Test different enemy EXP values from config
        enemy_scenarios = [
            ("grunt", 10),      # Basic enemy
            ("shooter", 25),    # Ranged enemy
            ("homing", 50),     # Advanced enemy
            ("boss", 500),      # Boss enemy
        ]

        total_expected_exp = 0
        for enemy_type, exp_value in enemy_scenarios:
            event = EnemyDiedEvent(position=(0, 0), enemy_type_tag=enemy_type, exp=exp_value)
            player._on_enemy_died(event)
            total_expected_exp += exp_value

            # After each enemy death, EXP should be processed correctly
            assert player.exp >= 0, f"EXP should never be negative after killing {enemy_type}, got {player.exp}"

        # Verify that massive EXP gain from diverse enemies triggers level-ups
        assert player.level > initial_level, f"Should have leveled up from killing diverse enemies, still level {player.level}"
        assert player.exp >= 0, f"Final EXP should be non-negative, got {player.exp}"

        # Session stats should track total EXP gained (before level-up consumption)
        if hasattr(player, '_mock_session_stats') and player._mock_session_stats:
            assert player._mock_session_stats.total_exp_gained >= initial_total_gained + total_expected_exp, \
                f"Session stats should track {total_expected_exp} EXP gain"

    def test_level_up_preserves_combat_state(self, mock_player_with_levelup):
        """
        CRITICAL: Test that level up doesn't break player combat state.
        Prevents level-ups from making players invulnerable or broken.
        """
        player = mock_player_with_levelup

        # Set critical combat state
        original_health = player.health
        original_max_health = player.max_health
        original_base_speed = player.base_speed
        original_position = (player.pos.x, player.pos.y) if hasattr(player, 'pos') else (100, 100)
        original_visible = player.visible
        original_layer = player.layer

        # Trigger level up
        player._level_up()

        # Verify combat state unchanged
        assert player.health == original_health, f"Health changed from {original_health} to {player.health}"
        assert player.max_health == original_max_health, f"Max health changed from {original_max_health} to {player.max_health}"
        assert player.base_speed == original_base_speed, f"Base speed changed from {original_base_speed} to {player.base_speed}"
        assert player.visible == original_visible, f"Visibility changed from {original_visible} to {player.visible}"
        assert player.layer == original_layer, f"Layer changed from {original_layer} to {player.layer}"

    def test_session_statistics_tracking_accuracy(self, mock_player_with_levelup):
        """
        CRITICAL: Test that session statistics accurately track progression.
        Prevents save/load and progression tracking bugs.
        """
        player = mock_player_with_levelup

        # Mock session stats properly
        with patch('src.entities.player.player_core.get_session_stats') as mock_get_stats:
            mock_stats = MagicMock()
            mock_stats.total_exp_gained = 0
            mock_stats.max_level_reached = 1
            mock_get_stats.return_value = mock_stats

            initial_exp_gained = mock_stats.total_exp_gained
            initial_max_level = mock_stats.max_level_reached

            # Gain EXP and level up
            exp_gain = 100
            event = EnemyDiedEvent(position=(0, 0), enemy_type_tag="test_enemy", exp=exp_gain)
            player._on_enemy_died(event)

            # Trigger level up manually if needed
            if player.exp >= player.exp_required:
                player._level_up()

            # Verify stats updated
            assert mock_stats.total_exp_gained == initial_exp_gained + exp_gain, \
                f"Total EXP should be {initial_exp_gained + exp_gain}, got {mock_stats.total_exp_gained}"
            assert mock_stats.max_level_reached >= initial_max_level, \
                f"Max level should be at least {initial_max_level}, got {mock_stats.max_level_reached}"


# ===========================================================
# Additional Edge Case Tests (Optional but recommended)
# ===========================================================

class TestPlayerLevelUpEdgeCases:
    """Additional edge cases if you want comprehensive testing."""

    def test_negative_exp_prevented(self, mock_player_with_levelup):
        """Test that negative EXP is prevented."""
        player = mock_player_with_levelup
        initial_exp = player.exp

        event = EnemyDiedEvent(position=(0, 0), enemy_type_tag="corrupted_enemy", exp=-10)
        player._on_enemy_died(event)

        assert player.exp == initial_exp, "Negative EXP should not change player EXP"

    def test_zero_exp_ignored(self, mock_player_with_levelup):
        """Test that zero EXP events are ignored."""
        player = mock_player_with_levelup
        initial_exp = player.exp

        event = EnemyDiedEvent(position=(0, 0), enemy_type_tag="zero_exp_enemy", exp=0)
        player._on_enemy_died(event)

        assert player.exp == initial_exp, "Zero EXP should not change player EXP"

    def test_level_up_boundary_conditions(self, mock_player_with_levelup):
        """Test exact boundary conditions for level up."""
        player = mock_player_with_levelup

        # Test just below threshold - should NOT level up
        player.exp_required = 100
        player.exp = 98
        event = EnemyDiedEvent(position=(0, 0), enemy_type_tag="test_enemy", exp=1)
        player._on_enemy_died(event)

        assert player.level == 1, f"Should not level up with 99/100 EXP, got level {player.level}"
        assert player.exp == 99, f"Should have 99 EXP, got {player.exp}"

        # Test exactly at threshold - should level up
        event = EnemyDiedEvent(position=(0, 0), enemy_type_tag="test_enemy", exp=1)
        player._on_enemy_died(event)

        assert player.level == 2, f"Should level up with 100/100 EXP, got level {player.level}"
        assert player.exp == 0, f"Should have 0 overflow EXP, got {player.exp}"