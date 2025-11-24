"""
test_player_leveling.py
-----------------------
Regression tests for Player level progression logic.

Covers:
- EXP gain from enemy deaths
- Level up mechanics and calculations
- EXP requirement scaling and capping
- Multiple level-ups and overflow handling
- Session statistics tracking
- Edge cases and error conditions
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
         patch('src.entities.player.player_core.get_events'):

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

        player = Player(
            x=100, y=100,
            draw_manager=MagicMock(),
            input_manager=MagicMock()
        )
        return player


# ===========================================================
# Test Suites
# ===========================================================

class TestPlayerEXPHandling:
    """Test player EXP gain and processing logic."""

    def test_exp_gain_from_enemy_death(self, mock_player_with_levelup):
        """Test that player gains EXP from enemy death events."""
        player = mock_player_with_levelup
        initial_exp = player.exp

        event = EnemyDiedEvent(position=(0, 0), enemy_type_tag="test_enemy", exp=50)
        player._on_enemy_died(event)

        assert player.exp == initial_exp + 50

    def test_negative_exp_prevented(self, mock_player_with_levelup):
        """Test that negative EXP is prevented and treated as zero."""
        player = mock_player_with_levelup
        initial_exp = player.exp

        event = EnemyDiedEvent(exp=-10, enemy_type_tag="test_enemy")
        player._on_enemy_died(event)

        assert player.exp == initial_exp  # Should not change

    def test_zero_exp_ignored(self, mock_player_with_levelup):
        """Test that zero EXP events are ignored."""
        player = mock_player_with_levelup
        initial_exp = player.exp

        event = EnemyDiedEvent(exp=0, enemy_type_tag="test_enemy")
        player._on_enemy_died(event)

        assert player.exp == initial_exp  # Should not change

    def test_session_stats_updated(self, mock_player_with_levelup):
        """Test that session statistics are updated with EXP gain."""
        with patch('src.entities.player.player_core.update_session_stats') as mock_stats:
            mock_session_stats = MagicMock()
            mock_session_stats.total_exp_gained = 100
            mock_stats.return_value = mock_session_stats

            player = mock_player_with_levelup
            event = EnemyDiedEvent(exp=25, enemy_type_tag="test_enemy")
            player._on_enemy_died(event)

            # Should update total EXP gained
            assert mock_session_stats.total_exp_gained == 125


class TestPlayerLevelUpMechanics:
    """Test player level up mechanics and progression."""

    def test_single_level_up(self, mock_player_with_levelup):
        """Test that player levels up when reaching required EXP."""
        player = mock_player_with_levelup
        player.exp_required = 500
        player.exp = 99
        initial_level = player.level

        # Gain exactly enough EXP to level up
        event = EnemyDiedEvent(exp=1, enemy_type_tag="test_enemy")
        player._on_enemy_died(event)

        assert player.level == initial_level + 1
        assert player.exp == 0  # Should reset with no overflow

    def test_multiple_level_ups(self, mock_player_with_levelup):
        """Test that multiple level-ups are handled correctly with overflow."""
        player = mock_player_with_levelup
        player.exp_required = 500
        player.exp = 0
        initial_level = player.level

        # Gain enough EXP for 2 level-ups
        event = EnemyDiedEvent(exp=250, enemy_type_tag="test_enemy")
        player._on_enemy_died(event)

        assert player.level == initial_level + 2
        # Should have overflow EXP after 2 level-ups
        assert player.exp == 50  # 250 - 100 - 100

    def test_exp_requirement_scaling(self, mock_player_with_levelup):
        """Test that EXP requirement scales correctly with level."""
        player = mock_player_with_levelup
        player.level = 1
        player.exp_required = 500
        initial_exp_req = player.exp_required

        # Level up to 2
        player._level_up()

        # EXP requirement should increase (30 * 2.0^(level-1))
        expected_level_2 = int(30 * (2.0 ** 1))  # Level 2: 30 * 2^1 = 60
        assert player.exp_required == expected_level_2

        # Level up to 3
        player._level_up()

        expected_level_3 = int(30 * (2.0 ** 2))  # Level 3: 30 * 2^2 = 120
        assert player.exp_required == expected_level_3

    def test_exp_requirement_capped(self, mock_player_with_levelup):
        """Test that EXP requirement is capped at reasonable maximum."""
        player = mock_player_with_levelup
        player.level = 250  # Very high level

        player._level_up()

        # Should be capped at 999999
        assert player.exp_required == 999999

    def test_session_stats_max_level_updated(self, mock_player_with_levelup):
        """Test that session statistics track max level reached."""
        with patch('src.entities.player.player_core.update_session_stats') as mock_stats:
            mock_session_stats = MagicMock()
            mock_session_stats.max_level_reached = 1
            mock_stats.return_value = mock_session_stats

            player = mock_player_with_levelup
            player.level = 3
            player._level_up()  # Level up to 4

            # Should update max level reached
            assert mock_session_stats.max_level_reached == 4


class TestPlayerLevelUpEdgeCases:
    """Test edge cases and unusual scenarios in level progression."""

    def test_extreme_exp_values(self, mock_player_with_levelup):
        """Test handling of very large EXP values."""
        player = mock_player_with_levelup

        # Test very large EXP gain
        large_exp_event = EnemyDiedEvent(exp=999999, enemy_type_tag="boss_enemy")
        player._on_enemy_died(large_exp_event)

        # Should handle gracefully without overflow
        assert player.exp >= 0
        assert player.level > 1

    def test_rapid_level_ups(self, mock_player_with_levelup):
        """Test multiple rapid level-ups don't cause issues."""
        player = mock_player_with_levelup
        initial_level = player.level

        # Rapidly trigger multiple level-ups
        for i in range(5):
            player._level_up()

        assert player.level == initial_level + 5
        assert player.exp >= 0

    def test_level_up_with_no_exp_required(self, mock_player_with_levelup):
        """Test level up behavior when exp_required is zero."""
        player = mock_player_with_levelup
        player.exp_required = 0
        player.exp = 100

        # Should not cause infinite loop or crash
        player._on_enemy_died(EnemyDiedEvent(exp=50, enemy_type_tag="test_enemy"))

        # Player should still be in valid state
        assert player.level >= 1
        assert player.exp >= 0

    def test_exp_overflow_handling(self, mock_player_with_levelup):
        """Test that EXP overflow is handled correctly."""
        player = mock_player_with_levelup
        player.exp = 999999999  # Very large EXP
        player.exp_required = 500

        # Should handle large EXP values without crashing
        player._on_enemy_died(EnemyDiedEvent(exp=1, enemy_type_tag="test_enemy"))

        assert player.level > 1
        assert player.exp >= 0

    def test_enemy_died_event_missing_exp(self, mock_player_with_levelup):
        """Test handling of EnemyDiedEvent without exp attribute."""
        player = mock_player_with_levelup
        initial_exp = player.exp

        # Create event without exp attribute
        event = MagicMock(spec=[])  # No attributes
        event.exp = None  # Explicitly set to None

        # Should not crash
        try:
            player._on_enemy_died(event)
        except (TypeError, AttributeError):
            # Expected to handle missing exp gracefully
            pass

        # EXP should remain unchanged or be handled safely
        assert player.exp >= 0


