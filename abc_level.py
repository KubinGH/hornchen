import abc

class AbstractLevel(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def __init__(self):
        """
        Setup this level and initialize. Called every time
        it is created (from scratch).
        Note: the parent is meant to be set by the state
        that will handle this level, e.g. DungeonState.
        """
        self.sprites = []
        self.parent = None
        self.layout = self.get_layout_copy()

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