# Pac-Man pygame re-creation
#
# Initial commit by Matthieu Le Gallic aka FlytrapDev
# Font PressStart2P by CodeMan38
#
# Licensed under GNU GPLv3

from pygame import *
from sys import exit

from globals import *
from map import *
from drawing import *
from netgame import *
from menus import *
from math import floor

#######################
###    JOYSTICK     ###
#######################
joystick.init()
joysticks = [joystick.Joystick(x) for x in range(joystick.get_count())]
for j in joysticks:
    j.init()

#######################
###      KEYS       ###
#######################

# Keys
key_held = [[False for j in range(KEY_NB)] for i in range(2)]
player_keys = [[K_d, K_w, K_a, K_s, K_f], [K_RIGHT, K_UP, K_LEFT, K_DOWN, K_RCTRL]]

menu_input = False

#######################
### MAIN GAME LOOP  ###
#######################

# Game loop
while game['loop']:

    #######################
    ###      EVENTS     ###
    #######################
    # Events
    for ev in event.get():

        if ev.type == QUIT:
            game['loop'] = False

        if ev.type == KEYUP:
            # Player keys
            for i in range(PLAYERNB_MAX):
                for k in range(5):
                    if ev.key == player_keys[i][k]:
                        key_held[i][k] = False

        if ev.type == KEYDOWN:
            # Player keys
            for i in range(PLAYERNB_MAX):
                for k in range(5):
                    if ev.key == player_keys[i][k]:
                        key_held[i][k] = True
                if ev.key == player_keys[i][4]:
                    player[i].action()
                # Menu keys
                if game['screen'] in SCREEN_MENUS + [SCREEN_SKINS]:
                    if ev.key == player_keys[i][0]:
                        press_right(i)
                    if ev.key == player_keys[i][1]:
                        press_up(i)
                    if ev.key == player_keys[i][2]:
                        press_left(i)
                    if ev.key == player_keys[i][3]:
                        press_down(i)

            # Number keys for ip and port
            if ev.key in input_keys and game['screen'] == SCREEN_NETMENU:
                net_menu_input(menu['menu_choice'], ev.key)

            if ev.key == K_RETURN:
                press_enter()

            if ev.key == K_ESCAPE:
                game['loop'] = False

            if ev.key == K_SPACE:
                end_level()

        # Joystick button
        if ev.type == JOYBUTTONDOWN:
            for i in range(joystick.get_count()):
                id = 1-i
                if joysticks[i].get_button(0) and game['screen']==SCREEN_GAME:
                    player[id].action()

    # Joysticks
    for i in range(joystick.get_count()):
        j = joysticks[i]
        hat_x, hat_y = j.get_hat(0)

        id = 1-i

        if hat_x == -1:
            key_held[id][2] = True
        if hat_x == 1:
            key_held[id][0] = True
        if hat_x == 0:
            key_held[id][0] = key_held[id][2] = False
        if hat_y == -1:
            key_held[id][3] = True
        if hat_y == 1:
            key_held[id][1] = True
        if hat_y == 0:
            key_held[id][1] = key_held[id][3] = False

    #######################
    ###      MENUS      ###
    #######################
    if game['screen'] == SCREEN_INTRO:
        # Update screen timer
        menu['intro_timer'] = min(INTRO_TIMER_MAX, menu['intro_timer'] + 1)
        draw_intro(menu['intro_timer'])

    elif game['screen'] == SCREEN_MENU:
        # Draw main menu
        draw_title(menu['menu_choice'])
        menu_input = True

    elif game['screen'] == SCREEN_OPTIONS:
        # Draw options menu
        draw_options(menu['menu_choice'])
        menu_input = True

    elif game['screen'] == SCREEN_SKINS:
        # Draw character select screen
        draw_skin_menu()
        menu_input = True

    elif game['screen'] == SCREEN_RESULTS:
        # Level end
        # Only 2 menu options
        if game_settings['change'] == CHANGE_ASK:
            menu_choice_max[SCREEN_RESULTS] = 3
        else:
            menu_choice_max[SCREEN_RESULTS] = 2

        draw_results(menu['menu_choice'], game_settings['maze'])

        # Game started by remote player
        if net_settings['type'] != NET_DISABLED:
            received = net.net_read()
            for r in received:
                if isinstance(r,MazeChangeData):
                    game_settings['maze'] = r.maze
                    game_settings['maze_count'] = r.maze_count
                    net_settings['maze_locked'] = True
                    # Send data for verification
                    net.net_send(MazeChangeData(r.maze,r.maze_count))

    elif game['screen'] == SCREEN_NETMENU:
        # Online menu
        draw_net_menu(menu['menu_choice'])

    elif game['screen'] == SCREEN_NETWAIT:
        # Connection between host and client

        # Host
        if net_settings['type'] == NET_HOST:
            # Create socket
            if not net:
                net = Host((net_settings['ip'], net_settings['port']))

            # Read received data
            received = net.net_read()
            for r in received:
                # Send game settings to remote player
                if isinstance(r, ConnectionData):
                    net.net_send(SettingsData())
                    net.net_send(SkinData(player_skin[0]))

                elif isinstance(r, SkinData):
                    player_skin[1] = r.skin

                elif isinstance(r, SettingsData):
                    # Check if received data is correct
                    new_settings = r.data
                    correct = True
                    for k in r.data.keys():
                        if game_settings[k] != new_settings[k]:
                            correct = False

                    if correct:
                        # Send acknowledge
                        net.net_send(AcknowledgeData())
                        # Start game
                        start_game()

        # Join
        if net_settings['type'] == NET_JOIN:
            # Create socket
            if not net:
                net = Join((net_settings['ip'], net_settings['port']))

            try:
                # Connect to host
                net.net_send(ConnectionData())

                # Read received data
                received = net.net_read()
                for r in received:
                    # Receive game settings
                    if isinstance(r, SettingsData):
                        new_settings = r.data
                        for k in new_settings.keys():
                            game_settings[k] = new_settings[k]

                        # Send received data for verification
                        net.net_send(SettingsData())

                    elif isinstance(r, SkinData):
                        player_skin[0] = r.skin

                    elif isinstance(r, AcknowledgeData):
                        # Start game
                        start_game()
            except ConnectionResetError:
                pass

        draw_net_wait(net)

    #######################
    ###      GAME       ###
    #######################
    elif game['screen'] == SCREEN_GAME:
        # Update game

        # Update all objects
        if game['start'] and not game['complete']:

            # Pacman input
            input_id = 1
            for p in [p for p in player[::-1] if not p.remote]:
                for d in range(4):
                    if key_held[input_id][d] and not key_held[input_id][(d+2)%4]:
                        p.steer(d)
                input_id -= 1

            # Update game
            Ghost.ghost_timer()
            for o in [p for p in player + fruits + ghosts if p.active and not p.remote]:
                o.update()

        # Draw game
        draw_maze()
        for o in [p for p in player + ghosts + fruits if p.active]:
            o.draw()
        draw_hud()
        if DISPLAY_TARGETS:
            draw_targets()

        # Before the level starts
        if not game['start']:

            # Draw 'ready' and 'game over' texts
            if all(p.ready for p in player):
                draw_text_centered("READY!", READY_POS, C_YELLOW)
                menu['start_timer'] += 1
                if menu['start_timer'] >= START_TIMER_MAX:
                    game['start'] = True
            else:
                draw_text_centered("WAITING", READY_POS, C_YELLOW)



        if not any(p.active for p in player):
            draw_text_centered("GAME OVER", READY_POS, C_RED)
            draw_prompt()
        else:
            # Dead player text
            for i in range(game_settings['player_nb']):
                if not player[i].active:
                    draw_prompt(['GAME OVER','PRESS START'], SCREEN_HW * (1/2 + i))

        # Complete level
        if not game['complete'] and dot_count['eaten'] >= dot_count['total']:
            game['complete'] = True
            if SOUND:
                ch_siren.stop()

        # Flashing maze timer
        if game['complete']:
            menu['end_timer'] += 1
            if menu['end_timer'] >= END_TIMER_MAX:
                # End level
                end_level()

        # Remove eaten fruit
        for f in [f for f in fruits if not f.active]:
            fruits.remove(f)

        #######################
        ###     NETGAME     ###
        #######################
        if net_settings['type'] != NET_DISABLED:

            try:
                to_send = []             # Data to be sent
                to_read = net.net_read() # Received data

                # Connection recovered, reset timer
                if to_read:
                    net_settings['timeout'] = 0

                # Send chosen maze to other player
                if not game['start'] and not game['complete'] and game_settings['change']==CHANGE_ASK\
                and net_settings['type']!=NET_DISABLED and not all(p.ready for p in player):
                    if not net_settings['maze_sent']:
                        to_send.append(MazeChangeData(game_settings['maze'], game_settings['maze_count']))

                # Read received data
                for m in to_read:
                    if isinstance(m, MazeChangeData):
                        # Check maze change data
                        if m.maze == game_settings['maze'] and m.maze_count == game_settings['maze_count']:
                            net_settings['maze_sent'] = True

                    elif isinstance(m, PlayerData):
                        # Update player
                        for p in [p for p in player if p.remote]:
                            p.net_update(m)

                        # Send acknowledge
                        if len(m.dots)>0:
                            to_send.append(DataAcknowledgeData(header='dots', content=m.dots))
                        if len(m.ghosts)>0:
                            to_send.append(DataAcknowledgeData(header='ghosts', content=m.ghosts))

                    elif isinstance(m, GhostData):
                        # Update ghosts
                        for g in [g for g in ghosts if g.remote]:
                            g.net_update(m)
                        if m.siren:
                            Ghost.play_siren()

                    elif isinstance(m, DataAcknowledgeData):
                        # Read acknowledged data
                        for p in [p for p in player if not p.remote]:
                            p.net_read_ack(m)


                # Send player and ghosts data
                for p in [p for p in player + ghosts if not p.remote]:
                    to_send.append(p.net_write())

                # Send
                for data in to_send:
                    net.net_send(data)

            # Connection lost
            except ConnectionResetError:

                # Increase timer
                net_settings['timeout'] += 1
                if net_settings['timeout'] >= net_settings['timeout_max']:
                    net.close()
                    net = None
                    restart_game()

            # Connection lost message
            if net_settings['timeout'] > 60:
                draw_text_centered('CONNECTION LOST', (SCREEN_HW, SCREEN_H-7))


    # Timing
    clock.tick(60)

    # Blit screen
    DISPLAY_SURF.blit(transform.scale(GAME_SURF, DISPLAY_SURF.get_size()), (0,0))
    display.update()


# End game
font.quit()
joystick.quit()
mixer.quit()
quit()
exit()
