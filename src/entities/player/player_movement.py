"""
player_movement.py
------------------
Handles all player movement, acceleration, and screen-boundary logic.

Responsibilities
----------------
- Translate input direction into acceleration and velocity.
- Apply smooth damping (friction) when no input is active.
- Clamp player position and velocity to the visible screen area.
"""

import pygame
from src.core.runtime.game_settings import Display

VELOCITY_SMOOTHING_RATE = 8.0

def update_movement(player, dt):
    """
    Update the player's velocity and position based on directional input.

    Args:
        player (Player): The player instance being updated.
        dt (float): Delta time since the last frame (in seconds).
    """

    move_vec = player.input.move()

    # -------------------------------------------------------
    # Retrieve movement parameters from config
    # -------------------------------------------------------
    core = player.cfg["core_attributes"]
    accel_rate = core["accel_rate"]
    friction_rate = core["friction_rate"]
    max_speed_mult = core["max_speed_mult"]

    # -------------------------------------------------------
    # Movement input active
    # -------------------------------------------------------
    move_len_sq = move_vec.length_squared()
    if move_len_sq > 0:
        # Normalize input and compute target velocity
        move_vec = move_vec.normalize()
        desired_velocity = move_vec * player.speed

        smoothing_factor = VELOCITY_SMOOTHING_RATE * dt

        # Smoothly interpolate toward desired velocity
        player.velocity = player.velocity.lerp(desired_velocity, smoothing_factor)

        # Apply acceleration to build up momentum
        player.velocity += move_vec * accel_rate * dt

        # Limit top speed
        vel_len_sq = player.velocity.length_squared()
        max_speed = player.speed * max_speed_mult
        max_speed_sq = max_speed ** 2
        if vel_len_sq > max_speed_sq:
            player.velocity.scale_to_length(max_speed)

    # -------------------------------------------------------
    # No movement input — apply friction
    # -------------------------------------------------------
    else:
        current_speed = player.velocity.length()
        if current_speed > 0:
            new_speed = max(0.0, current_speed - friction_rate * dt)

            # Stop completely when almost stationary
            if new_speed < 5.0:
                player.velocity.xy = (0, 0)
            else:
                player.velocity.scale_to_length(new_speed)

    # -------------------------------------------------------
    # Update position and constrain within screen bounds
    # -------------------------------------------------------
    player.pos += player.velocity * dt
    # Update virtual position (unclamped) for background parallax
    velocity_for_bg = player.velocity.copy()
    player.virtual_pos += velocity_for_bg * dt

    clamp_to_screen(player)

    # Apply parallax boost if pushing against edges (NEW SECTION)
    EDGE_PARALLAX_BOOST = 2.5  # Multiplier when clamped

    if player.clamped_x and move_vec.x != 0:  # Still trying to move horizontally
        boost_amount = move_vec.x * player.speed * (EDGE_PARALLAX_BOOST - 1) * dt
        player.virtual_pos.x += boost_amount

    if player.clamped_y and move_vec.y != 0:  # Still trying to move vertically
        boost_amount = move_vec.y * player.speed * (EDGE_PARALLAX_BOOST - 1) * dt
        player.virtual_pos.y += boost_amount

    # Sync render rectangle to updated position
    player.sync_rect()


def clamp_to_screen(player):
    screen_w, screen_h = Display.WIDTH, Display.HEIGHT
    half_w = player.rect.width * 0.5
    half_h = player.rect.height * 0.5

    SOFT_MARGIN = 30  # pixels from edge (tune to taste)

    old_x, old_y = player.pos.x, player.pos.y

    # Clamp position with soft margins
    player.pos.x = max(half_w + SOFT_MARGIN, min(player.pos.x, screen_w - half_w - SOFT_MARGIN))
    player.pos.y = max(half_h + SOFT_MARGIN, min(player.pos.y, screen_h - half_h - SOFT_MARGIN))

    # Track which edges are clamped (NEW)
    player.clamped_x = (player.pos.x != old_x)
    player.clamped_y = (player.pos.y != old_y)

    # Stop velocity if clamping occurred
    if player.pos.x != old_x:
        player.velocity.x = 0
    if player.pos.y != old_y:
        player.velocity.y = 0
