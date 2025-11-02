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
│  │   ├─ __init__.py
│  │   ├─ game_loop.py
│  │   ├─ settings.py
│  │   │
│  │   ├─ engine/
│  │   │   ├─ __init__.py
│  │   │   ├─ display_manager.py
│  │   │   ├─ input_manager.py
│  │   │   └─ scene_manager.py
│  │   │
│  │   └─ utils/
│  │       ├─ __init__.py
│  │       └─ debug_logger.py
│  │
│  ├─ entities/
│  │   ├─ __init__.py
│  │   └─ player.py
│  │
│  ├─ graphics/
│  │   ├─ __init__.py
│  │   └─ draw_manager.py
│  │
│  ├─ scenes/
│  │   ├─ __init__.py
│  │   ├─ game_scene.py
│  │   ├─ pause_scene.py
│  │   └─ start_scene.py
│  │
│  ├─ systems/
│  │   ├─ __init__.py
│  │   ├─ collision_manager.py
│  │   ├─ sound_manager.py
│  │   └─ spawn_manager.py
│  │
│  └─ ui/
│      ├─ __init__.py
│      │
│      ├─ effects/
│      │  ├─ __init__.py - null
│      │  ├─ ui_animation.py - null
│      │  └─ ui_fade.py - null
│      │
│      ├─ subsystems/
│      │  ├─ __init__.py - null
│      │  ├─ debug_hud.py
│      │  ├─ hud_manager.py
│      │  └─ menu_manager.py - null
│      │
│      ├─ __init__.py
│      ├─ button.py
│      ├─ ui_element.py
│      └─ ui_manager.py
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
