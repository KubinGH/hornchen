import math
import random
from enum import Enum

import pygame

from colors import Color
import json_ext as json
import imglib
from basesprite import BaseSprite
from animation import Animation
import utils
import easing
import particles
import statuseffects

print("Load projectiles")

class TickStatus(Enum):
    Ok = 0
    Destroy = 1

class DestroyReason(Enum):
    OutsideLevel = 0
    Collision = 1
    DamageDeal = 2

# Base

class BaseProjectile(BaseSprite):
    hostile = friendly = False
    cachable = False
    surface = None
    size = (30, 30)
    surface = imglib.get_missing_surface(size)
    speed = 3
    damage = 0.5
    def __init__(self, level, pos, *, centerpos=True):
        super().__init__()
        self.level, self.pos = level, pos
        if centerpos:
            self.rect = pygame.Rect((0, 0), self.size)
            self.rect.center = self.pos
        else:
            self.rect = pygame.Rect(self.pos, self.size)
        self.destroy_reason = None
        self.destroyed = False

    def destroy(self):
        self.level.sprites.remove(self)
        self.destroyed = True

    def simple_tick(self):
        destroy = False
        if not self.inside_level:
            destroy = True
            self.destroy_reason = DestroyReason.OutsideLevel
        elif self.get_collision_nearby():
            destroy = True
            self.destroy_reason = DestroyReason.Collision
        elif self.simple_deal_damage(once=True):
            destroy = True
            self.destroy_reason = DestroyReason.DamageDeal
        if destroy:
            self.destroy()
            return TickStatus.Destroy
        return TickStatus.Ok


# Parents

# Projectile that flies in a given left-right-up-down direction
class SimpleProjectile(BaseProjectile):
    base_size = base_image = image_r = size_r = None
    def __init__(self, level, pos, *, centerpos=True, rotation):
        self.rotation = rotation
        self.surface, self.size = self.image_r[self.rotation], self.size_r[self.rotation]
        super().__init__(level, pos, centerpos=centerpos)

    def update(self):
        if self.rotation == "left":
            self.rect.x -= self.speed
        elif self.rotation == "right":
            self.rect.x += self.speed
        elif self.rotation == "up":
            self.rect.y -= self.speed
        elif self.rotation == "down":
            self.rect.y += self.speed
        if self.simple_tick() is TickStatus.Destroy:
            return

# Projectile that may fly in any direction.
class OmniProjectile(BaseProjectile):
    rotating = False
    base_image = None
    speed = 1
    def __init__(self, level, pos, *, centerpos=True, norm_vector):
        self.norm_vector = norm_vector
        self.velocity = self.norm_vector * self.speed
        self.surface = self.base_image
        if self.rotating:
            self.surface = imglib.rotate(self.surface, -int(self.norm_vector.to_angle()))
        self.size = self.surface.get_size()
        super().__init__(level, pos, centerpos=centerpos)
        self.xbuf, self.ybuf = self.rect.topleft
        self.velx, self.vely = self.velocity.x, self.velocity.y

    @classmethod
    def from_angle(cls, level, pos, angle):
        return cls(level, pos, norm_vector=utils.Vector.from_angle(angle))

    @classmethod
    def towards(cls, level, pos, target):
        return cls(level, pos, norm_vector=utils.Vector.from_points(target, pos).normalize())        

    def update(self):
        self.xbuf += self.velx
        self.ybuf += self.vely
        self.rect.x, self.rect.y = self.xbuf, self.ybuf
        if self.simple_tick() is TickStatus.Destroy:
            return

# Projectile that may fly in any direction, provided with an easing function.
class EasedProjectile(BaseProjectile):
    dist = 100
    dist_diff = 20
    length = 40
    def __init__(self, level, pos, *, centerpos=True, norm_vector, ease=easing.ease_quintic_out):
        super().__init__(level, pos, centerpos=centerpos)
        self.norm_vector = norm_vector
        self.ease = ease
        self.set_ease_args()
        self.time = 0

    def update(self):
        self.rect.x = self.ease(self.time, *self.ease_args_x)
        self.rect.y = self.ease(self.time, *self.ease_args_y)
        self.time += 1
        if self.time > self.length:
            self.destroy()
            return
        if self.simple_tick() is TickStatus.Destroy:
            return

    def set_ease_args(self):
        self.diff = random.randint(-self.dist_diff, self.dist_diff)
        self.move = self.norm_vector * (self.dist + self.diff) 
        self.ease_args_x = (self.rect.x, self.move.x, self.length)
        self.ease_args_y = (self.rect.y, self.move.y, self.length)        

