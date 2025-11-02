"""
hud_manager.py
---------------
Temporary placeholder for the HUDManager system.
Used to satisfy imports during development.

Responsibilities (when implemented later):
- Manage in-game overlays (health bar, score, ammo, etc.)
- Handle temporary UI like damage flashes or debug HUD.
- Interface with UIManager for rendering.

NOTE:
This is a stub implementation for now and does nothing.
"""

class HUDManager:
    """Empty placeholder HUDManager for development builds."""

    def __init__(self, *args, **kwargs):
        print("[INFO] HUDManager: placeholder active (no HUD loaded).")

    def update(self, mouse_pos):
        pass

    def handle_event(self, event):
        return None

    def draw(self, draw_manager):
        pass
