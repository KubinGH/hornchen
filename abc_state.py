import abc
import pygame

print("Load abstract base class of state")

class AbstractGameState(metaclass=abc.ABCMeta):
    # laziness makes the state force 60 FPS limit, so that it doesn't
    # overuse the CPU doing literally nothing
    # doesn't do anything when the FPS limit is on
    lazy_state = False
    # e.g. DungeonState has this set to True, 
    # all states that are a parent of a level should too
    level_state = False
    # shows mouse when this state is enabled
    use_mouse = False
    # only fill a part of the screen automatically, a rect
    flags = set()
    @abc.abstractmethod
    def __init__(self, game):
        """
        Define the most important attributes of this state.
        Run every time a new state of this type is created.
        """
        self.game = game
        self.paused = False
        self.deactivated = False
        if self.use_mouse:
            pygame.mouse.set_visible(True)

    def cleanup(self):
        """
        Called when this thread is not going to be used anymore
        (Either its type won't be used again or we will use a new copy later)
        Delete all traces of this state from the game instance
        """
        print("Deactivated state", self.__class__.__name__)
        self.deactivated = True
        if self.use_mouse and not self.game.vars["forced_mouse"] and not self.game.top_state.use_mouse:
            pygame.mouse.set_visible(False)
    
    def pause(self):
        """
        Pause this state for now. It will be later unpaused with 
        the resume method. Make sure any other state won't have problems
        when dealing with the game instance.
        """
        print("Paused state", self.__class__.__name__)
        self.paused = True
        if self.use_mouse and not self.game.vars["forced_mouse"] and not self.game.top_state.use_mouse:
            pygame.mouse.set_visible(False)
        
    def resume(self):
        """
        Unpause this state after a period of pause.
        Reinitialize anything that this thread needs in the game instance.
        """
        print("Resumed state", self.__class__.__name__)
        self.paused = False
        if self.use_mouse:
            pygame.mouse.set_visible(True)

    @abc.abstractmethod
    def handle_events(self):
        """
        Handle user input or any other kinds of events.
        Called every tick.
        """

    @abc.abstractmethod
    def update(self):
        """
        Handle this state's game logic, and any other things that need
        updating after the last tick.
        Called every tick.
        """

    @abc.abstractmethod
    def draw(self, screen):
        """
        Draw this state to screen. Do not update the screen
        through here. Return a list of rectangles (selective update)
        or None (complete update).
        """