import pygame

cpdef rect_cmove(object rect, int x, int y, object screen_rect):
    return rect.move(x, y).clamp(screen_rect)

cpdef level_impassable_collision(list layout, object rect, int col, int row):
    if layout[row][col].passable:
        return False
    else:
        return rect.colliderect(layout[row][col].rect)

imp_col = level_impassable_collision

cpdef move_in_level(list layout, dict moving, int row, int col, object rect, int move_speed, object screen_rect):
    cdef:
      int level_cols = len(layout[0])
      int level_rows = len(layout)
      bint lft_in = col > 0
      bint rgt_in = col + 1 < level_cols
      bint top_in = row > 0
      bint bot_in = row + 1 < level_rows
      object next_rect
      bint collided
    if moving["left"]:
        next_rect = rect_cmove(rect, -move_speed, 0, screen_rect)
        collided = False
        if lft_in and (imp_col(layout, next_rect, col - 1, row) or \
           (top_in and imp_col(layout, next_rect, col - 1, row - 1)) or \
           (bot_in and imp_col(layout, next_rect, col - 1, row + 1))):
            collided = True
            rect.left = layout[row][col - 1].rect.right
        if not collided:
            rect = next_rect

    if moving["right"]:
        next_rect = rect_cmove(rect, move_speed, 0, screen_rect)
        collided = False
        if rgt_in and (imp_col(layout, next_rect, col + 1, row) or \
           (top_in and imp_col(layout, next_rect, col + 1, row - 1)) or \
           (bot_in and imp_col(layout, next_rect, col + 1, row + 1))):
            collided = True
            rect.right = layout[row][col + 1].rect.left
        if not collided:
            rect = next_rect

    if moving["up"]:
        next_rect = rect_cmove(rect, 0, -move_speed, screen_rect)
        collided = False
        if top_in and (imp_col(layout, next_rect, col, row - 1) or \
           (lft_in and imp_col(layout, next_rect, col - 1, row - 1)) or \
           (rgt_in and imp_col(layout, next_rect, col + 1, row - 1))):
            collided = True
            rect.top = layout[row - 1][col].rect.bottom
        if not collided:
            rect = next_rect

    if moving["down"]:
        next_rect = rect_cmove(rect, 0, move_speed, screen_rect)
        collided = False
        if bot_in and (imp_col(layout, next_rect, col, row + 1) or \
           (lft_in and imp_col(layout, next_rect, col - 1, row + 1)) or \
           (rgt_in and imp_col(layout, next_rect, col + 1, row + 1))):
            collided = True
            rect.bottom = layout[row + 1][col].rect.top
        if not collided:
            rect = next_rect

    moving["left"] = moving["right"] = False
    moving["up"]   = moving["down"]  = False

    return rect

def get_tiles_next_to(object sprite):
    cdef:
        tuple pair = sprite.closest_tile_index
        int col = pair[0]
        int row = pair[1]
        int level_cols, level_rows
        bint lft, rgt, top, bot
    if pair not in sprite.next_to_cache:
        sprite.next_to_cache[pair] = []
        level_cols, level_rows = sprite.level.layout_size
        lft = rgt = top = bot = False
        if col > 0:
            lft = True; sprite.next_to_cache[pair].append((col - 1, row))
        if col + 1 < level_cols:
            rgt = True; sprite.next_to_cache[pair].append((col + 1, row))
        if row > 0:
            top = True;  sprite.next_to_cache[pair].append((col, row - 1))
        if row + 1 < level_rows:
            bot = True; sprite.next_to_cache[pair].append((col, row + 1))

        if lft and top: 
            sprite.next_to_cache[pair].append((col - 1, row - 1))
        if rgt and top: 
            sprite.next_to_cache[pair].append((col + 1, row - 1))
        if lft and bot: 
            sprite.next_to_cache[pair].append((col - 1, row + 1))
        if rgt and bot: 
            sprite.next_to_cache[pair].append((col + 1, row + 1))
    return sprite.next_to_cache[pair]