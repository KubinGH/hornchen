from collections import namedtuple

import pygame

from abc_playeritem import AbstractPlayerItem
import json_ext as json
import imglib
from imglib import ValueRotationDependent, all_rotations
from basesprite import BaseSprite
import projectiles
import statuseffects
import utils

print("Load player items")

icon_size = 16
icon_size_t = (icon_size, icon_size)

config_dungeon = json.loadf("configs/dungeon.json")

class DroppedItem(BaseSprite):
    friendly = hostile = False
    def __init__(self, level, rectcenter, item_cls):
        super().__init__()
        self.level = level
        self.item_cls = item_cls
        self.rect = pygame.Rect((0, 0), item_cls.dropped_size)
        self.rect.center = rectcenter
        self.surface = imglib.scale(item_cls.icon, self.rect.size)

    def update(self):
        player = self.level.parent.player
        if self.rect.colliderect(player.rect):
            if not player.inventory.full:
                player.inventory.add_item(self.item_cls(player))
                self.level.sprites.remove(self)

    def create_cache(self):
        return {
            "type": "item",
            "cls": type(self),
            "rect": self.rect,
            "item_cls": self.item_cls
        }

    @classmethod
    def from_cache(cls, level, cache):
        return cls(level, cache["rect"].center, cache["item_cls"])

# ====== Bases =======

class BaseEdibleItem(AbstractPlayerItem):
    icon = imglib.get_missing_surface(icon_size_t)
    size = (16, 16)
    surface = imglib.get_missing_surface(size)

    points_healed = 1
    def __init__(self, player):
        super().__init__(player)
        self.being_eaten = False
        self.ticks_to_eat = self.points_healed / statuseffects.Regeneration.heal_per_tick

    def use(self):
        if not self.being_eaten:
            tick = self.player.status_effects.get_tick()
            self.ticks_to_eat = self.points_healed / statuseffects.Regeneration.heal_per_tick
            e = statuseffects.Regeneration(self.player, tick, self.ticks_to_eat)
            self.player.status_effects.add(e)
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

    def create_cache(self):
        if self.being_eaten:
            return None
        else:
            return super().create_cache()

# ====== Weapons ======

# ==== Swords ====

class Sword(AbstractPlayerItem):
    name = "Sword"
    description = \
"""It's probably not a good idea to use it for cutting bread.

0.5 Damage"""
    icon = imglib.load_image_from_file("images/sl/items/icons/SwordI.png", after_scale=icon_size_t)
    bsize1, bsize2 = 30, 12
    size_r = ValueRotationDependent(right=(bsize1, bsize2), left=(bsize1, bsize2), 
                                    up=(bsize2, bsize1), down=(bsize2, bsize1))
    image_r = all_rotations(imglib.load_image_from_file("images/sl/items/Sword.png", after_scale=size_r.right))
    dist_from_player = -6

    attack_length = 60
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
            self.rotation = self.get_new_sword_rotation()
            self.ticks_left = self.attack_length
            self.cooldown = round(self.ticks_left * 1.1)

    def update(self):
        if self.drawn:
            for sprite in BaseSprite.get_enemy_sprites_as(True, False, self.player.level):
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

    def get_new_sword_rotation(self):
        if not self.player.game.use_mouse:
            return self.player.rotation
        else:
            p = config_dungeon["level_surface_position"]
            f = (-p[0], -p[1])
            v = utils.norm_vector_to_mouse(self.player.rect.center, f)
            a = v.to_angle()
            if 315 < a <= 360 or 0 <= a <= 45:
                return "right"
            elif 45 < a <= 135:
                return "down"
            elif 135 < a <= 225:
                return "left"
            else:
                return "up"

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
    name = "Enchanted Sword"
    description = """\
Found in an underground cave, stuck in a rock. Only the Chosen One shall use it.

1 Damage
Projectile: 0.5 Damage"""
    icon = imglib.load_image_from_file("images/sl/items/icons/EnchantedSwordI.png", after_scale=icon_size_t)
    image_r = all_rotations(imglib.load_image_from_file("images/sl/items/EnchantedSword.png", after_scale=Sword.size_r.right))
    def __init__(self, player):
        super().__init__(player)
        self.projectile = None

    def use(self):
        if self.cooldown <= 0:
            self.drawn = True
            self.rotation = self.get_new_sword_rotation()
            self.ticks_left = self.attack_length
            self.cooldown = round(self.ticks_left * 1.1)
            if self.projectile is None or self.projectile not in self.player.level.sprites:
                self.projectile = projectiles.EtherealSword(self.player.level, self.rect.topleft, 
                                                            centerpos=False, rotation=self.rotation)
                self.player.level.sprites.append(self.projectile)


