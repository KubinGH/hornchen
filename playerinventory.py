from inventory import BaseInventory
import playeritems

print("Load player inventory")

class PlayerInventory(BaseInventory):
    slots_count = 32
    def __init__(self, player):
        super().__init__()
        self.player = player

    def handle_events(self, events, pressed_keys, mouse_pos):
        for item in self.slots:
            if item is not self.empty_slot:
                item.handle_events(events, pressed_keys, mouse_pos)

    def update(self):
        for item in self.slots:
            if item is not self.empty_slot:
                item.update()

    # Unused
    def draw_items(self, screen, pos_fix=(0, 0)):
        for item in self.slots:
            if item is not self.empty_slot:
                item.draw(screen, pos_fix)


