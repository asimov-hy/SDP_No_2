# SDP_No_2
Repository for Phase 2 of CSE2024 Software Development Practices

Team: No_1
Members:
| Name | Role | Responsibilities |
|------|------|------------------|
| **Lim Kang Jun** | Team Leader / Scrum Master | Oversees project direction, manages sprints, ensures communication |
| **Jang Gi Jun** | Calendar Manager / Main Tester | Maintains project schedule, coordinates deadlines, performs primary testing |
| **Kim Min Chan** | Git Manager | Manages repository branches, handles version control, reviews PRs |
| **Lee Jun Myeong** | QA Manager | Oversees code quality, ensures testing coverage and documentation |
| **Jo In Jun** | Balance Designer | Adjusts gameplay balance, tuning difficulty and progression |
| **Kim Isak** | CI/CD Engineer | Manages build pipeline, automates testing and deployment |


Project

**202X** is a 2D vertical scrolling shooting game inspired by Capcom’s classic *194x* series, developed in **Python** (using `pygame` or a similar framework).  
The player controls a spaceship, dodges enemies, and shoots down incoming threats while aiming for a high score.

This project demonstrates the use of:
- Modular software architecture  
- Team-based version control using Git  
- Agile development (Scrum-based iterations)  
- CI/CD integration and automated testing
## 202X Project Structure

```
202X/
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
│  │   ├─ player.py
│  │   ├─ base_entity.py
│  │   │
│  │   └─ enemies/
│  │      ├─ __init__.py
│  │      ├─ enemy.py
│  │      └─ enemy_basic.py
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
│  │   ├─ spawn_manager.py
│  │   └─ stage_manager.py
│  │
│  └─ ui/
│      ├─ __init__.py
│      │
│      ├─ effects/
│      │  ├─ __init__.py
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
├─ assets/
│  └─ player_config.json
│
└─ README.md
```
