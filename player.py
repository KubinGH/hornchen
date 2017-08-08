import random
from collections import deque

import pygame

import fontutils
import imglib
import json_ext as json
from colors import Color
from basesprite import BaseSprite
import playerui
import playerinventory, playeritems

import utils, projectiles, particles


#from libraries import fovlib

print("Load player")

config_dungeon = json.loadf("configs/dungeon.json")
level_size = config_dungeon["level_size"]
tile_size = config_dungeon["tile_size"]
tile_size_t = (tile_size, tile_size)
screen_size = config_dungeon["level_surface_size"]
screen_rect = pygame.Rect((0, 0), screen_size)

config_ui = json.loadf("configs/playerui.json")
minimap_tile = config_ui["minimap_blocksize"]
minimap_tiles = config_ui["minimap_tiles"]

class PlayerCharacter(BaseSprite):
    size = (32, 32)
    attributes = ["move_speed", "max_health_points", "vision_radius"]
    base_max_health_points = 3
    base_move_speed = 2
    base_vision_radius = 16

    starting_items = [playeritems.Sword, playeritems.EnchantedSword, playeritems.FireballStaff]

    # Static
    invincibility_ticks_on_damage = 120
    sprint_move_speed_gain = 4
    def __init__(self, game, *, imgname="Base"):
        super().__init__()
        self.game = game
        # Set somewhat implicitly by the state which handles the level
        self.level = None 
        self.rect = pygame.Rect((0, 0), self.size)
        self.image = imglib.load_image_from_file("images/dd/player/Hero{}.png".format(imgname), 
                                                  after_scale=self.rect.size)

        self.inventory = playerinventory.PlayerInventory(self)
        for item_cls in self.starting_items:
            self.inventory.add_item(item_cls(self))
        self.selected_item_idx = 0

        self.reset_attributes()
        self.activate_tile = False
        self.moving = {"left": False, "right": False, "up": False, "down": False}
        self.move_sprint = False
        self.rotation = "right"
        self.going_through_door = False
        self.crouching = False
        self.use_item = False

        self.fov_enabled = self.game.vars["enable_fov"]
        if self.fov_enabled:
            self.computed_fov_map = None
            self.level_vision = None

        self.health_points = self.max_health_points
        self.invincibility_ticks = 0

        #self.info_font = fontutils.get_font("fonts/BookAntiqua.ttf", config_ui["infofont_size"])
        #self.near_passage_text = fontutils.get_text_render(self.info_font, "Press Space to go through the door", True, Color.White)

        self.minimap = playerui.MinimapWidget(self.game, self)
        self.map_reveal = self.new_gamemap_map()
        self.invincible_hearts_render = False
        self.hearts = playerui.HeartsWidget(self.game, self)
        self.item_box = playerui.SelectedItemBoxWidget(self.game, self)

    def __repr__(self):
        return "<{} @ {}>".format(type(self).__name__, self.rect.topleft)

    def handle_events(self, events, pressed_keys, mouse_pos):
        self.activate_tile = False
        self.moving["left"]  = pressed_keys[pygame.K_LEFT]  or pressed_keys[pygame.K_a]
        self.moving["right"] = pressed_keys[pygame.K_RIGHT] or pressed_keys[pygame.K_d] 
        self.moving["up"]    = pressed_keys[pygame.K_UP]    or pressed_keys[pygame.K_w]
        self.moving["down"]  = pressed_keys[pygame.K_DOWN]  or pressed_keys[pygame.K_s]
        self.move_sprint     = pressed_keys[pygame.K_v]
        self.crouching       = pressed_keys[pygame.K_c]
        item = self.selected_item
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self.activate_tile = True
                elif event.key == pygame.K_z:
                    if item is not None and not item.special_use:
                        self.use_item = True
                elif event.key == pygame.K_LEFT:
                    self.rotation = "left"
                elif event.key == pygame.K_RIGHT:
                    self.rotation = "right"
                elif event.key == pygame.K_UP:
                    self.rotation = "up"
                elif event.key == pygame.K_DOWN:
                    self.rotation = "down"
        if item is not None and item.special_use:
            self.use_item = item.can_use(events, pressed_keys, mouse_pos)

    def update(self):
        self.reset_attributes()
        if self.use_item:
            self.selected_item.use()
            self.use_item = False
        if self.move_sprint:
            self.move_speed += self.sprint_move_speed_gain
        self.inventory.update()
        self.item_box.update()
        self.moving_last = self.moving.copy()
        if not self.crouching:
            self.handle_moving()
        self.near_passage = None
        pcol, prow = self.closest_tile_index
        ptile = self.level.layout[prow][pcol] 
        next_to = self.get_tiles_next_to()
        # Near passages to other levels
        self.going_through_door = False
        for col, row in next_to:
            tile = self.level.layout[row][col]
            if tile.flags.Passage:
                self.near_passage = tile
                break
        else:
            if ptile.flags.Passage:
                self.near_passage = ptile
        if self.near_passage is not None:
            if self.activate_tile or \
              (self.rect.left == 0 and self.moving_last["left"]) or \
              (self.rect.right == screen_size[0] and self.moving_last["right"]) or \
              (self.rect.top == 0 and self.moving_last["up"]) or \
              (self.rect.bottom == screen_size[1] and self.moving_last["down"]):
                self.going_through_door = True
        # Near containers (chests)
        self.near_container = None
        for col, row in next_to:
            tile = self.level.layout[row][col]
            if tile.flags.Container:
                self.near_container = tile
                break
        # FOV
        inside_level = 0 <= pcol < self.level.width and 0 <= prow < self.level.height
        if self.fov_enabled and inside_level and not self.computed_fov_map[prow][pcol]:
            fovlib.calculate_fov(self.level.transparency_map, 
                                 pcol, prow, self.vision_radius,
                                 dest=self.level_vision)
            self.computed_fov_map[prow][pcol] = True
        # Hidden rooms
        if ptile.flags.PartOfHiddenRoom and not ptile.uncovered:
            self.explore_room()
        # Invincibility ticks
        if self.invincibility_ticks:
            self.invincibility_ticks -= 1
            if not self.invincible_hearts_render:
                self.invincible_hearts_render = True
                self.hearts.update_hearts()
            elif self.invincibility_ticks == 0:
                self.invincible_hearts_render = False
                self.hearts.update_hearts()               

    def draw(self, screen, pos_fix=(0, 0), *, dui=True):
        if self.fov_enabled:
            # Draw black squares in places the player didn't see yet
            for row in self.level.layout:
                for tile in row:
                    if not self.level_vision[tile.row_idx][tile.col_idx]:
                        screen.fill(Color.Black, tile.rect.move(pos_fix))
        super().draw(screen, pos_fix)
        self.inventory.draw_items(screen, pos_fix)

    def draw_ui(self, screen, pos_fix=(0, 0)):
        screen.fill(Color.Black, pygame.Rect(config_dungeon["topbar_position"], config_dungeon["topbar_size"]))
        #if self.near_passage is not None:
        #    screen.blit(self.near_passage_text, config_ui["msg_pos"])
        self.minimap.draw(screen)
        self.hearts.draw(screen)
        self.item_box.draw(screen)

    @property
    def surface(self):
        return self.image

    # ===== Methods =====

    def new_empty_level_map(self):
        return [[False for _ in range(self.level.width)]
                for _ in range(self.level.height)]

    def new_gamemap_map(self):
        return [[False for _ in range(self.game.vars["mapsize"][0])] 
                for _ in range(self.game.vars["mapsize"][1])]

    def reset_attributes(self):
        #for attribute in self.attributes:
        #    setattr(self, attribute, getattr("base_{}".format(attribute)))
        self.move_speed = self.base_move_speed
        self.max_health_points = self.base_max_health_points
        self.vision_radius = self.base_vision_radius

    def new_damage_particle(self):
        return particles.Particle.from_sprite(self, 5, utils.Vector.uniform(2), 200, Color.Red)

    # Health

    def take_damage(self, value):
        if not self.invincibility_ticks:
            self.invincibility_ticks = self.invincibility_ticks_on_damage
            self.health_points -= value
            if self.health_points > self.max_health_points:
                self.health_points = self.max_health_points
            
            if value != 0: 
                self.on_damage(value)

    def heal(self, value):
        self.health_points += value
        if self.health_points > self.max_health_points:
            self.health_points = self.max_health_points

        if value != 0:
            self.hearts.update_hearts()

    # Updates

    def on_new_level(self):
        if self.fov_enabled:
            self.computed_fov_map = self.new_empty_level_map()
            self.level_vision = self.new_empty_level_map()
        self.reveal_nearby_map_tiles()
        self.minimap.update_on_new_level()

    def on_damage(self, value):
        self.hearts.update_hearts()
        for i in range(random.randint(3, 15)):
            self.level.particles.append(self.new_damage_particle())

    # Minimap

    def reveal_nearby_map_tiles(self):
        col, row = self.game.vars["player_mazepos"]
        width, height = self.game.vars["mapsize"]
        self.map_reveal[row][col] = True
        for ncol, nrow in [(col+1, row), (col-1, row), (col, row+1), (col, row-1),
                           (col+1, row+1), (col-1, row+1), (col+1, row-1), (col-1, row-1)]:
            if 0 <= ncol < width and 0 <= nrow < height:
                self.map_reveal[nrow][ncol] = True

    def reveal_all_map_tiles(self):
        for row in self.map_reveal:
            for i in range(len(row)):
                row[i] = True

    # Level

    def explore_room(self):
        scol, srow = self.closest_tile_index
        width, height = self.level.width, self.level.height
        queue = deque()
        queue.appendleft((scol, srow))
        visited = {(scol, srow)}
        while queue:
            col, row = queue.pop()
            tile = self.level.layout[row][col]
            if tile.flags.PartOfHiddenRoom:
                tile.uncover()
                checked = [
                    (col - 1, row),
                    (col + 1, row),
                    (col, row - 1),
                    (col, row + 1)
                ]
                for ncol, nrow in checked:
                    tup = (ncol, nrow)
                    if 0 <= ncol < width - 1 and 0 <= nrow < height - 1 and tup not in visited:
                        visited.add(tup)
                        queue.appendleft(tup)
        self.level.force_render_update = True

    # Status
    @property
    def dying(self):
        return self.health_points < self.max_health_points

    # Other
    @property
    def selected_item(self):
        return self.inventory.slots[self.selected_item_idx]