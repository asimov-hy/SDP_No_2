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
SDP-202X/
├─ README.md
├─ main.py
│
├─ assets/
│  ├─ audio/
│  │  ├─ bfx/
│  │  │  ├─ EnemyDestroy.wav
│  │  │  ├─ GameClear.wav
│  │  │  ├─ GameOver.wav
│  │  │  ├─ PlayerDestroy.wav
│  │  │  └─ PlayerShoot.wav
│  │  │
│  │  ├─ bgm/
│  │  │  ├─ IngameBGM.wav
│  │  │  ├─ IngameBGM2.wav
│  │  │  └─ MainMenuBGM.wav
│  │  │
│  │  └─ ui/
│  │     └─ switch.ogg
│  │
│  └─ images/
│     ├─ null.png
│     │
│     ├─ effects/
│     │  └─ explosions/
│     │     ├─ explosion01.png
│     │     ├─ explosion02.png
│     │     └─ explosion03.png
│     │
│     ├─ icons/
│     │  └─ 202X_icon.png
│     │
│     ├─ maps/
│     │  ├─ battle_stage1.png
│     │  ├─ battle_stage2.png
│     │  ├─ battle_stage3.png
│     │  ├─ battle_stage4.png
│     │  └─ boss_stage.png
│     │
│     ├─ sprites/
│     │  ├─ enemies/
│     │  │  ├─ enemy_basic.png
│     │  │  └─ missile.png
│     │  │
│     │  ├─ items/
│     │  │  ├─ health_pack.png
│     │  │  ├─ nuke.png
│     │  │  ├─ quick_fire.png
│     │  │  └─ speed_boost.png
│     │  │
│     │  ├─ player/
│     │  │  └─ robot_Garda.png
│     │  │
│     │  └─ projectiles/
│     │     ├─ 100H.png
│     │     └─ m107.png
│     │
│     └─ ui/
│        ├─ bars/
│        │  ├─ current_exp.png
│        │  ├─ exp_bar.png
│        │  └─ main_bar.png
│        │
│        └─ health/
│           ├─ health_gauge.png
│           └─ health_needle.png
│
└─ src/
   ├─ __init__.py
   │
   ├─ audio/
   │  ├─ __init__.py
   │  └─ sound_manager.py
   │
   ├─ config/
   │  ├─ campaigns.json
   │  │
   │  ├─ entities/
   │  │  ├─ bullets.json
   │  │  ├─ enemies.json
   │  │  ├─ items.json
   │  │  └─ player.json
   │  │
   │  ├─ levels/
   │  │  ├─ Demo_Level.json
   │  │  ├─ Test_Homing.json
   │  │  └─ level1.json
   │  │
   │  └─ ui/
   │     ├─ hud/
   │     │  ├─ debug_hud.yaml
   │     │  ├─ game_over.yaml
   │     │  ├─ gameplay_hud.yaml
   │     │  ├─ pause_hud.yaml
   │     │  └─ player_hud.yaml
   │     │
   │     └─ screens/
   │        ├─ campaign_select.yaml
   │        ├─ main_menu.yaml
   │        └─ settings.yaml
   │
   ├─ core/
   │  ├─ __init__.py
   │  │
   │  ├─ debug/
   │  │  ├─ __init__.py
   │  │  ├─ debug_hud.py
   │  │  └─ debug_logger.py
   │  │
   │  ├─ runtime/
   │  │  ├─ __init__.py
   │  │  ├─ game_loop.py
   │  │  ├─ game_settings.py
   │  │  └─ session_stats.py
   │  │
   │  └─ services/
   │     ├─ __init__.py
   │     ├─ config_manager.py
   │     ├─ display_manager.py
   │     ├─ event_manager.py
   │     ├─ input_manager.py
   │     ├─ scene_manager.py
   │     ├─ service_locator.py
   │     └─ settings_manager.py
   │
   ├─ entities/
   │  ├─ __init__.py
   │  ├─ base_entity.py
   │  ├─ entity_state.py
   │  ├─ entity_types.py
   │  ├─ state_manager.py
   │  │
   │  ├─ bullets/
   │  │  ├─ __init__.py
   │  │  ├─ base_bullet.py
   │  │  └─ bullet_straight.py
   │  │
   │  ├─ enemies/
   │  │  ├─ __init__.py
   │  │  ├─ base_enemy.py
   │  │  ├─ enemy_homing.py
   │  │  ├─ enemy_shooter.py
   │  │  └─ enemy_straight.py
   │  │
   │  ├─ environments/
   │  │  ├─ __init__.py
   │  │  ├─ base_hazard.py
   │  │  └─ base_obstacle.py
   │  │
   │  ├─ items/
   │  │  ├─ __init__.py
   │  │  └─ base_item.py
   │  │
   │  └─ player/
   │     ├─ __init__.py
   │     ├─ player_ability.py
   │     ├─ player_core.py
   │     ├─ player_effects.py
   │     ├─ player_logic.py
   │     ├─ player_movement.py
   │     └─ player_state.py
   │
   ├─ graphics/
   │  ├─ __init__.py
   │  ├─ draw_manager.py
   │  │
   │  └─ animations/
   │     ├─ __init__.py
   │     ├─ animation_manager.py
   │     ├─ animation_registry.py
   │     │
   │     ├─ animation_effects/
   │     │  ├─ __init__.py
   │     │  ├─ common_animation.py
   │     │  ├─ damage_animation.py
   │     │  ├─ death_animation.py
   │     │  └─ movement_animation.py
   │     │
   │     └─ entities_animation/
   │        ├─ __init__.py
   │        ├─ enemy_animation.py
   │        └─ player_animation.py
   │
   ├─ scenes/
   │  ├─ __init__.py
   │  ├─ base_scene.py
   │  ├─ campaign_select_scene.py
   │  ├─ game_scene.py
   │  ├─ main_menu_scene.py
   │  ├─ scene_state.py
   │  ├─ settings_scene.py
   │  │
   │  └─ transitions/
   │     ├─ __init__.py
   │     ├─ i_transition.py
   │     └─ instant_transition.py
   │
   ├─ systems/
   │  ├─ __init__.py
   │  ├─ game_system_initializer.py
   │  ├─ system_initializer.py
   │  │
   │  ├─ collision/
   │  │  ├─ __init__.py
   │  │  ├─ collision_hitbox.py
   │  │  └─ collision_manager.py
   │  │
   │  ├─ entity_management/
   │  │  ├─ __init__.py
   │  │  ├─ bullet_manager.py
   │  │  ├─ entity_registry.py
   │  │  ├─ item_manager.py
   │  │  └─ spawn_manager.py
   │  │
   │  └─ level/
   │     ├─ __init__.py
   │     ├─ level_manager.py
   │     ├─ level_registry.py
   │     ├─ pattern_registry.py
   │     ├─ stage_loader.py
   │     └─ wave_scheduler.py
   │
   └─ ui/
      ├─ __init__.py
      │
      ├─ core/
      │  ├─ __init__.py
      │  ├─ anchor_resolver.py
      │  ├─ binding_system.py
      │  ├─ ui_element.py
      │  ├─ ui_loader.py
      │  └─ ui_manager.py
      │
      └─ elements/
         ├─ __init__.py
         ├─ bar.py
         ├─ button.py
         ├─ container.py
         └─ label.py
```