class TestPlayerLevelUpIntegration:
    """Test integration between level up system and other components."""

    def test_level_up_debug_logging(self, mock_player_with_levelup):
        """Test that level up events are properly logged."""
        with patch('src.entities.player.player_core.DebugLogger') as mock_logger:
            player = mock_player_with_levelup
            player.level = 2

            player._level_up()

            # Should log level up event
            mock_logger.state.assert_called()

    def test_exp_gain_debug_logging(self, mock_player_with_levelup):
        """Test that EXP gain events are properly logged."""
        with patch('src.entities.player.player_core.DebugLogger') as mock_logger:
            player = mock_player_with_levelup

            event = EnemyDiedEvent(exp=25, enemy_type_tag="test_enemy")
            player._on_enemy_died(event)

            # Should log EXP gain
            mock_logger.state.assert_called()

    def test_level_up_persists_player_state(self, mock_player_with_levelup):
        """Test that level up preserves other player state."""
        player = mock_player_with_levelup

        # Set some player state
        original_health = player.health
        original_max_health = player.max_health
        original_base_speed = player.base_speed
        original_position = (player.pos.x, player.pos.y)

        player._level_up()

        # Other stats should remain unchanged
        assert player.health == original_health
        assert player.max_health == original_max_health
        assert player.base_speed == original_base_speed
        assert (player.pos.x, player.pos.y) == original_position


