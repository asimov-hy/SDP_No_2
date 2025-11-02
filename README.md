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
│  │   ├─ display_manager.py
│  │   ├─ game_loop.py
│  │   ├─ input_manager.py
│  │   ├─ scene_manager.py
│  │   └─ settings.py
│  │
│  ├─ graphics/
│  │   ├─ __init__.py
│  │   ├─ draw_manager.py
│  │   └─ effects.py
│  │
│  ├─ entities/
│  │   ├─ __init__.py
│  │   └─ player.py
│  │
│  ├─ systems/
│  │   ├─ collision_manager.py
│  │   ├─ spawn_manager.py
│  │   └─ sound_manager.py
│  │
│  └─ ui/
│      ├─ effects/
│      │  ├─ ui_animation.py - null
│      │  └─ ui_fade.py - null
│      ├─ subsystems/
│      ├─ button.py
│      ├─ hud_manager.py
│      ├─ menu_manager.py
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
