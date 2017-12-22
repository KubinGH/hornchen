import random
from enum import Enum

import pygame

from colors import Color, invert_color
import imglib
import utils
import particles

print("Load status effects")

class StatusType(Enum):
    Ice = 0
    Fire = 1
    Poison = 2
    Healing = 3
    Other = 100

status_type_cancels = {k: [] for k in StatusType.__members__.values()}
status_type_cancels.update({
    StatusType.Fire: [StatusType.Ice]
})

# Container for status effects,
# handles their updates, expiration and new effects
# (that may cancel each other)
class StatusEffects:
    def __init__(self, parent, get_tick=None):
        self.parent = parent
        self.get_tick = get_tick
        self.effects = []

    def update(self, tick=None):
        if tick is None: tick = self.get_tick()
        for effect in self.effects.copy():
            effect.update()
            if effect.ends_on is not None and tick >= effect.ends_on:
                effect.on_end()
                self.effects.remove(effect)   

    def has(self, cls):
        search = [e for e in self.effects if isinstance(e, cls)]
        return search[0] if search else None

    def add(self, effect):
        s_effect = self.has(type(effect))
        stypes = [e.stype for e in self.effects]
        # Remove all effects that this effect cancels
        for e in self.effects.copy():
            if e.stype in status_type_cancels[effect.stype]:
                e.on_end()
                self.effects.remove(e)
        # Remove this effect if it is cancelled by any others
        for stype in stypes:
            if effect.stype in status_type_cancels[stype]:
                return
        # If an effect of the same type was not inflicted
        # already, initialize this one
        # Otherwise, refresh the duration of the old one
        if s_effect is None:
            effect.on_start()
            self.effects.append(effect)
        else:
            s_effect.ends_on = effect.ends_on

    def clear(self):
        for effect in self.effects:
            effect.on_end()
        self.effects.clear()

    def create_cache(self):
        return [{
            "type": type(effect),
            "starts_on": effect.starts_on,
            "lasts": effect.lasts,
            "ends_on": effect.ends_on
        } for effect in self.effects]

    def load_cache(self, cache):
        for cdict in cache:
            e = cdict["type"](self.parent, cdict["starts_on"], cdict["lasts"])
            e.ends_on = cdict["ends_on"]
            e.on_start()
            self.effects.append(e)



class BaseStatusEffect:
    tinting = False
    stype = StatusType.Other
    move_speed_mul = damage_per_tick = None
    particle_chance = particle_size = particle_speed = particle_length = particle_color = None
    tint = None
    def __init__(self, parent, starts_on, lasts):
        self.parent = parent
        self.starts_on = starts_on
        self.lasts = lasts
        self.ends_on = self.starts_on + self.lasts
        # Tinting should be used with only one effect active at once
        # So that two tinting effects should cancel each other
        # Otherwise, original surface corruption may occur
        if self.tint is not None:
            self.tinted_parent_surface = imglib.tint(parent.surface, self.tint)
        else:
            self.tinted_parent_surface = None

    def update(self):
        pass

    def spawn_particle(self):
        new = particles.Particle.from_sprite
        p = new(self.parent, 4, utils.Vector.uniform(self.particle_speed),
                self.particle_length, self.particle_color)
        self.parent.level.particles.append(p)

    def on_start(self):
        if self.tinted_parent_surface is not None:
            self.parent.surface = self.tinted_parent_surface

    def on_end(self):
        if self.tinted_parent_surface is not None:
            self.parent.surface = self.parent.surface_default

class Chilled(BaseStatusEffect):
    stype = StatusType.Ice
    move_speed_mul = 0.6
    particle_chance = 1 / 10
    particle_size = 4
    particle_speed = 1
    particle_length = 50
    particle_color = Color.lBlue
    tint = (180, 180, 255)
    def update(self):
        super().update()
        self.parent.move_speed *= self.move_speed_mul
        if random.uniform(0, 1) <= self.particle_chance:
            self.spawn_particle()

class Burning(BaseStatusEffect):
    stype = StatusType.Fire
    move_speed_mul = 1.1
    damage_per_tick = 1 / 200 # 0.3 HP per second
    particle_chance = 1 / 7
    particle_size = 2
    particle_speed = 3
    particle_length = 40
    particle_color = Color.Red
    particle_colors = (Color.Red, Color.Orange, Color.Yellow)
    tint = (255, 180, 180)
    def update(self):
        super().update()
        self.parent.move_speed *= self.move_speed_mul
        self.parent.take_damage(self.damage_per_tick)
        if random.uniform(0, 1) <= self.particle_chance:
            self.particle_color = random.choice(self.particle_colors)
            self.spawn_particle()

class Regeneration(BaseStatusEffect):
    stype = StatusType.Healing
    heal_per_tick = 1 / 80 # 3/4 HP per second
    def update(self):
        super().update()
        self.parent.heal(self.heal_per_tick)

register = utils.Register.gather_type(BaseStatusEffect, locals())