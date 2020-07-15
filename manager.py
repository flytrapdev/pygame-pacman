from globals import *
from map import load_layout
from pacman import *
from ghosts import *

#######################
### GAME MANGEMENT  ###
#######################

def end_level():
    #global end_timer, menu_choice

    game['start'] = False
    menu['end_timer'] = 0
    menu['menu_choice'] = 0
    change = game_settings['change']

    # Remove fruit
    fruits.clear()
    # Reset ghost timer
    Ghost.reset_timer()
    # Increase level number
    game_settings['level'] += 1
    # Advance maze
    if change in [CHANGE_ALWAYS, CHANGE_HALF, CHANGE_THIRD]:
        # Increase counter
        game_settings['maze_count'] += 1
        # Next maze
        if (change, game_settings['maze_count']) in [(CHANGE_ALWAYS, 1), (CHANGE_HALF, 2), (CHANGE_THIRD, 3)]:
            game_settings['maze'] += 1
            game_settings['maze'] %= MAZE_MAX
            game_settings['maze_count'] = 0

    # Reset online settings
    if net_settings['type'] != NET_DISABLED:
        for p in player:
            p.ready = False
        net_settings['maze_sent'] = False
        net_settings['maze_locked'] = False

    if game_settings['player_nb'] > 1 or game_settings['change'] == CHANGE_ASK:
        game['screen'] = SCREEN_RESULTS
    else:
        restart_level()

def restart_level():
    '''Restart the current level'''

    for i in range(game_settings['player_nb']):
        p = player[i]

        if game_settings['player_nb'] > 1:
            p.prev_score += p.score
            p.score = 0

        p.direction = 0
        p.dots = 0
        p.x = start_pos['pacman'][0] - (game_settings['player_nb']-1) + 2*i
        p.y = start_pos['pacman'][1]
        p.x *= TILE_SIZE
        p.y *= TILE_SIZE

        if net_settings['type'] != NET_DISABLED:
            p.ready = False

    for g in ghosts :
        g.x, g.y = start_pos[g.type]
        g.x *= TILE_SIZE
        g.y *= TILE_SIZE
        g.state = g.default_state[g.type]
        g.direction = g.start_direction[g.type]
        g.speed = g.start_speed[g.type]

    Ghost.reset_timer()

    layout.clear()
    load_layout(game_settings['maze'])
    game['screen'] = SCREEN_GAME

    game['complete'] = False
    game['start'] = False
    menu['start_timer'] = 0
    menu['end_timer'] = 0

    # Set player to ready
    if net_settings['type'] != NET_DISABLED:
        for pl in [p for p in player if not p.remote]:
            pl.ready = True


def start_game():
    '''Start the game'''

    # Verify no game is in progress
    if len(player) < 1:

        game_settings['level'] = game_settings['starting_level']
        load_layout(game_settings['maze'])

        for i in range( min(PLAYERNB_MAX, game_settings['player_nb']) ):
            newx = start_pos['pacman'][0]-(game_settings['player_nb']-1) + 2*i
            newpl = Pacman(skin=player_skin[i], x=newx, pl_id=i)
            player.append(newpl)

        respawn_ghosts()

        game['screen'] = SCREEN_GAME

        # Configure netgame settings
        if net_settings['type'] != NET_DISABLED:
            if net_settings['type'] == NET_HOST:
                # Host
                player[1].remote = True
            elif net_settings['type'] == NET_JOIN:
                # Join / client
                player[0].remote = True
                for g in ghosts:
                    g.remote = True

def restart_game():
    '''Restart the game'''

    game['screen'] = SCREEN_MENU
    menu['menu_choice'] = 0

    game['complete'] = False
    game['start'] = False
    menu['start_timer'] = 0
    menu['end_timer'] = 0

    game_settings['level'] = 0

    player.clear()
    ghosts.clear()
    fruits.clear()

    if net_settings['type'] != NET_DISABLED and net:
        net.close()

    if SOUND:
        ch_siren.stop()
        ch_other.stop()
        for c in ch_munch:
            c.stop()
