from globals import *
from math import floor

#######################
###  MAP/COLLISION  ###
#######################

def load_layout(n = 0):
    '''Load level layout number n'''
    layout.clear()

    line_buffer = []

    # Copy file data into line buffer
    with open('layout.txt','r') as file:
        for line in file:
            line_buffer.append(line)

    # Reset dot count
    dot_count['eaten'] = 0
    dot_count['total'] = 0

    # Read maze layout
    r, c = 0, 0
    for l in range(n * MAZE_HEIGHT, (n+1) * MAZE_HEIGHT):
        line = line_buffer[l]
        row = []
        for char in line:
            #Add element to layout
            if char in FILE_FORMAT.keys():
                row.append(FILE_FORMAT[char])
                if FILE_FORMAT[char] in [COLL_DOT,COLL_POW]:
                    dot_count['total'] += 1
            else:
                if char == 'X':
                    start_pos['pacman'] = c, r + 0.5
                if char == 'B':
                    start_pos['blinky'] = c, r + 0.5
                if char == 'P':
                    start_pos['pinky'] = c, r + 0.5
                if char == 'I':
                    start_pos['inky'] = c, r + 0.5
                if char == 'C':
                    start_pos['clyde'] = c, r + 0.5
                row.append(COLL_VOID) # Other char

            c += 1

        layout.append(row)
        c = 0
        r += 1

def read_map(x, y):
    return layout[floor(y)] [floor(x)]

def is_wall(x, y):
    return read_map(x, y) == COLL_WALL

def is_gate(x, y):
    return read_map(x, y) == COLL_GATE

def is_dot(x, y):
    return read_map(x, y) == COLL_DOT

def is_pow(x, y):
    return read_map(x, y) == COLL_POW

def is_tunnel(x, y):
    return read_map(x, y) == COLL_TUNNEL

def dir_free(x, y, direction, offset = 0):
    '''Check for a collision with a wall when turning'''
    arg_x = x + offset*intcos(direction)
    arg_y = y + offset*intsin(direction)

    if not is_wall(arg_x + intcos(direction), arg_y + intsin(direction)):
        return True

    return False

def dir_gate(x, y, direction, offset = 0):
    '''Check for a collision with the gate when turning'''
    arg_x = x + offset*intcos(direction)
    arg_y = y + offset*intsin(direction)

    if is_gate(arg_x + intcos(direction), arg_y + intsin(direction)):
        return True

    return False

def write_map(x, y, val):
    layout[floor(y)] [floor(x)] = val

def snap_grid(x, y):
    '''Snap coordinates (in pixels) to the grid'''
    new_x = TILE_SIZE * (floor(x / TILE_SIZE) + 1/2)
    new_y = TILE_SIZE * (floor(y / TILE_SIZE) + 1/2)
    return new_x, new_y

def grid_snapped(x, y, tolerance=GRID_TOLERANCE):
    '''Checks if coordinates (in pixels) are snapped on the grid'''
    check_x = (floor(x / TILE_SIZE) + 1/2) * TILE_SIZE
    check_y = (floor(y / TILE_SIZE) + 1/2) * TILE_SIZE
    return distance(x, y, check_x, check_y) <= tolerance * TILE_SIZE

def ghost_exception(x, y, dir):
    '''Areas where ghosts can't go up'''
    return dir == 1 and game_settings['maze']== 0 and x in range(11, 17) and (y in range(11, 12) or y in range(23, 24))

def ghost_collide(x,y):
    for g in ghosts:
        gx, gy = get_tile(g.x, g.y)
        if x == gx and y == gy:
            return g
    return None

def get_fruit_type(n):
    return FRUIT_TYPE[min(n, len(FRUIT_TYPE)-1)]
