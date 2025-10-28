import pygame
from src.settings import *
from src.entities.player import Player

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Vertical Shooter - Minimal")
        self.clock = pygame.time.Clock()
        self.running = True

        # Create player
        self.player = Player(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 80)

    def run(self):
        while self.running:
            self._handle_events()
            self._update()
            self._draw()
            self.clock.tick(FPS)

        pygame.quit()

    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

    def _update(self):
        self.player.update()

    def _draw(self):
        self.screen.fill((10, 10, 40))  # background
        self.player.draw(self.screen)
        pygame.display.flip()
