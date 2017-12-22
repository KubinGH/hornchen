import random
import levels

print("Load map generator")

def generate_map(dest, maze_gen):
    maze = maze_gen.data
    for row, irow in enumerate(maze):
        for col, tile in enumerate(irow):
            if tile: continue
            #left, right, up, down
            entries = [
                col > 0 and not maze[row][col-1],
                col + 1 < maze_gen.width and not maze[row][col+1],
                row > 0 and not maze[row-1][col],
                row + 1 < maze_gen.height and not maze[row+1][col]
            ]
            val = entries[0] * 8 + entries[1] * 4 + entries[2] * 2 + entries[3]
            level = random.choice(levels.leveldict[val])
            dest[row][col] = level
    scol, srow = maze_gen.start_pos
    dest[scol][srow] = levels.StartLevel