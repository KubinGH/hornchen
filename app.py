import cProfile, pstats

import pygame

import game
import states
import fontutils
from colors import Color

WINDOW_SIZE = (1024, 768)

MAX_FPS = 0

_screen = None

def get_screen(*args, **kwargs):
    global _screen
    if _screen is not None and (args or kwargs):
        raise ValueError("Screen already created")
    if _screen is None:
        if not args:
            args = (WINDOW_SIZE, )
        assert args[0][0] >= 1024 and args[0][1] >= 768
        _screen = pygame.display.set_mode(*args, **kwargs)
    return _screen

def alt_pressed(pressed_keys):
    return pressed_keys[pygame.K_LALT] or pressed_keys[pygame.K_RALT]

def exit_event(event, pressed_keys):
    return (event.type == pygame.QUIT) or \
           (event.type == pygame.KEYDOWN and \
                event.key == pygame.K_q and alt_pressed(pressed_keys))

def center_fix(outer_rect, inner_rect):
    return ((outer_rect.width - inner_rect.width) // 2, (outer_rect.height - inner_rect.height) // 2)

def fixed_mouse_pos(ds_center_fix):
    pos = pygame.mouse.get_pos()
    return (pos[0] - ds_center_fix[0], pos[1] - ds_center_fix[1])

class App:
    def __init__(self, screen=None):
        pygame.init()
        self.screen = screen if screen is not None else get_screen()
        self.draw_surface = pygame.Surface(WINDOW_SIZE)
        self.game = game.GameEngine(screen_size=WINDOW_SIZE, draw_surface=self.draw_surface, screen=self.screen)

    def run(self):
        ds_center_fix = center_fix(self.screen.get_rect(), self.draw_surface.get_rect())
        last_state = current_state = None
        show_fps = False; fpsfont = fontutils.get_sysfont("Monospace", 32); force_show_fps = False
        max_fps = MAX_FPS
        ticks = 0
        clock = pygame.time.Clock()
        running = True
        while running:
            mouse_pos = fixed_mouse_pos(ds_center_fix)
            pressed_keys = pygame.key.get_pressed()
            events = pygame.event.get()
            for event in events:
                if exit_event(event, pressed_keys):
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_F3:
                        show_fps = not show_fps
                        if show_fps: force_show_fps = True
                    elif event.key == pygame.K_f and (pressed_keys[pygame.K_LSHIFT] or pressed_keys[pygame.K_RSHIFT]):
                        max_fps = MAX_FPS if max_fps == 60 else 60
                        print("set max fps", max_fps)
            last_state = current_state
            current_state = self.game.top_state
            if current_state is None: 
                raise AssertionError("No current state")
            if last_state != current_state and last_state is not None and not last_state.deactivated:
                last_state.pause()
                self.draw_surface.fill(Color.Black)
            if current_state.paused:
                current_state.resume()

            self.game.handle_events(current_state, events, pressed_keys, mouse_pos)
            pygame.event.pump()

            self.game.update(current_state)

            rects = self.game.draw(current_state, self.draw_surface)
            self.screen.fill(Color.Black)
            self.screen.blit(self.draw_surface, ds_center_fix)
            if show_fps:
                if not ticks % 120 or force_show_fps:
                    current_fps = round(clock.get_fps())
                    render = fontutils.get_text_render(fpsfont, str(current_fps), False, Color.Red, dolog=False)
                self.screen.blit(render, (self.screen.get_width() - render.get_width(), 0))
            if rects is not None and len(rects) < 250:
                pygame.display.update(rects)
            else:
                pygame.display.flip()

            clock.tick(max_fps)
            ticks += 1
            if ticks > 10**9: ticks = 1

        pygame.quit()


fullscreen = False
custom_screen_size = None

if __name__ == "__main__":
    if fullscreen:
        _screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    elif custom_screen_size is not None:
        _screen = pygame.display.set_mode(custom_screen_size)
    print("Screen size:", get_screen().get_size())
    profiler = cProfile.Profile()
    profiler.enable()
    app = App()
    app.run()
    profiler.disable()
    profiler.dump_stats("profile.stats")
    stats = pstats.Stats("profile.stats")
    stats.strip_dirs(); stats.sort_stats("calls")
    stats.print_stats()

