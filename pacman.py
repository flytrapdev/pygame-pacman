from globals import *
from map import *
from ghosts import *
from netgame import PlayerData
from copy import deepcopy

#######################
###     PACMAN      ###
#######################

class Pacman:

    move_speed = 4/3
    anim_spd = 1/2
    anim_max = 4
    dead_anim_spd = 1/4
    dead_anim_max = 12
    xoffset = TILE_SIZE
    yoffset = TILE_SIZE

    def __init__(self, skin=(0,0), x=14, y=23.5, pl_id=0, remote=False):

        self.x = x * TILE_SIZE
        self.y = y * TILE_SIZE
        self.direction = 0
        self.speed = 0
        self.anim = 3
        self.speed_factor = PACMAN_SPEEDS[0]['normal']
        self.freeze = 0
        self.dots = 0
        self.dead = False
        self.to_respawn = False
        self.active = True
        self.shield = 0
        self.skin = skin
        self.score = 0
        self.prev_score = 0
        self.combo = 0
        self.show_points = -1
        self.lives = game_settings['lives']
        self.pl_id = pl_id
        self.remote = remote
        self.ready = True       # Netgame player status
        self.dots_tosend = []   # Netgame eaten dots
        self.ghosts_tosend = [] # Netgame eaten ghosts

    def update(self):
        '''Update Pacman'''
        x2, y2 = get_tile(self.x, self.y)

        # Collision with ghosts
        # (is checked even if pacman is frozen)
        g = ghost_collide(x2,y2)
        if g:
            if g.state == 'scared' and not g.client_eaten:
                # Eat ghost
                g.eat_ghost()
                self.score += POINTS_GHOST[self.combo]
                self.show_points = self.combo
                self.combo = min(3, self.combo+1)
                if SOUND:
                    ch_other.play(snd_eat_ghost)
                # Workaround to allow client to send eaten ghost data to host
                # and prevent ghost from being eaten multiple times
                if net_settings['type'] == NET_JOIN:
                    self.ghosts_tosend.append(g.type)
                    g.client_eaten = True

            elif g.state in ['leave','scatter','chase'] and not self.dead and self.shield < 1:
                # Die
                self.die()

        # Dot freeze
        if self.freeze > 0 :
            self.freeze -= 1
            if self.freeze <= 0:
                self.show_points = -1
        else:
            # Other actions
            if self.dead :
                # Respawn
                if self.to_respawn:
                    self.respawn()
                # Death animation and sound
                if self.anim < 0:
                    if SOUND:
                        ch_other.play(snd_death[0])
                    self.anim = 0

                self.anim += self.dead_anim_spd
                if self.anim >= self.dead_anim_max - 1:
                    self.freeze = 60
                    self.to_respawn = True
                    if SOUND:
                        ch_other.play(snd_death[1])

            else:
                # Manage speed
                self.manage_speed()
                # Shield
                self.shield = max(0, self.shield-1)

                # Movement
                if self.speed > 0 :
                    # Move pacman
                    self.x += self.speed * self.speed_factor * intcos(self.direction)
                    self.y += self.speed * self.speed_factor * intsin(self.direction)

                    self.x %= MAZE_WIDTH * TILE_SIZE

                    # Animation
                    self.anim = (self.anim + self.anim_spd) % self.anim_max

                    # Collision with walls
                    if not (dir_free(self.x/TILE_SIZE, self.y/TILE_SIZE, self.direction, -1/2)):
                        self.speed = 0
                        self.x, self.y = snap_grid(self.x, self.y)

                    # Eat dots
                    if is_dot(x2,y2) or is_pow(x2,y2):
                        # Pellet effects
                        if is_dot(x2,y2):
                            self.freeze = max(self.freeze, 1)
                            self.score += POINTS_DOT
                        else:
                            self.freeze = max(self.freeze, 3)
                            self.score += POINTS_POW
                            Ghost.scare_ghosts()
                        # Remove dot from map
                        write_map(x2, y2, COLL_VOID)
                        # Dot counters
                        self.dots += 1
                        dot_count['eaten'] += 1
                        # Spawn fruit
                        if dot_count['eaten'] in FRUIT_DOTS:
                            spawn_fruit()
                        # Sound
                        if SOUND:
                            ch_munch[self.pl_id].play(snd_munch[dot_count['sound']])
                        # Alternate between both munch sounds
                        dot_count['sound'] = 1 - dot_count['sound']
                        # Add dot to dot list
                        if net_settings['type'] != NET_DISABLED:
                            self.dots_tosend.append((x2,y2))

                    # Eat fruit
                    f = fruit_collide(x2,y2)
                    if f and f.active and not f.draw_score:
                        f.eat_fruit(self)
                        if SOUND:
                            ch_other.play(snd_eat_fruit)

    def net_update(self, data):
        '''Update player from net data'''
        x2, y2 = get_tile(self.x, self.y)

        self.x, self.y = data.x, data.y
        self.direction = data.dir
        self.speed = data.spd
        self.skin = data.skin
        self.dead = data.dead
        self.anim = data.anim
        self.score = data.score
        self.lives = data.lives
        self.show_points = data.show_points
        self.ready = data.ready

        # Remove dots
        for d in data.dots:
            if is_pow(d[0], d[1]):
                Ghost.scare_ghosts()
            if is_pow(d[0], d[1]) or is_dot(d[0], d[1]):
                write_map(d[0], d[1], COLL_VOID)
                dot_count['eaten'] += 1
                # Spawn fruit
                if dot_count['eaten'] in FRUIT_DOTS:
                    spawn_fruit()

        # Eat ghosts
        for name in data.ghosts:
            for g in ghosts:
                # Compare ghost name with received data
                if g.type == name and g.state != 'eaten':
                    g.eat_ghost()

        # Eat fruit
        f = fruit_collide(x2,y2)
        if f and f.active and not f.draw_score:
            f.eat_fruit(self)
            if SOUND:
                ch_other.play(snd_eat_fruit)

        if self.lives == 0:
            # Game over
            self.active = False

    def net_read_ack(self, m):
        '''Read acknowledged data and remove it from the lists'''

        # Dots
        if m.header == 'dots':
            for t in m.content:
                # Look for dot tuple in list
                tup = (t[0],t[1])
                if tup in self.dots_tosend:
                    self.dots_tosend.remove(tup)

        # Ghosts
        elif m.header == 'ghosts':
            for g in m.content:
                if g in self.ghosts_tosend:
                    self.ghosts_tosend.remove(g)

    def net_write(self):
        '''Return net data to be sent'''
        data = PlayerData(self.x, self.y, self.speed, self.direction, self.anim,\
            self.skin, self.dead, self.score, self.lives, deepcopy(self.dots_tosend), deepcopy(self.ghosts_tosend),\
            self.show_points, self.ready)

        return data

    def steer(self, direction):
        '''Change direction'''
        if not self.dead and self.freeze < 1:
            corner_x, corner_y = self.x + TILE_SIZE*CORNERING*intcos(self.direction), self.y + TILE_SIZE*CORNERING*intsin(self.direction)
            x2, y2 = get_tile(self.x, self.y)

            if dir_free(x2, y2, direction) and not dir_gate(x2, y2, direction) and \
                ( grid_snapped(corner_x, corner_y) or direction == (self.direction+2)%4 or self.speed == 0 ):

                # Snap Pacman to the grid if he changes direction
                snap = False
                if direction == (self.direction+1)%4 or direction == (self.direction-1)%4:
                    snap = True

                self.direction = direction
                self.speed = self.move_speed

                if snap:
                    self.x, self.y = snap_grid(self.x, self.y)

    def manage_speed(self):
        lvl_id = get_level_id(game_settings['level'])
        if Ghost.scared_clock > 0:
            self.speed_factor = PACMAN_SPEEDS[lvl_id]['scared']
        else:
            self.speed_factor = PACMAN_SPEEDS[lvl_id]['normal']

    def die(self):
        if game_settings['player_nb'] < 2:
            # Respawn ghosts in single player mode
            ghosts.clear()
            self.freeze = 60
            if SOUND:
                ch_siren.stop()

        self.dead = True
        self.anim = -1

    def action(self):
        # Revive player
        if len(player)>1 and not self.active and sum(p.lives for p in player)>1:
            for p in [pl for pl in player if pl.lives>1]:
                p.lives -= 1
            # respawn() takes away 1 life
            self.lives += 2
            self.active = True
            self.respawn()

    def respawn(self):
        self.lives = max(-1, self.lives - 1)

        if self.lives == 0:
            # Game over
            self.active = False
        else:
            # Respawn
            self.x, self.y = start_pos['pacman']
            self.x *= TILE_SIZE
            self.y *= TILE_SIZE
            self.dead = False
            self.to_respawn = False
            self.anim = 0

            if game_settings['player_nb'] > 1:
                self.shield = 120

            if len(ghosts) < 1:
                respawn_ghosts()
                self.freeze = 90
                for g in ghosts :
                    g.freeze = 90

    def draw(self, x = -1, y = -1, dest = GAME_SURF):
        '''Render Pacman on the screen'''
        if x < 0 and y < 0:
            x, y = self.x, self.y
            maze_offset = MAZE_YOFFSET
        else:
            maze_offset = 0

        if self.show_points >= 0:
            # Show points for eating ghost
            col = self.show_points
            x0, y0, w, h = SHEET_POINTS
            area = (x0 + w * col,
                    y0,
                    w, h)
            surf = sprites
        else:
            # Location of pacman on the sprite sheet
            if self.dead:
                img = max(0,self.anim) + 16
            else:
                img = floor(self.anim)%4 + self.direction*4

            col = floor(img)%4 + 4 * self.skin[0]
            row = floor(img/4) + 7 * self.skin[1]

            x0, y0, w, h = SHEET_PACMAN
            area = (x0 + w*col,
                    y0 + h*row,
                    w, h)
            surf = characters

        # Draw sprite on screen
        if not (self.shield%2 > 0): # Pacman flashes if invincible
            coords = (x - self.xoffset, y - self.yoffset + maze_offset, w, h)
            dest.blit(surf, coords, area)

