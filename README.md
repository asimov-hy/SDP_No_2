# SDP_No_2
Repository for Phase 2 of CSE2024 Software Development Practices

Team: No_1
Members

Project

Details:

file:

# VerticalShooter Project Structure

```
VerticalShooter/
│
├─ main.py
│
├─ src/
│  ├─ core/
│  │   ├─ game_loop.py
│  │   ├─ input_manager.py
│  │   ├─ scene_manager.py
│  │   └─ settings.py
│  │
│  ├─ graphics/
│  │   ├─ draw_manager.py
│  │   └─ effects.py
│  │
│  ├─ entities/
│  │   ├─ player.py
│  │   ├─ enemy.py
│  │   ├─ bullet.py
│  │   ├─ boss.py
│  │   └─ item.py
│  │
│  ├─ systems/
│  │   ├─ collision_manager.py
│  │   ├─ spawn_manager.py
│  │   └─ sound_manager.py
│  │
│  ├─ ui/
│  │   ├─ hud.py
│  │   ├─ menu.py
│  │   └─ game_over.py
│  │
│  └─ utils/
│      ├─ math_utils.py
│      ├─ resource_loader.py
│      └─ timer.py
│
├─ assets/
│  ├─ images/
│  │   ├─ player.png
│  │   ├─ enemies/
│  │   ├─ bullets/
│  │   └─ effects/
│  │
│  ├─ sounds/
│  │   ├─ shoot.wav
│  │   ├─ explosion.wav
│  │   └─ bgm.ogg
│  │
│  └─ fonts/
│      └─ arcade.ttf
│
└─ README.md
```
