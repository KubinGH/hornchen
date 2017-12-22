import math
import random

import pygame

from abc_spell import AbstractSpell
from basesprite import BaseSprite
from colors import Color
import imglib
import utils
import projectiles
import particles
import statuseffects

print("Load spells")

base_icon_size = (32, 32)

# Check if the caster has enough mana,
# and if so, remove it and cast the spell.
def requires_mana(points):
    def wrapper(function):
        def decorated(self, *args, **kwargs):
            if self.player.mana_points >= points:
                self.player.mana_points -= points
                return function(self, *args, **kwargs)
            else:
                self.cast_this_tick = False
        return decorated
    return wrapper

# Check if the caster has enough mana,
# remove it or add the cost to the buffer,
# then cast the spell.
# Has support for floating point mana usage. 
def requires_channel_mana(points):
    def wrapper(function):
        def decorated(self, *args, **kwargs):
            if self.player.mana_points >= points - self.buffer:
                self.buffer += points
                i, self.buffer = divmod(self.buffer, 1)
                self.player.mana_points -= i
                self.player.mana_points = int(self.player.mana_points)
                return function(self, *args, **kwargs)
            else:
                self.cast_this_tick = False
        return decorated
    return wrapper

class ChanneledSpell(AbstractSpell):
    special_cast = True
    mana_cost = 0
    mana_channel_cost = None
    def __init__(self, player):
        super().__init__(player)
        self.buffer = 0

    def can_cast(self, events, pressed_keys, mouse_pos, controls):
        return pressed_keys[controls.Keys.CastSpell] or pygame.mouse.get_pressed()[2]


class Embers(AbstractSpell):
    icon = imglib.load_image_from_file("images/pt/fire-arrows-2.png", after_scale=base_icon_size)
    tree_pos = (0, 0) # Position from center
    mana_cost = 10

    count_min, count_max = 1, 3
    angle_spread = 10
    mul_if_moving = 2

    @requires_mana(mana_cost)
    def cast(self):
        level = self.player.level
        mid_angle = self.player.best_heading_vector.to_angle()
        level = self.player.level
        pos = self.player.rect.center
        count = random.randint(self.count_min, self.count_max)
        any_move = any(self.player.moving.values())
        for i in range(count):
            vec = utils.Vector.from_angle(mid_angle + random.randint(-self.angle_spread, self.angle_spread))
            projectile = projectiles.Ember(level, pos, norm_vector=vec)
            if any_move:
                projectile.dist *= self.mul_if_moving
                projectile.set_ease_args()
            level.sprites.append(projectile)


class Fireball(AbstractSpell):
    icon = imglib.load_image_from_file("images/pt/fireball-red-2.png", after_scale=base_icon_size)
    tree_pos = (0, -100)
    mana_cost = 20

    @requires_mana(mana_cost)
    def cast(self):
        projectile = projectiles.Fireball(self.player.level, self.player.rect.center, 
                                          norm_vector=self.player.best_heading_vector)
        self.player.level.sprites.append(projectile)


class PoisonRune(AbstractSpell):
    icon = imglib.load_image_from_file("images/pt/shielding-acid-3.png", after_scale=base_icon_size)
    tree_pos = (-100, 0)
    mana_cost = 25

    count_min, count_max = 2, 4
    dist = 20

    class Rune(BaseSprite):
        friendly = True
        hostile = False
        cachable = False
        size = (20, 20)
        damage = 0.5
        aoe = 50
        damage_aoe = 0.25
        surface = imglib.load_image_from_file("images/sl/spells/RunePoison.png", after_scale=size)
        def __init__(self, level, pos):
            super().__init__()
            self.level = level
            self.rect = pygame.Rect((0, 0), self.size)
            self.rect.center = pos

        def update(self):
            if self.simple_deal_damage():
                self.level.sprites.remove(self)
                for i in range(random.randint(4, 7)):
                    p = particles.Particle.from_sprite(self, 4, utils.Vector.uniform(3), 50, Color.Green)
                    self.level.particles.append(p)
                for sprite in self.level.hostile_sprites:
                    if utils.dist(self.rect.center, sprite.rect.center) < self.aoe:
                        sprite.take_damage(self.damage_aoe)

    @requires_mana(mana_cost)
    def cast(self):
        level = self.player.level
        pos = self.player.rect.center
        vec = self.player.best_heading_vector
        rune = self.Rune(level, (pos[0] + vec.x * self.dist, pos[1] + vec.y * self.dist))
        level.sprites.append(rune)


