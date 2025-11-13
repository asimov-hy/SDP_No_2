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
│  ├─ __init__.py
│  │
│  ├─ audio/
│  │   ├─ __init__.py
│  │   └─ sound_manager.py
│  │
│  ├─ core/
│  │   ├─ __init__.py
│  │   │
│  │   ├─ debug/
│  │   │   ├─ __init__.py
│  │   │   ├─ debug_hud.py
│  │   │   └─ debug_logger.py
│  │   │
│  │   ├─ runtime/
│  │   │   ├─ __init__.py
│  │   │   ├─ game_loop.py
│  │   │   ├─ game_settings.py
│  │   │   ├─ game_state.py
│  │   │   └─ scene_manager.py
│  │   │
│  │   └─ services/
│  │       ├─ __init__.py
│  │       ├─ config_manager.py
│  │       ├─ display_manager.py
│  │       └─ input_manager.py
│  │
│  ├─ data/
│  │   ├─ configs/
│  │   │   └─ player_config.py
│  │   │
│  │   └─ levels/
│  │       └─ Stage 1.py
│  │
│  ├─ entities/
│  │   ├─ __init__.py
│  │   ├─ base_entity.py
│  │   ├─ entity_registry.py
│  │   ├─ entity_state.py
│  │   ├─ status_manager.py
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
│  │      ├─ player_ability.py
│  │      ├─ player_core.py
│  │      ├─ player_logic.py
│  │      ├─ player_movement.py
│  │      └─ player_state.py
│  │
│  ├─ graphics/
│  │   ├─ __init__.py
│  │   ├─ draw_manager.py
│  │   │
│  │   └─ animations/
│  │      ├─ __init__.py
│  │      ├─ animation_controller.py
│  │      ├─ animation_manager.py
│  │      │
│  │      ├─ animation_effects/
│  │      │  ├─ __init__.py
│  │      │  ├─ common_animation.py
│  │      │  ├─ damage_animation.py
│  │      │  ├─ death_animation.py
│  │      │  └─ movement_animation.py
│  │      │
│  │      └─ entities/
│  │         ├─ __init__.py
│  │         ├─ enemy_animation.py
│  │         └─ player_animation.py
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
│  │   ├─ collision/
│  │   │  ├─ __init__.py
│  │   │  ├─ collision_hitbox.py
│  │   │  └─ collision_manager.py
│  │   │
│  │   ├─ combat/
│  │   │  ├─ __init__.py
│  │   │  └─ bullet_manager.py
│  │   │
│  │   └─ level/
│  │      ├─ __init__.py
│  │      ├─ level_manager.py
│  │      ├─ pattern_registry.py
│  │      └─ spawn_manager.py
│  │
│  └─ ui/
│      ├─ __init__.py
│      ├─ base_ui.py
│      ├─ menu_manager.py (empty)
│      ├─ ui_manager.py
│      │
│      ├─ components/
│      │  ├─ __init__.py
│      │  └─ ui_button.py
│      │
│      └─ effects/
│         ├─ __init__.py
│         ├─ ui_animation.py (empty)
│         └─ ui_fade.py (empty)
│
└─ assets/
   ├─ images/
   │   ├─ player.png (unused)
   │   │
   │   └─ icons/
   │       └─ 202X_icon.png
   │
   └─ audio/
```
