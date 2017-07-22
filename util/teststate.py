# Useless, tbh.

# ===== ===== ===== ===== ===== ===== ===== ===== ===== =====
# ===== ===== =====        Test State       ===== ===== =====
# ===== ===== ===== ===== ===== ===== ===== ===== ===== =====

class TestState(AbstractGameState):
    def __init__(self, game):
        super().__init__(game)

        self.rect = pygame.rect.Rect(0, 0, 40, 40)
        self.last_rect = None
        self.step = 4
        self.changed = False
        self.force_refresh = True

    def cleanup(self):
        super().cleanup()

    def pause(self):
        super().pause()

    def resume(self):
        super().resume()

    def handle_events(self, events, pressed_keys, mouse_pos):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_a:
                    self.step = 4 if self.step != 4 else 12
                elif event.key == pygame.K_e:
                    self.game.pop_state()
                    self.cleanup()
                elif event.key == pygame.K_ESCAPE:
                    self.game.push_state(PauseState(self.game))
        self.last_rect = self.rect.copy()
        self.changed = False
        if pressed_keys[pygame.K_LEFT]:
            if self.rect.x - self.step >= 0:
                self.rect.x -= self.step
                self.changed = True
            else:
                self.rect.x = 0
        if pressed_keys[pygame.K_RIGHT]:
            if self.rect.x + self.rect.width + self.step <= self.game.vars["screen_size"][0]:
                self.rect.x += self.step
                self.changed = True
            else:
                self.rect.x = self.game.vars["screen_size"][0] - self.rect.width
        if pressed_keys[pygame.K_UP]:
            if self.rect.y - self.step >= 0:
                self.rect.y -= self.step
                self.changed = True
            else:
                self.rect.y = 0
        if pressed_keys[pygame.K_DOWN]:
            if self.rect.y + self.rect.height + self.step <= self.game.vars["screen_size"][1]:
                self.rect.y += self.step
                self.changed = True
            else:
                self.rect.y = self.game.vars["screen_size"][1] - self.rect.height

    def update(self):
        pass

    def draw(self, screen):
        if self.changed or self.force_refresh:
            self.changed = False
            screen.fill(Color.Black, self.last_rect)
            screen.fill(Color.Black, self.rect)
            if self.force_refresh:
                return None
            else:
                return [self.last_rect, self.rect]
        else:
            return []