from collections import namedtuple

import pygame

import json_ext as json
import imglib
from abc_playeritem import AbstractPlayerItem

class ValueRotationDependent:
    def __init__(self, right, left, up, down):
        self.right, self.left, self.up, self.down = right, left, up, down

    def __getitem__(self, key):
        return getattr(self, key)

inventory_gui_config = json.loadf("configs/player_inventory.json")
slot_size_t = inventory_gui_config["slot_size"]
slot_border_width = inventory_gui_config["slot_border_width"]
slot_size = slot_size_t[0]
icon_size = 16
icon_size_t = (icon_size, icon_size)

dungeon_config = json.loadf("configs/dungeon.json")
level_surface_size = dungeon_config["level_surface_size"]
level_rect = pygame.Rect((0, 0), level_surface_size)

def all_rotations(right):
    left = pygame.transform.flip(right, 1, 0) # surface, xbool, ybool
    down = pygame.transform.rotate(right, -90)
    up = pygame.transform.flip(down, 0, 1)
    return ValueRotationDependent(right, left, up, down)

# ====== Bases =======

class BaseEdibleItem(AbstractPlayerItem):
    icon = imglib.get_missing_surface(icon_size_t)
    size = (16, 16)
    surface = imglib.get_missing_surface(size)

    points_healed = 1

    def __init__(self, player):
        super().__init__(player)
        self.being_eaten = False
        self.ticks_to_eat = 80

    def use(self):
        if not self.being_eaten:
            self.player.heal(self.points_healed)
            self.being_eaten = True

    def update(self):
        if self.being_eaten:
            self.ticks_to_eat -= 1
        if self.ticks_to_eat <= 0:
            self.player.inventory.remove_item(self)

    def draw(self, screen, pos_fix=(0, 0)):
        if self.being_eaten:
            screen.blit(self.surface, self.rect.move(pos_fix))

    @property
    def rect(self):
        return pygame.Rect((self.player.rect.centerx - self.size[0] / 2, self.player.rect.bottom - 20), self.size)

# ====== ====== ======

class Sword(AbstractPlayerItem):
    icon = imglib.load_image_from_file("images/sl/items/icons/sword_i.png", after_scale=icon_size_t)
    bsize1, bsize2 = 30, 12
    size_r = ValueRotationDependent(right=(bsize1, bsize2), left=(bsize1, bsize2), 
                                    up=(bsize2, bsize1), down=(bsize2, bsize1))
    image_r = all_rotations(imglib.load_image_from_file("images/sl/items/sword.png", after_scale=size_r.right))
    dist_from_player = -6

    attack_length = 120
    damage_dealt = 0.5

    def __init__(self, player):
        super().__init__(player)
        self.drawn = False
        self.rotation = "right"
        self.ticks_left = 0
        self.cooldown = 0
        self.hit = []

    def use(self):
        if self.cooldown <= 0:
            self.drawn = True
            self.rotation = self.player.rotation
            self.ticks_left = self.attack_length
            self.cooldown = round(self.ticks_left * 1.1)

    def update(self):
        if self.drawn:
            level = self.player.level
            if level is not None:
                for sprite in level.sprites:
                    if self.rect.colliderect(sprite.rect) and sprite not in self.hit:
                        sprite.take_damage(self.damage_dealt)
                        self.hit.append(sprite)
            self.ticks_left -= 1
            if not self.ticks_left:
                self.drawn = False
                self.hit = []
        if self.cooldown > 0:
            self.cooldown -= 1

    def draw(self, screen, pos_fix=(0, 0)):
        if self.drawn:
            screen.blit(self.surface, self.rect.move(pos_fix))

    @property
    def size(self):
        return self.size_r[self.rotation]

    @property
    def surface(self):
        return self.image_r[self.rotation]

    @property
    def rect(self):
        y_centered = self.player.rect.centery - self.size[1]/2
        x_centered = self.player.rect.centerx - self.size[0]/2
        if self.rotation == "right":
            pos = self.player.rect.right + self.dist_from_player, y_centered
        elif self.rotation == "left":
            pos = self.player.rect.left - self.dist_from_player - self.size[0], y_centered
        elif self.rotation == "up":
            pos = x_centered, self.player.rect.top - self.dist_from_player - self.size[1]
        elif self.rotation == "down":
            pos = x_centered, self.player.rect.bottom + self.dist_from_player
        else:
            pos = (0, 0)
        return pygame.Rect(pos, self.size)

class EnchantedSword(Sword):
    icon = imglib.load_image_from_file("images/sl/items/icons/enchanted_sword_i.png", after_scale=icon_size_t)
    image_r = all_rotations(imglib.load_image_from_file("images/sl/items/enchanted_sword.png", after_scale=Sword.size_r.right))
    projectile_r = all_rotations(imglib.load_image_from_file("images/sl/items/projectiles/ethereal_sword.png", after_scale=Sword.size_r.right))

    damage_dealt = 1
    projectile_speed = 3

    def __init__(self, player):
        super().__init__(player)
        self.projectile_rect = self.projectile_img = None

    def use(self):
        if self.cooldown <= 0:
            self.drawn = True
            self.rotation = self.player.rotation
            self.ticks_left = self.attack_length
            self.cooldown = round(self.ticks_left * 1.1)
            if self.projectile_rect is None:
                self.spawn_projectile(self.rect)
        if self.player.activate_tile:
            self.remove_projectile()

    def update(self):
        super().update()
        if self.projectile_rect is not None:
            if self.rotation == "left": 
                self.projectile_rect.x -= self.projectile_speed
            elif self.rotation == "right": 
                self.projectile_rect.x += self.projectile_speed
            if self.rotation == "up": 
                self.projectile_rect.y -= self.projectile_speed
            if self.rotation == "down": 
                self.projectile_rect.y += self.projectile_speed
            for row in self.player.level.layout:
                for tile in row:
                    if not tile.passable and self.projectile_rect.colliderect(tile.rect):
                        self.projectile_rect = None
                        break
                else:
                    continue
                break
            if self.projectile_rect is not None:
                for sprite in self.player.level.sprites:
                    if sprite.hostile and self.projectile_rect.colliderect(sprite.rect):
                        sprite.take_damage(self.damage_dealt / 2)
                        self.remove_projectile()
                        break
            if self.projectile_rect is not None:
                if not 0 < self.projectile_rect.x < level_rect.right or \
                   not 0 < self.projectile_rect.y < level_rect.bottom:
                    self.remove_projectile()

    def spawn_projectile(self, rect):
        self.projectile_rect = rect.copy()
        self.projectile_img = self.projectile_r[self.rotation]

    def remove_projectile(self):
        self.projectile_rect = None

    def draw(self, screen, pos_fix=(0, 0)):
        super().draw(screen, pos_fix)
        if self.projectile_rect is not None:
            screen.blit(self.projectile_img, self.projectile_rect.move(pos_fix))

class Apple(BaseEdibleItem):
    icon = imglib.load_image_from_file("images/sl/items/apple.png", after_scale=icon_size_t)
    size = (16, 16)
    surface = imglib.load_image_from_file("images/sl/items/apple.png", after_scale=size)
    points_healed = 1