#######################
###      FRUIT      ###
#######################

class Fruit:

    xoffset = TILE_SIZE
    yoffset = TILE_SIZE
    duration = 10
    score_duration = 1

    def __init__(self):
        self.x, self.y = FRUIT_POS
        self.x *= TILE_SIZE
        self.y *= TILE_SIZE
        self.timer = 0
        self.draw_score = False
        self.active = True
        self.remote = False

    def update(self):
        self.timer += 1
        if (not self.draw_score and self.timer >= self.duration*60)\
        or (self.draw_score and self.timer >= self.score_duration*60):
            self.active = False

    def eat_fruit(self, pl):
        self.timer = 0
        self.draw_score = True
        pl.score += FRUIT_SCORE[ get_fruit_type(game_settings['level']) ]

    def draw(self):
        coords = (self.x - self.xoffset, self.y - self.yoffset + MAZE_YOFFSET)
        type = get_fruit_type(game_settings['level'])

        if self.draw_score:
            x0, y0, w, h = SHEET_POINTS2
            if type < 4:
                area = (x0 + type*w, y0,\
                    w, h)
            else:
                # >=1000
                area = (x0 + 4*w, y0 + (type-4)*h,\
                    2*w, h)
        else:
            x0, y0, w, h = SHEET_FRUIT
            area = (x0 + w*type, y0,\
                w, h)
        GAME_SURF.blit(sprites, coords, area)

def spawn_fruit():
    fruits.append(Fruit())

def fruit_collide(x,y):
    for f in fruits:
        fx, fy = get_tile(f.x, f.y)
        if x == fx and y == fy:
            return f
    return None