class IceBeam(ChanneledSpell):
    icon = imglib.load_image_from_file("images/pt/beam-blue-2.png", after_scale=base_icon_size)
    tree_pos = (100, 0)
    mana_channel_cost = 0.25

    cooldown = 1

    # If it works, it ain't broken.
    class BeamProjectile(projectiles.OmniProjectile):
        rotating = True
        hostile = False
        friendly = True
        base_size = (10, 5)
        base_image = imglib.load_image_from_file("images/sl/projectiles/BeamBlue.png", after_scale=base_size)
        speed = base_size[0] - 1
        damage = 0.003
        particle_chance = 1 / 4
        particle_spread = 30
        particle_speed = 2
        charged_particle_chance = 1 / 100
        caused_effect = statuseffects.Chilled
        effect_length = 120
        def __init__(self, level, pos, *, centerpos=True, norm_vector, charged=True, retain=lambda: True, reason=None):
            super().__init__(level, pos, centerpos=centerpos, norm_vector=norm_vector)
            self.charged = charged
            self.retain = retain
            self.reason = reason
            self.moving = True
            # Used to make the beam go deeper into the wall after collision
            self.destroy_on_next = False
        def update(self):
            if self.moving:
                self.xbuf += self.velx
                self.ybuf += self.vely
                self.rect.x, self.rect.y = self.xbuf, self.ybuf
            else:
                self.simple_deal_damage()
            if self.reason is None:        
                if self.charged and random.uniform(0, 1) <= self.charged_particle_chance:
                    p = particles.Particle.from_sprite(self, 3, utils.Vector.uniform(1), 50, Color.lBlue)
                    self.level.particles.append(p)
            elif random.uniform(0, 1) <= self.particle_chance:
                norm = self.norm_vector
                spread = self.particle_spread
                source_sprite = self
                if self.reason == projectiles.DestroyReason.Collision:
                    vel = utils.Vector.random_spread(norm, spread).opposite() * self.particle_speed
                elif self.reason == projectiles.DestroyReason.DamageDeal:
                    vel = utils.Vector.uniform(self.particle_speed)
                    source_sprite = self.last_attacked_sprite
                else:
                    vel = utils.Vector(0, 0)
                p = particles.Particle.from_sprite(source_sprite, 4, vel, 40, Color.lBlue)
                self.level.particles.append(p)
        def draw(self, screen, pos_fix=(0, 0)):
            super().draw(screen, pos_fix)            
            if not self.retain():
                self.destroy()
        def deal_damage(self, sprite):
            super().deal_damage(sprite)
            tick = self.level.parent.game.ticks
            eff = self.caused_effect(sprite, tick, self.effect_length)
            sprite.status_effects.add(eff)

    def __init__(self, player):
        super().__init__(player)
        self.next_beam = self.cooldown
        self.stationary_time = 0
        self.last_tick_cast = -1
        self.last_vec = None
        self.last_pos = None
        self.last_col = False
        self.beams = []

    @requires_channel_mana(mana_channel_cost)
    def cast(self):
        level = self.player.level
        vec = self.player.best_heading_vector
        pos = self.player.rect.center
        if not any(self.player.moving.values()) and self.player.game.ticks == self.last_tick_cast + 1:
            self.stationary_time += 1
        else:
            self.stationary_time = 0
        
        dest = False
        col = False
        any_beam = None
        ens = []
        if self.beams:
            any_beam = self.beams[0]
            ens = any_beam.get_local_enemy_sprites() 
        if self.beams and not any_beam in self.player.level.sprites:
            dest = True
        if not dest and self.last_vec != vec or self.last_pos != pos:
            dest = True
        if not dest and self.beams and ens:
            for b in self.beams:
                for e in ens:
                    if b.rect.colliderect(e.rect):
                        dest = True
                        col = True
                        break
                else:
                    continue
                break
        if not dest and not col and self.last_col:
            dest = True
        if not dest and self.stationary_time >= 60 and not self.last_charged:
            dest = True
        if dest:
            self.destroy_beams()
        self.repopulate_beams()
        
        self.last_tick_cast = self.player.game.ticks
        self.last_vec = vec
        self.last_pos = pos
        self.last_col = col
        self.last_charged = self.stationary_time >= 60

    def destroy_beams(self):
        for b in self.beams:
            if not b.destroyed:
                b.destroy()
        self.beams.clear()

    def repopulate_beams(self):
        level = self.player.level
        vec = self.player.best_heading_vector
        pos = self.player.rect.center      
        i = 0
        added = []
        hit = []
        stop_on_next = False
        first_collide = False
        while not stop_on_next:
            p = self.BeamProjectile(level, pos, norm_vector=vec, charged=self.stationary_time >= 60,
                                    retain=(lambda: self.cast_this_tick))
            for v in range(i):
                p.xbuf += p.velx
                p.ybuf += p.vely
            p.rect.x, p.rect.y = p.xbuf, p.ybuf
            if not p.inside_level:
                break
            if p.get_collision_nearby():
                p.reason = projectiles.DestroyReason.Collision
                stop_on_next = True
            for sprite in p.get_local_enemy_sprites():
                if sprite in hit:
                    continue
                if p.rect.colliderect(sprite.rect):
                    p.last_attacked_sprite = sprite
                    p.reason = projectiles.DestroyReason.DamageDeal
                    hit.append(sprite)
                    sprite.take_damage(p.damage)
                    if not p.charged or len(hit) >= 3:
                        stop_on_next = True
                        break
            for sprite in self.beams:
                if p.rect.colliderect(sprite.rect):
                    if i == 0:
                        first_collide = True
                    stop_on_next = True
                    break
            if first_collide:
                break
            added.append(p)
            i += 1
        for a in added:
            a.moving = False
            level.sprites.append(a)
            self.beams.append(a)

register = utils.Register.gather_type(AbstractSpell, locals())
del register["ChanneledSpell"]

tree_border = 2
for k, v in register.items():
    if v.icon is None:
        continue
    v.icon_dim = imglib.dim_surface(v.icon, 125)
    v.icon_circle = imglib.in_circle(v.icon, tree_border, Color.White)
    v.icon_circle_dim = imglib.in_circle(v.icon_dim, tree_border, Color.White)
    v.icon_circle_select = imglib.in_circle(v.icon, tree_border, Color.Yellow)
    v.icon_circle_dim_select = imglib.in_circle(v.icon_dim, tree_border, Color.Yellow)