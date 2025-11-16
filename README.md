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
│  │   │   ├─ base_scene.py
│  │   │   ├─ game_loop.py
│  │   │   ├─ game_state.py
│  │   │   ├─ gameplay_scene.py
│  │   │   ├─ menu_scene.py
│  │   │   ├─ scene_controller.py
│  │   │   ├─ scene_manager.py
│  │   │   ├─ scene_state.py
│  │   │   └─ settings_manager.py
│  │   │
│  │   └─ services/
│  │       ├─ __init__.py
│  │       ├─ config_manager.py
│  │       ├─ display_manager.py
│  │       └─ input_manager.py
│  │
│  ├─ config/
│  │   ├─ campaigns.json
│  │   │
│  │   ├─ entities/
│  │   │   ├─ items.json
│  │   │   └─ player.json
│  │   │
│  │   └─ levels/
│  │       ├─ Test_Homing.json
│  │       ├─ Test_Straight.json
│  │       └─ Test_Straight 2.json
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
│  │   ├─ items/
│  │   │   ├─ __init__.py
│  │   │   ├─ base_item.py
│  │   │   └─ item_health.py
│  │   │
│  │   ├─ enemies/
│  │   │   ├─ __init__.py
│  │   │   ├─ base_enemy.py
│  │   │   └─ enemy_straight.py
│  │   │
│  │   └─ player/
│  │       ├─ __init__.py
│  │       ├─ player_ability.py
│  │       ├─ player_core.py
│  │       ├─ player_logic.py
│  │       ├─ player_movement.py
│  │       └─ player_state.py
│  │
│  ├─ graphics/
│  │   ├─ __init__.py
│  │   ├─ draw_manager.py
│  │   │
│  │   └─ animations/
│  │       ├─ __init__.py
│  │       ├─ animation_controller.py
│  │       ├─ animation_manager.py
│  │       │
│  │       ├─ animation_effects/
│  │       │  ├─ __init__.py
│  │       │  ├─ common_animation.py
│  │       │  ├─ damage_animation.py
│  │       │  ├─ death_animation.py
│  │       │  └─ movement_animation.py
│  │       │
│  │       └─ entities/
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
│  │   │   ├─ __init__.py
│  │   │   ├─ collision_hitbox.py
│  │   │   └─ collision_manager.py
│  │   │
│  │   ├─ combat/
│  │   │   ├─ __init__.py
│  │   │   └─ bullet_manager.py
│  │   │
│  │   └─ level/
│  │       ├─ __init__.py
│  │       ├─ level_manager.py
│  │       ├─ pattern_registry.py
│  │       └─ spawn_manager.py
│  │
│  └─ ui/
│      ├─ __init__.py
│      │
│      ├─ configs/
│      │   ├─ hud/
│      │   │   ├─ debug_hud.yaml
│      │   │   └─ player_hud.yaml
│      │   │ 
│      │   └─ screens/
│      │       └─ pause_menu.yaml
│      │
│      ├─ core/
│      │   ├─ __init__.py
│      │   ├─ anchor_resolver.py
│      │   ├─ binding_system.py
│      │   ├─ ui_element.py
│      │   ├─ ui_loader.py
│      │   └─ ui_manager.py
│      │
│      └─ elements/
│          ├─ __init__.py
│          ├─ bay.py
│          ├─ button.py
│          ├─ container.py
│          └─ label.py
│
└─ assets/
   ├─ audio/
   │   ├─ bfx/
   │   │   ├─ EnemyDestroy.wav
   │   │   ├─ GameClear.wav
   │   │   ├─ GameOver.wav
   │   │   ├─ PlayerDestroy.wav
   │   │   └─ PlayerShoot.wav
   │   │
   │   ├─ bgm/
   │   │   ├─ IngameBGM.wav
   │   │   ├─ IngameBGM2.wav
   │   │   └─ MainMenuBGM.wav
   │   │
   │   └─ icons/
   │       └─ switch.ogg
   │
   └─ images/
       ├─ characters/
       │   ├─ enemies/
       │   │   └─ enemy_basic.png
       │   │
       │   └─ player/
       │       └─ robot_Garda.png
       │
       ├─ effects/
       │   └─ explosions/
       │       ├─ explosion01.png
       │       ├─ explosion02.png
       │       └─ explosion03.png
       │
       ├─ icons/
       │   └─ 202X_icon.png
       │
       ├─ items/
       │   └─ dummy_item.png
       │
       ├─ maps/
       │   ├─ battle_stage1.png
       │   ├─ battle_stage2.png
       │   ├─ battle_stage3.png
       │   ├─ battle_stage4.png
       │   └─ boss_stage.png
       │
       ├─ projectiles/
       │   ├─ 100H.png
       │   ├─ m107.png
       │   └─ missile.png
       │
       └─ ui/
           ├─ bars/
           │   ├─ current_exp.png
           │   ├─ exp_bar.png
           │   └─ main_bar.png
           │
           └─ health/
               ├─ health_guage.png
               └─ health_needle.png
```
