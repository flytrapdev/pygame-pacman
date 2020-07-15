from pygame import *
from math import floor,sqrt
from sys import argv

#######################
###  COMMAND LINE   ###
#######################
SOUND = True
SCREEN_SCALE = 3

for i in range(len(argv)):
    if argv[i] == '-s':
        SOUND = False

    if argv[i] == '-z' and len(argv)>i+1 and argv[i+1].isdigit():
        SCREEN_SCALE = int(argv[i+1])

#######################
###   INIT MIXER    ###
#######################
if SOUND:
    mixer.init(buffer = 64)

#######################
###    CONSTANTS    ###
#######################

# Sprite sheet coordinates
SHEET_MAZE = (0, 0, 224, 248)
SHEET_PACMAN = (0, 0, 16, 16)
SHEET_GHOSTS = (0, 16, 16, 16)
SHEET_SCARED = (128, 16, 16, 16)
SHEET_FRUIT = (16, 0, 16, 16)
SHEET_DOT = (0, 0, 8, 8)
SHEET_POW = (8, 0, 8, 8)
SHEET_POINTS = (0, 80, 16, 16)
SHEET_LIVES = (0, 112, 16, 16)
SHEET_POINTS2 = (0, 96, 16, 16)
TILE_SIZE = 8

# Number of palettes / characters
SKIN_MAX = (4,4)
PACMAN_IMAGES = 24

# Screen size
SCREEN_W, SCREEN_H = 224,288
SCREEN_HW, SCREEN_HH = SCREEN_W/2, SCREEN_H/2

# Screen indices
SCREEN_INTRO, SCREEN_MENU, SCREEN_OPTIONS, SCREEN_SKINS, SCREEN_MODES,\
SCREEN_GAME, SCREEN_RESULTS, SCREEN_NETMENU, SCREEN_NETWAIT = 0, 1, 2, 3, 4, 5, 6, 7, 8

SCREEN_MENUS = [SCREEN_MENU, SCREEN_OPTIONS, SCREEN_MODES, SCREEN_RESULTS, SCREEN_NETMENU]

# Game settings constants
CHANGE_NEVER, CHANGE_ALWAYS, CHANGE_ASK, CHANGE_HALF, CHANGE_THIRD = 0, 1, 2, 3, 4
NET_DISABLED, NET_HOST, NET_JOIN = 0, 1, 2
LIVES_INFINITE = -1
MAZE_MAX = 7
BUFSIZE = 4096

PORT_MAX = 65535 # Port is a 16-bit value
IP_MAXLENGTH = 15 # IP can take up to 15 chars
PLAYERNB_MAX = 2

MAZE_NAMES = ['CLASSIC', 'MSPAC 1', 'MSPAC 2', 'MSPAC 3', 'MSPAC 4', 'NEW 1', 'NEW 2']

# Colors
C_WHITE = (222, 222, 255)
C_GRAY = (104, 104, 81)
C_RED = (255, 0, 0)
C_BLINKY = C_RED
C_PINKY = (255, 183, 255)
C_INKY = (0, 255, 255)
C_CLYDE = (255, 183, 81)
C_YELLOW = (255, 255, 0)

# Collision constants and layout file format
COLL_VOID, COLL_WALL, COLL_DOT, COLL_POW, COLL_GATE, COLL_TUNNEL = 0, 1, 2, 3, 4, 5
FILE_FORMAT = {' ':COLL_VOID, '#':COLL_WALL, '.':COLL_DOT, '0':COLL_POW, '$':COLL_GATE, 'T':COLL_TUNNEL}

# Number of keys per player
KEY_NB = 5

# Ghost names
GHOST_NAMES = ['blinky','inky','pinky','clyde']

# Speed factors
GHOST_SPEEDS = [ {'scatter':0.75, 'chase':0.75, 'scared':0.5, 'tunnel':0.4, 'leave':0.4, 'eaten':1.5, 'house':0},\
    {'scatter':0.85, 'chase':0.85, 'scared':0.55, 'tunnel':0.45, 'leave':0.45, 'eaten':1.5, 'house':0},\
    {'scatter':0.95, 'chase':0.95, 'scared':0.6, 'tunnel':0.5, 'leave':0.5, 'eaten':1.5, 'house':0}]
PACMAN_SPEEDS = [ {'normal':0.8, 'scared':0.9}, {'normal':0.9, 'scared':0.95},\
    {'normal':1, 'scared':1}, {'normal':0.9, 'scared':1} ]

# Scared durations
GHOST_TIMES = [6, 5, 4, 3, 2, 5, 2, 2, 1, 5, 2, 1, 1, 3, 1]

# House entrance position
GATE_X, GATE_Y = 14, 11.5

# Points
POINTS_DOT = 10
POINTS_POW = 50
POINTS_GHOST = [200, 400, 800, 1600]

# Fruit info
FRUIT_DOTS = [70, 170]
FRUIT_SCORE = [100, 300, 500, 700, 1000, 2000, 3000, 5000]
FRUIT_TYPE = [0, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 7]

MAZE_YOFFSET = 24
MAZE_WIDTH = 28
MAZE_HEIGHT = 31
READY_POS = (112, 140 + MAZE_YOFFSET)
FRUIT_POS = (14, 17.5)

GRID_TOLERANCE = 1/8
CORNERING = 1/4

# Misc settings
DISPLAY_TARGETS = False
SIREN_VOLUME = 0.5

# Menu info
INTRO_TIMER_MAX = 1200
END_TIMER_MAX = 180
START_TIMER_MAX = 120

