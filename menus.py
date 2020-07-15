from globals import *
from manager import *
from netgame import *

#######################
###  MENU BUTTONS   ###
#######################

def press_enter():
    # global intro_timer, intro_timer_max, start, menu_choice

    screen = game['screen']

    if screen == SCREEN_INTRO:
        # Advance through the intro
        if menu['intro_timer'] < INTRO_TIMER_MAX:
            # Skip intro
            menu['intro_timer'] = INTRO_TIMER_MAX
        else :
            game['screen'] = SCREEN_MENU
            if SOUND:
                ch_other.play(snd_credit)

    elif screen == SCREEN_MENU:
        # Menu action
        menu_action(menu['menu_choice'])

    elif screen == SCREEN_OPTIONS:
        # Toggle option
        option_toggle(menu['menu_choice'])

    elif screen == SCREEN_SKINS:
        # Return to options menu
        game['screen'] = SCREEN_OPTIONS
        menu['menu_choice'] = 1
        if SOUND:
            ch_other.play(snd_credit)

    elif screen == SCREEN_RESULTS:
        # Result screen menu
        results_action(menu['menu_choice'])

    elif screen == SCREEN_NETMENU:
        # Online game menu
        net_menu_action(menu['menu_choice'])

    elif screen == SCREEN_GAME and not any(p.active for p in player):
        # Restart game
        restart_game()

def press_up(pl = 0):
    pl = min(game_settings['player_nb']-1, pl)
    if game['screen'] in SCREEN_MENUS:
        menu['menu_choice'] = max(0, menu['menu_choice']-1)
    elif game['screen'] == SCREEN_SKINS:
        skin = player_skin[pl]
        player_skin[pl][0] = (skin[0]-1) % SKIN_MAX[0]

def press_down(pl = 0):
    pl = min(game_settings['player_nb']-1, pl)
    if game['screen'] in SCREEN_MENUS:
        menu['menu_choice'] = min(menu_choice_max[game['screen']]-1, menu['menu_choice']+1)
    elif game['screen'] == SCREEN_SKINS:
        skin = player_skin[pl]
        player_skin[pl][0] = (skin[0]+1) % SKIN_MAX[0]

def press_left(pl = 0):
    pl = min(game_settings['player_nb']-1, pl)
    if game['screen'] == SCREEN_SKINS:
        skin = player_skin[pl]
        player_skin[pl][1] = (skin[1]-1) % SKIN_MAX[1]

def press_right(pl = 0):
    pl = min(game_settings['player_nb']-1, pl)
    if game['screen'] == SCREEN_SKINS:
        skin = player_skin[pl]
        player_skin[pl][1] = (skin[1]+1) % SKIN_MAX[1]

#######################
###      MENUS      ###
#######################

def results_action(choice):
    global loop
    if game_settings['change'] == CHANGE_ASK :
        if choice == 0 and (net_settings['type'] == NET_DISABLED or not net_settings['maze_locked']):
            # Change maze layout
            game_settings['maze'] = (game_settings['maze'] + 1) % MAZE_MAX
        elif choice == 1:
            # Next level
            restart_level()
        elif choice == 2 :
            # Quit
            game['loop'] = False
    else:
        if choice == 0:
            # Next level
            restart_level()
        elif choice == 1 :
            # Quit
            game['loop'] = False


def menu_action(choice):
    # global loop, menu_choice
    if choice == 0:
        # Start game
        if SOUND:
            ch_other.play(snd_credit)
        start_game()
    elif choice == 1:
        game['screen'] = SCREEN_NETMENU
        menu['menu_choice'] = 0
        if SOUND:
            ch_other.play(snd_credit)
    elif choice == 2:
        game['screen'] = SCREEN_OPTIONS
        menu['menu_choice'] = 0
        if SOUND:
            ch_other.play(snd_credit)
    else:
        # End game
        game['loop'] = False

def option_toggle(choice):
    # global menu_choice
    if choice == 0:
        # Number of players
        if game_settings['player_nb'] == 1:
            game_settings['player_nb'] = 2
        else:
            game_settings['player_nb'] = 1
    elif choice == 1 :
        # Character select screen
        game['screen'] = SCREEN_SKINS
        if SOUND:
            ch_other.play(snd_credit)
    elif choice == 2 :
        # Change number of lives
        if game_settings['lives'] == LIVES_INFINITE:
            game_settings['lives'] = 1
        elif game_settings['lives'] < 5:
            game_settings['lives'] += 1
        else:
            game_settings['lives'] = LIVES_INFINITE
    elif choice == 3:
        # Change maze layout
        game_settings['maze'] = (game_settings['maze'] + 1) % MAZE_MAX
    elif choice == 4:
        # Change maze change behavior
        game_settings['change'] = (game_settings['change'] + 1) % 5
    elif choice == 5:
        # Change starting level
        game_settings['starting_level'] = (game_settings['starting_level'] + 5) % 25
    elif choice == 6:
        # Return to main menu
        game['screen'] = SCREEN_MENU
        menu['menu_choice'] = menu_choice_max[SCREEN_MENU] - 2
        if SOUND:
            ch_other.play(snd_credit)

def net_menu_action(choice):
    # global menu_choice, net

    # Start netplay
    if choice in [2,3]:
        net_settings['type'] = NET_HOST if choice == 2 else NET_JOIN
        addr = (net_settings['ip'], net_settings['port']) # IP/port tuple
        game['screen'] = SCREEN_NETWAIT

        net = Host(addr) if choice == 2 else Join(addr)
        game_settings['player_nb'] = 2

        # Make 1P skin the default for client
        if choice == 3:
            player_skin[1] = player_skin[0]

        menu['menu_choice'] = 0
        if SOUND:
            ch_other.play(snd_credit)
    # Return to main menu
    elif choice == 4:
        game['screen'] = SCREEN_MENU
        menu['menu_choice'] = 1
        if SOUND:
            ch_other.play(snd_credit)

def net_menu_input(choice, key):
    if choice == 0:
        # Change IP
        if key in number_keys:
            for i in range(len(number_keys)):
                if key == number_keys[i]:
                    net_settings['ip'] += str(i)
                    net_settings['ip'] = net_settings['ip'][:IP_MAXLENGTH]
                    break
        elif key == K_PERIOD:
            net_settings['ip'] += '.'
            net_settings['ip'] = net_settings['ip'][:IP_MAXLENGTH]
        elif key == K_BACKSPACE:
            net_settings['ip'] = net_settings['ip'][:len(net_settings['ip'])-1]
    elif choice == 1:
        # Change port
        if key in number_keys:
            for i in range(len(number_keys)):
                if key == number_keys[i]:
                    net_settings['port'] *= 10
                    net_settings['port'] += i
                    net_settings['port'] = min(PORT_MAX, net_settings['port'])
                    break
        elif key == K_BACKSPACE:
            net_settings['port'] = min(PORT_MAX, floor(net_settings['port']/10))
