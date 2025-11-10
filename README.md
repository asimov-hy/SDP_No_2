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
├─ README.md
├─ main.py
├─ .gitignore
│
├─ src/
│  │
│  ├─ __init__.py
│  │
│  ├─ core/
│  │   ├─ __init__.py
│  │   ├─ game_loop.py
│  │   ├─ game_settings.py
│  │   ├─ game_state.py
│  │   │
│  │   ├─ engine/
│  │   │   ├─ __init__.py
│  │   │   ├─ display_manager.py
│  │   │   ├─ input_manager.py
│  │   │   └─ scene_manager.py
│  │   │
│  │   └─ utils/
│  │       ├─ __init__.py
│  │       ├─ config_manager.py
│  │       └─ debug_logger.py
│  │
│  ├─ data/
│  │   └─ player_config.json
│  │
│  ├─ entities/
│  │   ├─ __init__.py
│  │   ├─ base_entity.py
│  │   │
│  │   ├─ bullets/
│  │   │  ├─ __init__.py
│  │   │  ├─ base_bullet.py
│  │   │  └─ bullet_straight.py
│  │   │
│  │   ├─ enemies/
│  │   │  ├─ __init__.py
│  │   │  ├─ base_enemy.py
│  │   │  └─ enemy_straight.py
│  │   │
│  │   └─ player/
│  │      ├─ __init__.py
│  │      ├─ player_base.py
│  │      ├─ player_combat.py
│  │      ├─ player_config.py
│  │      ├─ player_movement.py
│  │      └─ player_state.py
│  │
│  ├─ graphics/
│  │   ├─ __init__.py
│  │   └─ draw_manager.py
│  │
│  ├─ scenes/
│  │   ├─ __init__.py
│  │   ├─ game_scene.py
│  │   ├─ pause_scene.py (empty)
│  │   └─ start_scene.py
│  │
│  ├─ systems/
│  │   ├─ __init__.py
│  │   │
│  │   ├─ combat/
│  │   │  ├─ __init__.py
│  │   │  ├─ bullet_manager.py
│  │   │  ├─ collision_hitbox.py
│  │   │  └─ collision_manager.py
│  │   │
│  │   └─ enemies/
│  │      ├─ __init__.py
│  │      ├─ level_manager.py
│  │      ├─ sound_manager.py (empty)
│  │      └─ spawn_manager.py
│  │
│  └─ ui/
│      ├─ __init__.py
│      ├─ base_ui.py
│      ├─ ui_button.py
│      ├─ ui_manager.py
│      │
│      ├─ effects/
│      │  ├─ __init__.py
│      │  ├─ ui_animation.py (empty)
│      │  └─ ui_fade.py (empty)
│      │
│      └─ subsystems/
│         ├─ __init__.py
│         ├─ debug_hud.py
│         ├─ hud_manager.py
│         └─ menu_manager.py (empty)
│
└─ assets/
   ├─ images/
   │   ├─ player.png
   │   │
   │   └─ icons/
   │       └─ 202X_icon.png
   │
   └─ sounds/
```
