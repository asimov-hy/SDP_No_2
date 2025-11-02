import pygame

class DrawManager:
    def __init__(self):
        self.images = {}
        self.draw_queue = []  # store (image, rect, layer)

    def load_image(self, key, path, scale=1.0):
        try:
            img = pygame.image.load(path).convert_alpha()
        except FileNotFoundError:
            print(f"[WARN] Missing image: {path}")
            img = pygame.Surface((40, 40))
            img.fill((255, 255, 255))
        if scale != 1.0:
            w, h = img.get_size()
            img = pygame.transform.scale(img, (int(w * scale), int(h * scale)))
        self.images[key] = img

    def get_image(self, key):
        return self.images.get(key)

    def clear(self):
        self.draw_queue.clear()

    def draw_entity(self, entity, layer=0):
        """Queue an entity (must have image + rect attributes)."""
        self.draw_queue.append((entity.image, entity.rect, layer))

    def render(self, surface):
        """Sort draw calls by layer and render to surface."""
        surface.fill((50, 50, 100))  # clear background
        for image, rect, _ in sorted(self.draw_queue, key=lambda x: x[2]):
            surface.blit(image, rect)
        pygame.display.flip()