class Boomerang(AbstractPlayerItem):
    name = "Boomerang"
    description = """\
IT ALWAYS COMES BACK!

0.75 Damage, decreasing with each hit"""
    icon_base = imglib.load_image_from_file("images/sl/items/Boomerang.png")
    icon_thrown = imglib.load_image_from_file("images/sl/items/BoomerangAfterThrow.png")
    dist = 250
    def __init__(self, player):
        super().__init__(player)
        self.thrown = False
        self.projectile = None
        self.icon = self.icon_base
        self.drawer = None

    def update(self):
        if self.projectile is not None and (self.projectile.destroyed or \
          self.projectile not in self.player.level.sprites):
            self.projectile.destroy()
            self.projectile = None
            self.thrown = False
            self.player.item_box.force_update = True
        if self.thrown:
            self.icon = self.icon_thrown
        else:
            self.icon = self.icon_base
        
    def use(self):
        if not self.thrown:
            level, pos = self.player.level, self.player.rect.center
            vec = self.player.best_heading_vector
            target = vec * self.dist + utils.Vector(*pos)
            self.projectile = projectiles.FlyingBoomerang(level, pos, source_sprite=self.player, target=target)
            self.player.level.sprites.append(self.projectile)
            self.thrown = True
            self.player.item_box.force_update = True

# ==== Staffs ====

class FireballStaff(AbstractPlayerItem):
    name = "Fireball Staff"
    description = """\
Conjures a fireball, without any mana cost. Amazing!

0.5 Damage
0.25 AOE Damage
Chance to set enemy aflame"""
    icon = imglib.load_image_from_file("images/sl/items/icons/FireballStaff.png", after_scale=icon_size_t)
    cooldown_length = 25
    def __init__(self, player):
        super().__init__(player)
        self.cooldown = 0

    def update(self):
        if self.cooldown >= 0:
            self.cooldown -= 1

    def use(self):
        if self.cooldown <= 0:
            self.cooldown = self.cooldown_length
            pos = self.player.rect.center
            vec = self.player.best_heading_vector
            proj = projectiles.Fireball(self.player.level, pos, norm_vector=vec)
            self.player.level.sprites.append(proj)

# ====== Edible ======

class Apple(BaseEdibleItem):
    name = "Apple"
    description = """\
Nice 'n' tasty

Heals 1 HP"""
    icon = imglib.load_image_from_file("images/sl/items/Apple.png", after_scale=icon_size_t)
    size = (16, 16)
    surface = imglib.load_image_from_file("images/sl/items/Apple.png", after_scale=size)
    points_healed = 1

class HealthPotion(BaseEdibleItem):
    name = "Health Potion"
    description = """\
It's redness ensures you that the potion is meant to heal you. Or is it?

Heals 4 HP"""
    icon = imglib.load_image_from_file("images/dd/pickups/HealthPotion.png", after_scale=icon_size_t)
    size = (16, 16)
    surface = imglib.load_image_from_file("images/dd/pickups/HealthPotion.png", after_scale=size)
    points_healed = 4



register = utils.Register.gather_type(AbstractPlayerItem, locals())

del register["BaseEdibleItem"]