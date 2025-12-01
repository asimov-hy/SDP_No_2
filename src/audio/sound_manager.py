import pygame

from src.core.debug.debug_logger import DebugLogger

INSTANCE = None

def get_sound_manager():
    global INSTANCE
    return INSTANCE


class SoundManager:
    ASSET_PATHS = {
        "bgm": {
            "menu_bgm": "assets/audio/bgm/MainMenuBGM.wav",
            "game_bgm": "assets/audio/bgm/IngameBGM.wav",
            "game_clear": "assets/audio/bgm/GameClear.wav",
            "game_over": "assets/audio/bgm/GameOver.wav",
        },
        "bfx": {
            "enemy_destroy": "assets/audio/bfx/EnemyDestroy.wav",
            "player_destroy": "assets/audio/bfx/PlayerDestroy.wav",
            "player_shoot": "assets/audio/bfx/PlayerShoot.wav",
            "button_click": "assets/audio/ui/ButtonClick.wav",
        }
    }
    def __init__(self):
        global INSTANCE
        INSTANCE = self
        pygame.init()
        pygame.mixer.init()
        self.bfx = {}
        self.bgm = {}

        # Store UI int level separately from internal calculation float
        self.bfx_level = 100
        self.bgm_level = 100
        self.master_level = 100 # default volume = 100

        self.bfx_volume = 1.0
        self.bgm_volume = 1.0
        self.master_volume = 1.0
        self.load_assets()

        self.current_bgm = None
        self.current_bgm_id = None

    def load_assets(self):
        # DebugLogger.init("Loading Audio Assets...")
        for name, path in self.ASSET_PATHS["bgm"].items(): # load BGM
            self.load_bgm(name, path)
        for name, path in self.ASSET_PATHS["bfx"].items(): # load BFX / UI sound
            self.load_bfx(name, path)


    def volume_scale(self, level): # log scale volume control(0-100)
        if level < 0:
            return 0
        else:
            log_volume = (level / 100) ** 2
            return min(max(log_volume, 0.0), 1.0)

    def load_bfx(self, name, route): # load BFX file
        bfx_sound = self.bfx[name] = pygame.mixer.Sound(route)
        volume = self.master_volume * self.bfx_volume
        bfx_sound.set_volume(volume)

    def load_bgm(self, name, route): # load BGM route
        self.bgm[name] = route

    def play_bfx(self, name): # play BFX
        bfx = self.bfx[name]
        bfx.play()

    def play_bgm(self, name, loop): # play BGM
        if self.current_bgm_id == name:
            return
        if self.current_bgm:
                self.stop_bgm()

        route = self.bgm[name]
        pygame.mixer.music.load(route)
        volume = self.master_volume * self.bgm_volume
        pygame.mixer.music.set_volume(volume)
        pygame.mixer.music.play(loops=loop)
        self.current_bgm_id = name

    def stop_bgm(self): # stop BGM
        pygame.mixer.music.stop()
        self.current_bgm_id = None

    # Set BFX volume (0 - 100)
    def set_bfx_volume(self, level):
        self.bfx_volume = self.volume_scale(level)
        self.update_bfx()

    # Set BGM volume (0 - 100)
    def set_bgm_volume(self, level):
        self.bgm_volume = self.volume_scale(level)
        self.update_bgm()

    # Set master volume (0 - 100)
    def set_master_volume(self, level): # Set master volume
        self.master_level = level # int value for UI
        self.master_volume = self.volume_scale(level) # float value for sound calculations
        self.update_bfx()
        self.update_bgm()

    # Update BFX
    def update_bfx(self):
        volume = self.master_volume * self.bfx_volume
        for sound in self.bfx.values():
            sound.set_volume(volume)

    # Update BGM
    def update_bgm(self):
        volume = self.master_volume * self.bgm_vo1qlume
        pygame.mixer.music.set_volume(volume)

    # Get master volume level (Renew UI)
    def get_master_volume_level(self):
        return self.master_level