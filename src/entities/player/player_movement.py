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
from src.core.game_settings import Display


def update_movement(player, dt, move_vec):
    """
    Update the player's velocity and position based on directional input.

    Args:
        player (Player): The player instance being updated.
        dt (float): Delta time since the last frame (in seconds).
        move_vec (pygame.Vector2): Directional input vector.
    """
    # -------------------------------------------------------
    # Tuning parameters
    # -------------------------------------------------------
    accel_rate = 3000       # Acceleration factor (higher = more responsive)
    friction_rate = 500     # Deceleration factor when no input
    max_speed_mult = 1.8    # Cap multiplier relative to base speed

    # -------------------------------------------------------
    # Movement input active
    # -------------------------------------------------------
    if move_vec.length_squared() > 0:
        # Normalize input and compute target velocity
        move_vec = move_vec.normalize()
        desired_velocity = move_vec * player.speed

        # Smoothly interpolate toward desired velocity
        player.velocity = player.velocity.lerp(desired_velocity, 0.25)

        # Apply acceleration to build up momentum
        player.velocity += move_vec * accel_rate * dt

        # Limit top speed
        max_speed = player.speed * max_speed_mult
        if player.velocity.length() > max_speed:
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
    clamp_to_screen(player)

    # Sync render rectangle to updated position
    player.rect.center  = (int(player.pos.x), int(player.pos.y))


def clamp_to_screen(player):
    """
    Prevent the player from leaving the visible screen area.
    If the player hits the border, their velocity on that axis is reset to zero.

    Args:
        player (Player): The player instance to clamp.
    """
    screen_w, screen_h = Display.WIDTH, Display.HEIGHT

    # Constrain position within boundaries
    player.pos.x = max(0.0, min(player.pos.x, screen_w - player.rect.width))
    player.pos.y = max(0.0, min(player.pos.y, screen_h - player.rect.height))

    # Stop velocity if hitting screen edge
    if player.pos.x in (0, screen_w - player.rect.width):
        player.velocity.x = 0
    if player.pos.y in (0, screen_h - player.rect.height):
        player.velocity.y = 0
