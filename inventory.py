class BaseInventory:
    # Exceptionless: If inventory-manipulating operations fail,
    # no exceptions will be raised. Use return values to check
    # if they did. Exceptions could crash the game if things went wrong.
    empty_slot = None
    # Inheriting classes need to set this to an integer
    slots_count = None

    def __init__(self):
        self.slots = [self.empty_slot for _ in range(self.slots_count)]

    def update(self):
        pass

    @property
    def full_slots(self):
        return self.slots.count(self.empty_slot)

    @property
    def empty_slots(self):
        return self.slots_count - self.full_slots

    @property
    def full(self):
        return self.full_slots == self.slots

    def add_item(self, item):
        if self.full: 
            return -1
        first_empty = self.slots.index(self.empty_slot)
        self.slots[first_empty] = item
        return first_empty

    def remove_item(self, sought_item):
        for i, item in enumerate(self.slots):
            if item is sought_item:
                deleted_index = i
                break
        else:
            return -1
        self.slots[deleted_index] = self.empty_slot
        return deleted_index

    def pop_item(self, index):
        deleted = self.slots[index]
        self.slots[index] = self.empty_slot
        return deleted