# Children

class EtherealSword(SimpleProjectile):
    hostile = False
    friendly = True
    base_size = (30, 12)
    base_image = imglib.load_image_from_file("images/sl/projectiles/EtherealSword.png", after_scale=base_size)
    image_r = imglib.all_rotations(base_image)
    size_r = imglib.ValueRotationDependent(*[surface.get_size() for surface in image_r.as_list])
    speed = 10
    damage = 0.5

class Fireball(OmniProjectile):
    hostile = False
    friendly = True
    rotating = False
    base_size = (16, 16)
    base_image = imglib.load_image_from_file("images/sl/projectiles/Fireball.png", after_scale=base_size)
    animation_frames = 5
    speed = 14
    particle_spread = 35
    particle_speed = 5
    damage = 0.5
    aoe = 40
    damage_aoe = 0.25
    caused_effect = statuseffects.Burning
    effect_length = 90
    aoe_effect_chance = 1 / 2
    def __init__(self, level, pos, *, centerpos=True, norm_vector):
        super().__init__(level, pos, centerpos=centerpos, norm_vector=norm_vector)
        anim_size = (self.base_size[0] * self.animation_frames, self.base_size[1])
        animation_surf = imglib.load_image_from_file("images/sl/projectiles/FireballAnim.png", after_scale=anim_size)
        self.animation = Animation.from_surface_w(animation_surf, self.base_size[0], 5)

    def update(self):
        super().update()
        self.animation.update()
        self.surface = self.animation.surface

    def destroy(self):
        super().destroy()
        norm, spread = self.norm_vector, self.particle_spread
        # Different particles depending on the destroy_reason
        # (collision - bouncing off the wall, damage deal - around the target sprite, 
        # otherwise - assume the projectile is out-of-view anyways and don't spawn particles)
        for i in range(random.randint(5, 8)):
            if self.destroy_reason == DestroyReason.Collision:
                vel = utils.Vector.random_spread(norm, spread).opposite() * self.particle_speed
                source_sprite = self
            elif self.destroy_reason == DestroyReason.DamageDeal:
                vel = utils.Vector.uniform(self.particle_speed)
                source_sprite = self.last_attacked_sprite
            else:
                break
            color = random.choice((Color.Yellow, Color.Orange, Color.Red))
            p = particles.Particle.from_sprite(source_sprite, 4, vel, 30, color)
            self.level.particles.append(p)
        # AOE Damage
        for sprite in self.get_local_enemy_sprites():
            if utils.dist(self.rect.center, sprite.rect.center) < self.aoe:
                sprite.take_damage(self.damage_aoe)
                if random.uniform(0, 1) <= self.aoe_effect_chance:
                    tick = self.level.parent.game.ticks
                    effect = self.caused_effect(sprite, tick, self.effect_length)
                    sprite.status_effects.add(effect)

    def deal_damage(self, sprite):
        super().deal_damage(sprite)
        tick = self.level.parent.game.ticks
        effect = self.caused_effect(sprite, tick, self.effect_length)
        sprite.status_effects.add(effect)

class Ember(EasedProjectile):
    hostile = False
    friendly = True
    size = (4, 6)
    surface = imglib.load_image_from_file("images/sl/projectiles/Ember.png", after_scale=size)
    dist = 100
    dist_diff = 20
    length = 50
    damage = 0.25
    caused_effect = statuseffects.Burning
    effect_length = 60
    effect_chance = 1 / 2
    def deal_damage(self, sprite):
        super().deal_damage(sprite)
        if random.uniform(0, 1) <= self.effect_chance:
            tick = self.level.parent.game.ticks
            effect = self.caused_effect(sprite, tick, self.effect_length)
            sprite.status_effects.add(effect)