# Number keys
number_keys = [K_0, K_1, K_2, K_3, K_4, K_5, K_6, K_7, K_8, K_9]
input_keys = number_keys + [K_PERIOD, K_BACKSPACE]

#######################
###     GLOBALS     ###
#######################
DISPLAY_SURF = display.set_mode((SCREEN_W*SCREEN_SCALE, SCREEN_H*SCREEN_SCALE),
                                DOUBLEBUF, 32)
GAME_SURF = Surface( (SCREEN_W, SCREEN_H) )
SCALE_SURF = Surface( (SCREEN_W*SCREEN_SCALE, SCREEN_H*SCREEN_SCALE) )
clock = time.Clock()

game = {'loop':True, 'start':False, 'complete':False, 'screen':SCREEN_INTRO}

menu = {'menu_choice':0, 'intro_timer':0, 'start_timer':0, 'end_timer':0}

menu_choice_max = {SCREEN_MENU:4, SCREEN_OPTIONS:7, SCREEN_RESULTS:3,
    SCREEN_NETMENU:5}

game_settings = {'type':'settings', 'player_nb':1, 'maze':0,\
    'maze_count':0, 'starting_level':0, 'level':0, 'change':0, 'lives':3}
net_settings = {'ip':'127.0.0.1', 'port':5555, 'type':NET_DISABLED,\
    'timeout':0, 'timeout_max':240,\
    'maze_locked':False, 'maze_sent':False}

net = None

player_skin = {0: [0,0], 1: [0,1]}
dot_count = {'total':0, 'eaten':0, 'sound':0}

# Starting positions
start_pos = {}

#######################
###    RESOURCES    ###
#######################

# Graphics
sprites = image.load('gfx/sprites.png')
sprites.set_colorkey((0,0,0))

mazes = image.load('gfx/mazes.png')
mazes.set_colorkey((0,0,0))

characters = image.load('gfx/characters.png')
characters.set_colorkey((0,0,0))

logo = image.load('gfx/title.png')
logo.set_colorkey((0,0,255))

# Sounds
if SOUND:
    snd_munch = [mixer.Sound('sfx/munch_1.wav'), mixer.Sound('sfx/munch_2.wav')]
    snd_siren = [mixer.Sound('sfx/siren_1.wav'), mixer.Sound('sfx/siren_2.wav'),\
        mixer.Sound('sfx/siren_3.wav'), mixer.Sound('sfx/siren_4.wav'),\
        mixer.Sound('sfx/siren_5.wav')]
    snd_scared = mixer.Sound('sfx/power_pellet.wav')
    snd_eaten = mixer.Sound('sfx/retreating.wav')
    snd_eat_ghost = mixer.Sound('sfx/eat_ghost.wav')
    snd_eat_fruit = mixer.Sound('sfx/eat_fruit.wav')
    snd_credit = mixer.Sound('sfx/credit.wav')
    snd_death = [mixer.Sound('sfx/death_1.wav'), mixer.Sound('sfx/death_2.wav')]

    # Set siren volume
    for s in snd_siren:
        s.set_volume(SIREN_VOLUME)
    snd_scared.set_volume(SIREN_VOLUME)
    snd_eaten.set_volume(SIREN_VOLUME)

    # Reserved channels
    ch_munch = [mixer.Channel(0), mixer.Channel(1)]
    ch_siren = mixer.Channel(2)
    ch_other = mixer.Channel(3)
    SIREN_MAX = 4

#######################
###      MATH       ###
#######################

def intsin(direction):
    val = [0, -1, 0, 1]
    return val[direction]

def intcos(direction):
    val = [1, 0, -1, 0]
    return val[direction]

def clamp(x, xmin, xmax):
    return min(max(x, xmin), xmax)

#######################
###   MAP LAYOUT    ###
#######################

layout = []

#######################
###  OBJECT LISTS   ###
#######################

player = []
ghosts = []
fruits = []

#######################
###  MAP FUNCTIONS  ###
#######################

def get_tile(x, y):
    return floor(x / TILE_SIZE), floor(y / TILE_SIZE)

def distance(x1, y1, x2, y2):
    return sqrt((x1 - x2)**2 + (y1 - y2)**2)

# Access player attributes
def get_nearest_player(x,y):
    if len(player) == 1:
        return player[0]
    # Player 1
    px, py = get_tile(player[0].x,player[0].y)
    mindist = distance(x, y, px, py)
    minp = player[0]
    # Other players
    for p in player[1:]:
        px, py = get_tile(p.x, p.y)
        dist = distance(x, y, px, py)
        if(dist < mindist):
            mindist = dist
            minp = p

    return minp

def get_player_xy(x,y):
    pl = get_nearest_player(x,y)
    return get_tile(pl.x, pl.y)

def get_player_dots():
    return sum(p.dots for p in player)

def reset_player_dots():
    for p in player:
        p.dots = 0

def get_player_direction(x,y):
    return get_nearest_player(x,y).direction

def count_dots(map):
    DOTS_TOTAL = len([c for row in map for c in row if c in [COLL_DOT,COLL_POW]])

def get_blinky_xy(default_x = 0, default_y = 0):
    blinkys = [g for g in ghosts if g.type == 'blinky']
    if len(blinkys) > 0:
        return get_tile(blinkys[0].x, blinkys[0].y)
    return default_x, default_y

def get_level_id(n):
    '''Returns the level id for the speed and timer tables'''
    if n < 1:
        return 0
    elif n < 4:
        return 1
    elif n < 20:
        return 2
    return 3
