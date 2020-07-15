from globals import *
from map import *
from random import choice
from netgame import GhostData

#######################
###     GHOSTS      ###
#######################

class Ghost:

    move_speed = 4/3
    anim_spd = 1/12
    anim_max = 2
    xoffset = TILE_SIZE
    yoffset = TILE_SIZE
    # Starting positions
    start_direction  = {'blinky':2, 'pinky':3, 'inky':3, 'clyde':3}
    start_speed = {'blinky':move_speed, 'pinky':0, 'inky':0, 'clyde':0}
    # Target tiles for scatter mode
    scatter_target = {'blinky':(25,-2), 'pinky':(2,-1), 'inky':(27,31), 'clyde':(0,31)}
    # Dot limits for leaving the ghost house
    dot_limit = [{'blinky':-1, 'pinky':0, 'inky':30, 'clyde':90},\
    {'blinky':-1, 'pinky':0, 'inky':0, 'clyde':50},\
    {'blinky':-1, 'pinky':0, 'inky':0, 'clyde':0}]

    # Modes when starting the level
    default_state = {'blinky':'scatter', 'pinky':'house', 'inky':'house', 'clyde':'house'}
    # Position on the sprite sheet
    color = {'blinky':0, 'pinky':1, 'inky':2, 'clyde':3}
    scared_clock = 0

    # Scatter / chase durations
    state_durations = [ [7, 20, 7, 20, 5, 20, 5, -1], [7, 20, 7, 20, 5, -1], [5, 20, 5, 20, 5, -1] ]
    states =  ['scatter', 'chase', 'scatter', 'chase','scatter', 'chase','scatter', 'chase']
    ghost_phase = -1
    ghost_state = 'scatter'
    ghost_clock = 0

    def __init__(self, type, x=14, y=11.5):
        self.x, self.y = start_pos[type]
        self.x *= TILE_SIZE
        self.y *= TILE_SIZE
        self.direction = self.start_direction[type]
        self.speed = self.start_speed[type]
        self.anim = 0
        self.speed_factor = 3/4
        self.type = type
        self.state = self.default_state[type]
        self.turned = True
        self.freeze = 0
        self.target_x = -1
        self.target_y = -1
        self.show_points = -1
        self.active = True
        self.remote = False
        self.siren_tosend = False
        self.client_eaten = False

    def update(self):
        '''Update ghosts'''
        if self.freeze > 0:
            self.freeze -= 1
            if self.freeze == 0 and self.show_points > -1:
                self.show_points = -1
                Ghost.play_siren()
        else:
            global ghost_state, player

            # Animation
            self.anim = (self.anim + self.anim_spd) % self.anim_max

            # Manage states and speed
            self.manage_states()
            self.manage_speed()

            if self.speed > 0 :
                # Move ghost
                self.x += self.speed * self.speed_factor * intcos(self.direction)
                self.y += self.speed * self.speed_factor * intsin(self.direction)
                # Tunnel warp
                self.x %= MAZE_WIDTH * TILE_SIZE

            # Get new direction from ghost AI
            if grid_snapped(self.x, self.y) and not self.turned and self.state not in ['house','leave'] \
                and not is_tunnel(self.x / TILE_SIZE, self.y / TILE_SIZE):

                new_dir = self.ai()

                # Push ghost away from wall if it got stuck
                while new_dir < 0:
                    self.x -= intcos(self.direction)
                    self.y -= intsin(self.direction)
                    new_dir = self.ai()

                if new_dir != self.direction:
                    self.x, self.y = snap_grid(self.x, self.y)

                self.direction = new_dir
                self.turned = True

            # Reset intersection status
            if self.turned and not grid_snapped(self.x, self.y):
                self.turned = False

    def ai(self):
        '''Determine new direction at an intersection'''
        snap_x, snap_y = snap_grid(self.x, self.y)
        x2, y2 = get_tile(snap_x, snap_y)

        if self.state in ['leave','eaten']:
            # Leave the ghost house
            self.target_x, self.target_y = GATE_X, GATE_Y

        elif self.state == 'scatter':
            # Go back to scatter area
            self.target_x, self.target_y = self.scatter_target[self.type]

        elif self.state == 'chase':
            # Target player
            px, py = get_player_xy(x2, y2)
            vector = [(1,0), (-1,-1), (-1,0), (0,1)]
            # The 'up' vector is diagonal due to a programming error
            # in the original game

            if self.type == 'blinky':
                # Blinky always follows Pacman
                self.target_x, self.target_y = px, py

            if self.type == 'pinky':
                # Pinky tries to catch Pacman from the front
                pdir = get_player_direction(x2,y2)
                self.target_x = px + vector[pdir][0] * 4
                self.target_y = py + vector[pdir][1] * 4

            if self.type == 'inky':
                # Inky's target tile is determined by Pacman and blinky'
                # positions.
                pdir = get_player_direction(x2,y2)
                bx, by = get_blinky_xy(x2,y2)
                px += vector[pdir][0] * 2
                py += vector[pdir][1] * 2
                # Vector from Pacman's position to Blinky's position
                dx = bx - px
                dy = by - py
                # The vector is rotated 180° to get the target tile
                self.target_x = px - dx
                self.target_y = py - dy

            if self.type == 'clyde':
                if distance(x2, y2, px, py) < 8:
                    # Return to scatter target if close to Pacman
                    self.target_x, self.target_y = self.scatter_target[self.type]
                else:
                    # Follow Pacman
                    self.target_x, self.target_y = px, py



        dist = {}
        # Available directions
        dirs = [self.direction, (self.direction-1)%4, (self.direction+1)%4]

        # Remove directions that cannot be reached
        dirs = [ d for d in dirs if dir_free(x2, y2, d) and (not dir_gate(x2, y2, d) or self.state in ['eaten','leave'])\
            and (not ghost_exception(x2, y2, d) or self.state == 'scared')]

        # Error : ghost is stuck
        if len(dirs) < 1:
            return -1

        if self.state == 'scared':
            # Pick a direction at random
            return choice(dirs)

        # Calculate distances
        for d in dirs:
            dist[d]= distance(x2 + intcos(d), y2 + intsin(d), self.target_x, self.target_y)

        mindist = 9999 # Infinite distance
        mindir = dirs[0]

        # Directions are checked in reverse priority order
        for d in [0,3,2,1]:
            # If the direction is available
            if d in dirs:
                # Check for the shortest distance
                if dist[d] <= mindist:
                    mindist = dist[d]
                    mindir = d

        return mindir

    def net_update(self,data):
        '''Update player from net data'''
        if data.name == self.type:
            self.x, self.y = data.x, data.y
            self.direction = data.dir
            self.speed = data.spd
            self.anim = data.anim
            self.state = data.state
            self.show_points = data.show_points
            Ghost.scared_clock = data.scared_clock

            if data.state not in ['eaten','scared'] and self.client_eaten == True:
                self.client_eaten = False

            if data.scared_clock == 0:
                # Reset ghost combo
                for p in player:
                    p.combo = 0
                # Stop scared sound effect
                if ch_siren.get_sound() == snd_scared:
                    Ghost.play_siren()

    def net_write(self):
        '''Return net data to be sent'''
        data = GhostData(self.x, self.y, self.speed, self.direction, self.anim,\
            self.state, self.show_points, self.siren_tosend, self.scared_clock, self.type)
        self.siren_tosend = False
        return data

    def manage_speed(self):
        '''Manage each ghost's speed'''
        x2, y2 = get_tile(self.x,self.y)
        lvl_id = min( get_level_id( game_settings['level'] ), len(GHOST_SPEEDS)-1 )
        if is_tunnel(x2,y2) and self.state != 'eaten':
            self.speed_factor = GHOST_SPEEDS[lvl_id]['tunnel']
        else:
            self.speed_factor = GHOST_SPEEDS[lvl_id][self.state]

    def manage_states(self):
        '''Used to manage ghost states'''
        if self.state in ['scatter','chase']:
            # Sync with ghost timer
            self.state = self.ghost_state

        elif self.state == 'eaten':
            # Enter house
            if distance(self.x / TILE_SIZE, self.y / TILE_SIZE, GATE_X, GATE_Y) < GRID_TOLERANCE:
                self.direction = 3
            # Restore ghost
            if distance(self.x / TILE_SIZE, self.y / TILE_SIZE, GATE_X, GATE_Y + 3) < GRID_TOLERANCE:
                self.state = 'leave'
                self.x = GATE_X * TILE_SIZE
                self.y = (GATE_Y + 3) * TILE_SIZE
                Ghost.play_siren()
                if net_settings['type'] == NET_HOST:
                    self.siren_tosend = True

        elif self.state == 'house':
            # Leave house
            limit_id = min(game_settings['level'], len(self.dot_limit)-1)
            if dot_count['eaten'] >= self.dot_limit[limit_id][self.type]:
                self.state = 'leave'
                self.direction = self.ai()
                self.turned = False
                self.speed = self.move_speed

        elif self.state == 'leave':
            # Turn to leave ghost house
            if abs(self.x / TILE_SIZE - GATE_X) < GRID_TOLERANCE:
                self.direction = 1
            # Return to normal state
            if self.y / TILE_SIZE <= GATE_Y:
                self.state = self.ghost_state
                self.direction = self.ai()
                self.x, self.y = snap_grid(self.x, self.y)

    def reverse_direction(self):
        '''Reverse direction'''
        self.direction = (self.direction + 2) % 4
        self.turned = False

    def ghost_timer():
        '''Ghost timers, called each frame'''
        global ghosts, player

        if not all(g.freeze>0 for g in ghosts) and not (game_settings['player_nb'] == 1 and player[0].dead):

            if Ghost.scared_clock > 0:
                # Scared timer
                Ghost.scared_clock -= 1
                # Revert to original state
                if Ghost.scared_clock <= 0:
                    for g in [ g for g in ghosts if g.state == 'scared']:
                        g.state = Ghost.ghost_state
                    # Reset ghost combo
                    for p in player:
                        p.combo = 0
                    Ghost.play_siren()
                    if net_settings['type'] == NET_HOST:
                        ghosts[0].siren_tosend = True
            else:
                # Scatter / chase
                if Ghost.ghost_clock > 0:
                    Ghost.ghost_clock -= 1
                else:
                    lvl_id = min(get_level_id(game_settings['level']), len(Ghost.state_durations)-1)

                    if Ghost.ghost_phase < len(Ghost.state_durations[lvl_id])-1:
                        Ghost.ghost_phase += 1
                        Ghost.ghost_state = Ghost.states[Ghost.ghost_phase]

                        if Ghost.ghost_phase > 0:
                            for g in [g for g in ghosts if not g.remote and g.state in ['scatter','chase']]:
                                g.reverse_direction()
                                g.turned = False

                        Ghost.ghost_clock = Ghost.state_durations[lvl_id][Ghost.ghost_phase]*60
                        Ghost.play_siren()

    def reset_timer():
        '''Reset timer'''
        Ghost.scared_clock = 0
        Ghost.ghost_phase = -1
        lvl_id = min(get_level_id(game_settings['level']), len(Ghost.state_durations)-1)
        Ghost.ghost_clock = 0
        Ghost.ghost_state = 'scatter'

    def scare_ghosts():
        '''Switch ghosts to frightened state'''
        global ghosts
        Ghost.scared_clock = 60 * GHOST_TIMES[ min(game_settings['level'], len(GHOST_TIMES)-1) ]
        for g in [ g for g in ghosts if g.state in ['scatter', 'chase']]:
            g.reverse_direction()
            g.speed_factor = 1/2
            g.state = 'scared'
        Ghost.play_siren()

    def eat_ghost(self):
        '''Eat ghost'''
        for o in player + [g for g in ghosts if g.state != 'eaten']:
            o.freeze = 30
        self.state = 'eaten'
        self.show_points = 0

    def draw(self):
        '''Render ghost on the screen'''
        if self.show_points < 0:
            # Location of the ghost on the sprite sheet
            if self.state == 'scared':
                row = 0
                col = 8 + floor(self.anim)
                if self.scared_clock < 2 * 60 and (self.scared_clock % 40 < 20):
                    col += 2
            elif self.state == 'eaten':
                row = 1
                col = 8 + self.direction
            else:
                row = self.color[self.type]
                col = floor(self.anim) + 2*self.direction

            x0, y0, w, h = SHEET_GHOSTS

            area = (x0 + w*col,
                    y0 + h*row,
                    w, h)

            # Coordinates on the screen
            coords = (self.x - self.xoffset, self.y - self.yoffset + MAZE_YOFFSET, w, h)
            # Blit surface
            GAME_SURF.blit(sprites, coords, area)

    def play_siren():
        '''Play ghost siren or change playing siren'''
        if SOUND:
            global ghosts

            sound = snd_siren[clamp(Ghost.ghost_phase-2, 0, SIREN_MAX)]
            if Ghost.scared_clock > 0:
                sound = snd_scared
            if any(g.state=='eaten' for g in ghosts):
                sound = snd_eaten
            ch_siren.play(sound, -1)

def respawn_ghosts():
    '''Respawn and reset ghosts'''
    ghosts.clear()
    for g in GHOST_NAMES:
        ghosts.append(Ghost(g))
    Ghost.reset_timer()