class FlyingBoomerang(OmniProjectile):
    hostile = False
    friendly = True
    base_size = (16, 16)
    base_image = imglib.load_image_from_file("images/sl/items/Boomerang.png", after_scale=base_size)
    damage = 0 # Override normal damage deal
    max_damage = 0.75
    damage_loss_mul = 0.6
    rotation_speed = 7
    base_length = 40
    back_speed = 10
    curve_spread = 30
    curve_point = 0.9
    curve_back_spread = 60
    curve_back_point = 0.2
    def __init__(self, level, pos, *, centerpos=True, source_sprite, target):
        super().__init__(level, pos, centerpos=centerpos, norm_vector=utils.Vector(0, 0))
        self.source_sprite = source_sprite # It always comes back!
        self.target = target
        self.dist = utils.dist(self.pos, self.target)
        self.surface = self.base_image
        self.length = self.base_length
        self.curve_points = None
        self.curve = self.new_curve()
        self.time_trans = lambda t: utils.translate_to_zero_to_one_bounds(t, (0, self.length))
        self.time = 0
        self.rotation = 0
        self.coming_back = False
        self.coming_back_curve = False
        self.hit = set()
        self.act_damage = self.max_damage
        self.last_source_sprite_pos = self.source_sprite.rect.topleft
        self.last_adist = self.dist

    def update(self):
        self.rotation += self.rotation_speed; self.rotation %= 360
        self.surface = imglib.rotate(self.base_image, self.rotation)
        new_rect = self.surface.get_rect(); new_rect.center = self.rect.center
        self.rect = new_rect
        for sprite in self.get_local_enemy_sprites():
            if sprite not in self.hit and self.rect.colliderect(sprite.rect):
                self.hit.add(sprite)
                sprite.take_damage(self.act_damage)
                self.act_damage *= self.damage_loss_mul
        if self.simple_tick() == TickStatus.Destroy and \
          (self.destroy_reason != DestroyReason.DamageDeal and self.act_damage > 0.2):
            if self.rect.colliderect(self.source_sprite.rect):
                super().destroy()
                return
            self.coming_back = True
        else:
            self.destroy_reason = None
        if (self.coming_back or self.coming_back_curve) and self.rect.colliderect(self.source_sprite.rect):
            super().destroy()
            return
        if self.coming_back:
            self.curve = None
            self.curve_points = None
            # Move in a straight line ignoring everything
            vec_back = utils.Vector.from_points(self.source_sprite.rect.center, self.rect.center)
            move = self.back_speed * vec_back.normalize()
            self.xbuf += move.x
            self.ybuf += move.y
            self.rect.centerx, self.rect.centery = self.xbuf, self.ybuf
        else:
            # Move in a curve, collision breaks this state
            change = self.source_sprite.rect.topleft != self.last_source_sprite_pos
            if self.coming_back_curve and change:
                self.curve = self.new_back_curve()
            if self.time > self.length:
                if not self.coming_back_curve:
                    self.time = 0
                    self.curve = self.new_back_curve()
                    self.coming_back_curve = True
                else:
                    self.coming_back = True
            else:
                curve_pos = self.curve(self.time_trans(self.time))
                self.xbuf, self.ybuf = self.rect.center = (curve_pos.x, curve_pos.y)
                self.time += 1
        self.last_source_sprite_pos = self.source_sprite.rect.topleft

    def destroy(self):
        pass

    def new_curve(self):
        p = utils.break_segment(self.rect.center, self.target,
                                self.curve_spread, self.curve_point)
        self.curve_points = p
        return utils.bezier(*p)

    def new_back_curve(self):
        # Make the boomerang go faster if the player is running away from it
        # THERE'S NO ESCAPE
        # IT WILL COME BACK
        adist = utils.dist(self.rect.center, self.source_sprite.rect.center)
        if adist < self.last_adist:
            d = self.dist / adist
            if d > 1: d = 1 / d
            d = d ** (1/10)
            d = max(d, 0.2)
            self.length = self.base_length * d
            self.time = (self.time - 1) * (self.base_length / self.length)
            self.time = max(self.time, 1)
            self.last_adist = adist
        p = utils.break_segment(self.rect.center, self.source_sprite.rect.center, 
                                self.curve_back_spread, self.curve_back_point)
        self.curve_points = p
        return utils.bezier(*p)

class Arrow(OmniProjectile):
    rotating = True
    hostile = True
    friendly = False
    base_size = (15, 3)
    base_image = imglib.load_image_from_file("images/sl/projectiles/Arrow.png", after_scale=base_size)
    speed = 10
    damage = 0.5


register = utils.Register.gather_type(BaseProjectile, locals())