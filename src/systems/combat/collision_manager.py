"""
collision_manager.py
--------------------
Optimized modular collision handler.
Uses spatial hashing to reduce redundant collision checks
and delegates actual responses to entities and bullets.

Responsibilities
----------------
- Detect collisions between bullets ↔ entities.
- Delegate behavior to bullet.on_hit() or entity.on_collision().
- Support collision rules for flexible filtering.
- Provide optional hitbox debug visualization and profiling.
"""

from src.core.game_settings import Debug
from src.core.utils.debug_logger import DebugLogger


class CollisionManager:
    """Detects collisions but lets objects decide what happens."""

    # ===========================================================
    # Configuration
    # ===========================================================
    BASE_CELL_SIZE = 64

    # ===========================================================
    # Initialization
    # ===========================================================
    def __init__(self, player, bullet_manager, spawn_manager):
        """
        Initialize the collision manager and register key systems.

        Args:
            player: Player entity instance to include in collision checks.
            bullet_manager: Reference to the BulletManager containing active bullets.
            spawn_manager: Reference to the SpawnManager containing active enemies.
        """
        self.player = player
        self.bullet_manager = bullet_manager
        self.spawn_manager = spawn_manager
        self.CELL_SIZE = self.BASE_CELL_SIZE

        self.rules = {
            ("player", "enemy"),
            ("player_bullet", "enemy"),
            ("enemy_bullet", "player"),
        }

        DebugLogger.init("Collision system initialized")

    # ===========================================================
    # Utility: Grid Assignment
    # ===========================================================
    def _add_to_grid(self, grid, obj):
        """
        Assign an entity to a grid cell based on its hitbox center.

        Args:
            grid (dict): Spatial hash table mapping cell → list of entities.
            obj: Any entity with a valid hitbox attribute.
        """
        hitbox = getattr(obj, "hitbox", None)
        if not hitbox:
            return

        rect = hitbox.rect
        start_x = int(rect.left // self.CELL_SIZE)
        end_x   = int(rect.right // self.CELL_SIZE)
        start_y = int(rect.top // self.CELL_SIZE)
        end_y   = int(rect.bottom // self.CELL_SIZE)

        for cx in range(start_x, end_x + 1):
            for cy in range(start_y, end_y + 1):
                grid.setdefault((cx, cy), []).append(obj)

    # ===========================================================
    # Optimized Collision Detection
    # ===========================================================
    def detect(self):
        """
        Optimized collision detection using spatial hashing.

        Groups entities by screen regions to minimize redundant checks.
        Delegates all responses to each entity’s `on_collision()` or `on_hit()`.

        Returns:
            list[tuple]: List of (object_a, object_b) pairs that have collided.
        """

        collisions = []

        # -------------------------------------------------------
        # Pre-filter active objects
        # -------------------------------------------------------
        active_bullets = [b for b in self.bullet_manager.active if b.alive]
        active_enemies = [e for e in self.spawn_manager.enemies if e.alive]
        player = self.player if self.player.alive else None

        total_entities = len(active_bullets) + len(active_enemies) + (1 if player else 0)
        if total_entities == 0:
            return collisions

        # -------------------------------------------------------
        # 2) Dynamic grid size adjustment
        # -------------------------------------------------------
        if total_entities > 800:
            self.CELL_SIZE = 48  # tighter grid for dense scenes
        elif total_entities < 100:
            self.CELL_SIZE = 96  # looser grid for sparse scenes
        else:
            self.CELL_SIZE = self.BASE_CELL_SIZE

        # -------------------------------------------------------
        # 3) Build Spatial Grid
        # -------------------------------------------------------
        grid = {}
        add_to_grid = self._add_to_grid  # micro-optimization (local ref)

        if player:
            add_to_grid(grid, player)
        for enemy in active_enemies:
            add_to_grid(grid, enemy)
        for bullet in active_bullets:
            add_to_grid(grid, bullet)

        # -------------------------------------------------------
        # 4) Localized Collision Checks (per cell + neighbors)
        # -------------------------------------------------------
        neighbor_offsets = [
            (0, 0), (1, 0), (-1, 0), (0, 1), (0, -1),
            (1, 1), (-1, 1), (1, -1), (-1, -1)
        ]

        checked_pairs = set()
        append_collision = collisions.append
        rules = self.rules
        get_hitbox = getattr
        get_tag = getattr

        for cell_key, cell_objects in grid.items():
            for dx, dy in neighbor_offsets:
                neighbor_key = (cell_key[0] + dx, cell_key[1] + dy)
                neighbor_objs = grid.get(neighbor_key)
                if not neighbor_objs:
                    continue

                for a in cell_objects:
                    a_hitbox = get_hitbox(a, "hitbox", None)
                    if not a_hitbox or not getattr(a_hitbox, "active", True):
                        continue

                    for b in neighbor_objs:
                        if a is b:
                            continue
                        b_hitbox = get_hitbox(b, "hitbox", None)
                        if not b_hitbox or not getattr(b_hitbox, "active", True):
                            continue

                        # Avoid redundant duplicate checks
                        pair_key = tuple(sorted((id(a), id(b))))
                        if pair_key in checked_pairs:
                            continue
                        checked_pairs.add(pair_key)

                        # Skip destroyed entities mid-frame
                        if not getattr(a, "alive", True) or not getattr(b, "alive", True):
                            continue

                        # Rule-based filtering
                        tag_a = get_tag(a, "collision_tag", None)
                        tag_b = get_tag(b, "collision_tag", None)
                        if (tag_a, tag_b) not in rules and (tag_b, tag_a) not in rules:
                            continue

                        # Perform overlap check
                        if a_hitbox.rect.colliderect(b_hitbox.rect):
                            append_collision((a, b))

                            # Unified, single collision header with tags
                            tag_a = getattr(a, "collision_tag", "?")
                            tag_b = getattr(b, "collision_tag", "?")
                            DebugLogger.state(
                                f"Collision: {type(a).__name__} ({tag_a}) <-> {type(b).__name__} ({tag_b})",
                                category="collision"
                            )

                            # Let entities handle their reactions
                            try:
                                if hasattr(a, "on_collision"):
                                    a.on_collision(b)

                                if hasattr(b, "on_collision"):
                                    b.on_collision(a)

                            except Exception as e:
                                DebugLogger.warn(
                                    f"[CollisionManager] Exception during collision between "
                                    f"{type(a).__name__} and {type(b).__name__}: {e}",
                                    category="collision"
                                )
        return collisions

    # ===========================================================
    # Debug Visualization
    # ===========================================================
    def draw_debug(self, surface):
        """
        Draw hitboxes for all entities if debug mode is enabled.

        Args:
            surface (pygame.Surface): The surface used for drawing hitboxes.
        """
        if not Debug.HITBOX_VISIBLE:
            return

        if getattr(self.player, "hitbox", None):
            self.player.hitbox.draw_debug(surface)

        for enemy in self.spawn_manager.enemies:
            if getattr(enemy, "hitbox", None):
                enemy.hitbox.draw_debug(surface)

        for bullet in self.bullet_manager.active:
            if getattr(bullet, "hitbox", None):
                bullet.hitbox.draw_debug(surface)
