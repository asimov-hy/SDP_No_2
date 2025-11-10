"""
player_logic.py
---------------
Implements non-core player behavior and state transitions.

Responsibilities
----------------
- Manage health, damage, and death cleanup.
- Control invulnerability (i-frames) and interaction state logic.
- Update player visuals (sprite or color) based on current health.
- Remain independent of initialization and core setup.
"""

import pygame
from src.core.utils.debug_logger import DebugLogger
from .player_config import PLAYER_CONFIG
from .player_state import InteractionState

# ===========================================================
# Combat & Damage Handling
# ===========================================================
def take_damage(self, amount: int):
    """
    Apply incoming damage to the player and refresh visuals.

    Args:
        amount (int): Amount of health to reduce.
    """
    self.health = max(0, self.health - amount)
    update_visual_state(self)

    if self.health <= 0:
        # Death handling
        DebugLogger.state(f"Player took {amount} damage → Player destroyed!", category="damage")
        on_death(self)
    else:
        # Trigger i-frame logic (intangible + visual feedback)
        DebugLogger.state(f"Player took {amount} damage → HP={self.health}", category="damage")
        if hasattr(self, "start_iframes"):
            self.start_iframes()


def on_death(self):
    """Handle cleanup and deactivation when the player dies."""
    if not self.alive:
        return  # Prevent double calls

    self.alive = False
    # self.visible = False

    if self.hitbox:
        self.hitbox.active = False
        self.hitbox = None

    if getattr(self, "animation_manager", None):
        self.animation_manager.stop()
        self.animation_manager.enabled = False

    from src.core.game_state import STATE
    STATE.player_ref = None

    DebugLogger.state("Player on_death() cleanup complete", category="state")


# ===========================================================
# Visual Update Logic
# ===========================================================
def update_visual_state(self):
    """
    Update the player’s sprite or color based on current health.
    Triggered after taking damage or healing.

    Changes are determined by the thresholds defined in `player_config.py`.
    """
    hp = self.health
    th = self.health_thresholds
    mode = self.render_mode
    state = "normal"  # Default threshold name
    visual_value = None

    # -------------------------------------------------------
    # IMAGE MODE
    # -------------------------------------------------------
    if mode == "image":
        state = (
            "damaged_critical" if hp <= th["critical"]
            else "damaged_moderate" if hp <= th["moderate"]
            else "normal"
        )

        path = self.image_states[state]
        visual_value = path

        try:
            new_image = pygame.image.load(path).convert_alpha()
            new_image = pygame.transform.scale(new_image, PLAYER_CONFIG["size"])
            self.image = new_image
        except Exception as e:
            DebugLogger.warn(f"Failed to load sprite: {path} ({e})")

    # -------------------------------------------------------
    # SHAPE MODE
    # -------------------------------------------------------
    elif mode == "shape":
        if hp <= th["critical"]:
            state = "damaged_critical"
        elif hp <= th["moderate"]:
            state = "damaged_moderate"

        self.color = self.color_states[state]
        visual_value = self.color

    # -------------------------------------------------------
    # Unified Debug Output
    # -------------------------------------------------------
    DebugLogger.state(
        f"Mode={mode} | HP={hp} | Threshold={state} | Visual={visual_value}",
        category="effects"
    )


# ===========================================================
# Interaction State Management
# ===========================================================
def set_interaction_state(self, state: InteractionState | int):
    """
    Set the player's current interaction state using a numeric hierarchy.

    State Levels:
      0 -> DEFAULT      damage: O   enemy collision: O   environment: O
      1 -> INVINCIBLE   damage: X   enemy collision: O   environment: O
      2 -> INTANGIBLE   damage: X   enemy collision: X   environment: O
      3 -> CLIP_THROUGH damage: X   enemy collision: X   environment: X

    Behavior Rules:
        - Hitbox active if state < 3
        - Collides with environment if state < 3
        - Collides with enemies if state < 2

    Args:
        state (InteractionState | int): The desired interaction state,
            either as an InteractionState enum member or an integer value (0–3).
    """
    # -------------------------------------------------------
    # Normalize input to InteractionState enum
    # -------------------------------------------------------
    if isinstance(state, int):
        try:
            state = InteractionState(state)
        except ValueError:
            DebugLogger.warn(f"Invalid interaction state value: {state}")
            state = InteractionState.DEFAULT

    self.state = state
    level = state.value

    # -------------------------------------------------------
    # Apply collision rules
    # -------------------------------------------------------
    if self.hitbox:
        self.hitbox.active = level < 3
        self.hitbox.collides_with_environment = level < 3
        self.hitbox.collides_with_enemies = level < 2

    DebugLogger.state(f"InteractionState → {state.name} ({level})", category="state")
