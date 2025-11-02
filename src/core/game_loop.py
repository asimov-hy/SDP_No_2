import pygame
from src.entities.player import Player
from src.graphics.draw_manager import DrawManager
from src.core.settings import *
from src.core.input_manager import InputManager
from src.core.display_manager import DisplayManager

class GameLoop:
    def __init__(self):
        pygame.init()
        self.display = DisplayManager(GAME_WIDTH, GAME_HEIGHT)
        pygame.display.set_caption("202X")

        icon = pygame.image.load("assets/images/icons/202X_icon.png")
        pygame.display.set_icon(icon)


        self.clock = pygame.time.Clock()
        self.running = True

        # Systems
        self.draw_manager = DrawManager()
        self.input = InputManager()

        # Entities
        self.draw_manager.load_image("player", "assets/images/player.png", scale=1.0)
        player_img = self.draw_manager.get_image("player")
        self.player = Player(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 80, player_img)

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000
            self._handle_events()
            self._update(dt)
            self._draw()
        pygame.quit()

    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F11:  # F11 for fullscreen
                    self.display.toggle_fullscreen()
            elif event.type == pygame.VIDEORESIZE:
                self.display.handle_resize(event)

    def _update(self, dt):
        # Poll all inputs (keyboard, controller)
        self.input.update()

        # Movement vector (normalized)
        move = self.input.get_normalized_move()
        self.player.update(dt, move)

        # Action example
        if self.input.attack_pressed:
            print("Attack!")

    def _draw(self):
        # Get the game surface to draw on
        game_surface = self.display.get_game_surface()

        # Clear and draw to game surface
        self.draw_manager.clear()
        self.draw_manager.draw_entity(self.player, layer=1)
        self.draw_manager.render(game_surface)

        # Display manager handles scaling and letterboxing
        self.display.render()

