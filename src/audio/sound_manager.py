import pygame


class SoundManager:
    def __init__(self):
        pygame.init()
        pygame.mixer.init()
        self.bfx = {}
        self.bgm = {}
        self.bfx_volume = 1.0
        self.bgm_volume = 1.0
        self.master_volume = 1.0

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
        route = self.bgm[name]
        pygame.mixer.music.load(route)
        volume = self.master_volume * self.bgm_volume
        pygame.mixer.music.set_volume(volume)
        pygame.mixer.music.play(loops=loop)

    def stop_bgm(self): # stop BGM
        pygame.mixer.music.stop()

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
        self.master_volume = self.volume_scale(level)
        self.update_bfx()
        self.update_bgm()

    # Update BFX
    def update_bfx(self):
        volume = self.master_volume * self.bfx_volume
        for sound in self.bfx.values():
            sound.set_volume(volume)

    # Update BGM
    def update_bgm(self):
        volume = self.master_volume * self.bgm_volume
        pygame.mixer.music.set_volume(volume)