import abc
import time

print("Load abstract base class of level")

class SpriteContainer(list):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setchange()

    def setchange(self):
        self.last_changed = time.clock()

    def append(self, *args, **kwargs):
        super().append(*args, **kwargs)
        self.setchange()

    def clear(self, *args, **kwargs):
        super().clear(*args, **kwargs)
        self.setchange()

    def extend(self, *args, **kwargs):
        super().extend(*args, **kwargs)
        self.setchange()

    def insert(self, *args, **kwargs):
        super().insert(*args, **kwargs)
        self.setchange()

    def pop(self, *args, **kwargs):
        try:
            super().pop(*args, **kwargs)
            self.setchange()
        except IndexError as e:
            print("Unhandled IndexError in SpriteContainer: {}".format(str(e)))

    def remove(self, *args, **kwargs):
        try:
            super().remove(*args, **kwargs)
            self.setchange()
        except ValueError as e:
            print("Unhandled ValueError in SpriteContainer: {}".format(str(e)))

class AbstractLevel(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def __init__(self):
        """
        Setup this level and initialize. Called every time
        it is created (from scratch).
        """
        self.sprites = SpriteContainer()
        self.particles = []
        self.layout = self.get_layout_copy()
        self._hostile_sprites = []; self._hcheck = self.sprites.last_changed
        self._friendly_sprites = []; self._fcheck = self.sprites.last_changed
        self._passive_sprites = []; self._pcheck = self.sprites.last_changed

    @abc.abstractmethod
    def get_layout_copy(self):
        """
        Return a 2d list of level tiles, that is used to 
        instantiate every level of this type.
        Create by e.g. using the leveltiles.parse_layout function
        with a string representation of the level layout, from 
        a text file from the levels directory.
        """

    @abc.abstractmethod
    def create_cache(self):
        """
        Cache this level for later use. If the player leaves
        a level, it is then cached and later loaded from the
        cache data (either in the same process or loaded
        from a save game).
        """

    @classmethod
    @abc.abstractmethod
    def load_from_cache(cls, cache):
        """
        Load a level from cache created by the create_cache method.
        Should be defined as a classmethod.
        """

    @abc.abstractmethod
    def stop(self):
        """
        Stop a level (pause). Return the result of the create_cache method.
        """

    @abc.abstractmethod
    def handle_events(self, events, pressed_keys, mouse_pos):
        """
        Handle the events inside this level, 
        e.g. unique key combinations.
        """

    @abc.abstractmethod
    def update(self):
        """
        Update this level. Should perform a tick on 
        all of the sprites.
        """

    @abc.abstractmethod
    def draw(self, screen):
        """
        Takes a surface as input. It is expected for
        the surface to be the same as last time this level
        was drawn, unless the level was changed - then the
        surface will filled black.
        """

    def get_sprites_if(self, predicate):
        return [sprite for sprite in self.sprites if predicate(sprite)]

    @property
    def hostile_sprites(self):
        if self.sprites.last_changed != self._hcheck:
            self._hostile_sprites = [sprite for sprite in self.sprites if sprite.hostile]
            self._hcheck = self.sprites.last_changed
        return self._hostile_sprites

    @property
    def friendly_sprites(self):
        if self.sprites.last_changed != self._fcheck:
            self._friendly_sprites = [sprite for sprite in self.sprites if sprite.friendly]
            self._fcheck = self.sprites.last_changed
        return self._friendly_sprites

    @property
    def passive_sprites(self):
        if self.sprites.last_changed != self._pcheck:
            self._passive_sprites = [sprite for sprite in self.sprites 
                                     if sprite.hostile is sprite.friendly is False]
            self._pcheck = self.sprites.last_changed
        return self._passive_sprites