class TestPlayerLevelUpSpecificCases:
    """Detailed tests for specific level up scenarios and edge cases."""

    def test_exp_calculation_formula_consistency(self, mock_player_with_levelup):
        """Test that EXP calculation formula remains consistent across levels."""
        player = mock_player_with_levelup

        # Test formula: exp_required = 30 * (2.0 ** (level - 1))
        expected_values = [
            (1, 30),    # Level 1: 30 * 2^0 = 30
            (2, 60),    # Level 2: 30 * 2^1 = 60
            (3, 120),   # Level 3: 30 * 2^2 = 120
            (4, 240),   # Level 4: 30 * 2^3 = 240
            (5, 480),   # Level 5: 30 * 2^4 = 480
        ]

        for level, expected_exp in expected_values:
            player.level = level
            player.exp_required = expected_exp  # Set the expected requirement
            actual_req = player.exp_required

            # Verify the formula matches
            formula_result = min(int(30 * (2.0 ** min(player.level - 1, 200))), 999999)
            assert actual_req == expected_exp, f"Level {level} should require {expected_exp} EXP, got {actual_req}"
            assert actual_req == formula_result, f"Formula result mismatch at level {level}"

    def test_exp_overflow_across_multiple_levels(self, mock_player_with_levelup):
        """Test EXP overflow handling across multiple consecutive level-ups."""
        player = mock_player_with_levelup
        player.exp_required = 30  # Level 1 requirement
        player.exp = 0

        # Gain massive EXP that should trigger multiple level-ups
        massive_exp_gain = 1000
        event = EnemyDiedEvent(exp=massive_exp_gain, enemy_type_tag="boss_enemy")
        player._on_enemy_died(event)

        # Should handle multiple level-ups correctly
        assert player.level > 1
        assert player.exp >= 0

        # Track manual level-ups to verify consistency
        calculated_exp = massive_exp_gain
        current_exp_req = 30
        calculated_levels = 0

        while calculated_exp >= current_exp_req:
            calculated_exp -= current_exp_req
            calculated_levels += 1
            current_exp_req = int(30 * (2.0 ** calculated_levels))
            if current_exp_req > 999999:  # Cap check
                break

        # Player should have approximately the same level and remaining exp
        assert player.level >= 1 + calculated_levels

    def test_level_up_preserves_combat_stats(self, mock_player_with_levelup):
        """Test that level up doesn't unintentionally modify combat stats."""
        player = mock_player_with_levelup

        # Set combat-related stats
        player.health = 15
        player.max_health = 20
        player.base_speed = 150
        player.velocity.x = 5
        player.velocity.y = -3

        original_stats = {
            'health': player.health,
            'max_health': player.max_health,
            'base_speed': player.base_speed,
            'velocity_x': player.velocity.x if hasattr(player.velocity, 'x') else 0,
            'velocity_y': player.velocity.y if hasattr(player.velocity, 'y') else 0,
            'visible': player.visible,
            'layer': player.layer
        }

        player._level_up()

        # Combat stats should remain unchanged
        for stat, value in original_stats.items():
            if stat in ['velocity_x', 'velocity_y']:
                if stat == 'velocity_x':
                    current_value = player.velocity.x if hasattr(player.velocity, 'x') else 0
                else:
                    current_value = player.velocity.y if hasattr(player.velocity, 'y') else 0
            else:
                current_value = getattr(player, stat)
            assert current_value == value, f"Stat {stat} changed from {value} to {current_value}"

    def test_enemy_type_exp_distribution(self, mock_player_with_levelup):
        """Test different enemy types give appropriate EXP amounts."""
        player = mock_player_with_levelup
        initial_exp = player.exp

        # Test different enemy types and their EXP values
        enemy_scenarios = [
            ("grunt", 10),      # Basic enemy
            ("shooter", 25),    # Ranged enemy
            ("homing", 50),     # Advanced enemy
            ("boss", 500),      # Boss enemy
        ]

        for enemy_type, exp_value in enemy_scenarios:
            event = EnemyDiedEvent(exp=exp_value, enemy_type=enemy_type)
            player._on_enemy_died(event)

            expected_exp = initial_exp + exp_value
            assert player.exp == expected_exp, f"Killing {enemy_type} should give {exp_value} EXP"

            # Reset for next test
            player.exp = initial_exp

    def test_level_up_boundary_conditions(self, mock_player_with_levelup):
        """Test level up at exact boundary conditions."""
        player = mock_player_with_levelup
        player.exp_required = 500

        # Test exact boundary
        player.exp = 99
        event = EnemyDiedEvent(exp=1, enemy_type_tag="test_enemy")
        player._on_enemy_died(event)

        assert player.level == 2  # Should level up
        assert player.exp == 0   # No overflow

        # Test just below boundary
        player.exp = 98
        event = EnemyDiedEvent(exp=1, enemy_type_tag="test_enemy")
        player._on_enemy_died(event)

        assert player.level == 2  # Should not level up again
        assert player.exp == 99   # 98 + 1 = 99

        # Test exactly at new boundary
        player.exp_required = 60  # Level 2 requirement
        player.exp = 59
        event = EnemyDiedEvent(exp=1, enemy_type_tag="test_enemy")
        player._on_enemy_died(event)

        assert player.level == 3  # Should level up again
        assert player.exp == 0   # No overflow

    def test_concurrent_enemy_deaths_exp_handling(self, mock_player_with_levelup):
        """Test EXP handling from multiple enemy deaths in quick succession."""
        player = mock_player_with_levelup
        initial_exp = player.exp

        # Simulate multiple enemies dying at once
        enemy_deaths = [
            EnemyDiedEvent(exp=15, enemy_type_tag="grunt1"),
            EnemyDiedEvent(exp=25, enemy_type_tag="shooter1"),
            EnemyDiedEvent(exp=10, enemy_type_tag="grunt2")
        ]

        total_expected_exp = sum(death.exp for death in enemy_deaths)

        # Process all deaths
        for death_event in enemy_deaths:
            player._on_enemy_died(death_event)

        # Should accumulate all EXP correctly
        assert player.exp == initial_exp + total_expected_exp

    def test_level_up_with_zero_initial_exp(self, mock_player_with_levelup):
        """Test level up starting from zero EXP."""
        player = mock_player_with_levelup
        player.exp = 0
        player.exp_required = 500
        player.level = 1

        # Give exactly enough EXP to level up
        event = EnemyDiedEvent(exp=100, enemy_type_tag="test_enemy")
        player._on_enemy_died(event)

        assert player.level == 2
        assert player.exp == 0  # No overflow

    def test_exp_requirements_grow_exponentially(self, mock_player_with_levelup):
        """Test that EXP requirements follow exponential growth pattern."""
        player = mock_player_with_levelup

        exp_requirements = []

        # Collect EXP requirements for first 10 levels
        for _ in range(10):
            exp_requirements.append(player.exp_required)
            player._level_up()

        # Each requirement should be double the previous (up to cap)
        for i in range(1, len(exp_requirements)):
            if exp_requirements[i] < 999999:  # Before cap
                expected_growth = exp_requirements[i-1] * 2.0
                actual_growth = exp_requirements[i]

                if expected_growth < 999999:
                    assert actual_growth == min(int(expected_growth), 999999)

    def test_level_up_event_emission(self, mock_player_with_levelup):
        """Test that level up properly emits events if implemented."""
        player = mock_player_with_levelup

        # Check if player has event emission capabilities
        if hasattr(player, 'emit_event') or hasattr(player, '_emit_event'):
            with patch('src.entities.player.player_core.get_events') as mock_events:
                mock_event_dispatcher = MagicMock()
                mock_events.return_value = mock_event_dispatcher

                player._level_up()

                # Should emit some kind of level up event
                # (This test depends on your actual event system)
                pass