class BaseInventory:
    # Exceptionless: If inventory-manipulating operations fail,
    # no exceptions will be raised. Use return values to check
    # if they did.
    # Value used to represent an empty slot in the inventory
    empty_slot = None
    # Inheriting classes need to set this to an integer
    slots_count = None

    def __init__(self):
        self.slots = [self.empty_slot for _ in range(self.slots_count)]

    def update(self):
        pass

    @property
    def empty_slots(self):
        return self.slots.count(self.empty_slot)

    @property
    def full_slots(self):
        return self.slots_count - self.full_slots

    @property
    def full(self):
        return not self.empty_slots

    @property
    def first_empty(self):
        return self.slots.index(self.empty_slot) if not self.full else -1

    def add_item(self, item):
        if self.full: 
            return -1
        idx = self.first_empty
        self.slots[idx] = item
        return idx

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