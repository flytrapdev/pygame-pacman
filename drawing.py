from pygame import Surface, font, draw, transform
from globals import *
from map import ghost_exception

#######################
###      FONTS      ###
#######################

font.init()
ft = font.Font('PressStart2P.ttf', 8)

#######################
###     DRAWING     ###
#######################

def clear_screen():
    #Clear surface
    draw.rect(GAME_SURF, (0,0,0), GAME_SURF.get_rect())

def draw_text_centered(str, pos, col = C_WHITE):
    '''Draw text centered on pos'''
    render = ft.render(str, False, col, 8)
    render_rect = render.get_rect()
    new_pos = (round(pos[0] - render_rect.w/2), round(pos[1] - render_rect.h/2))
    GAME_SURF.blit(render, new_pos)

def draw_text_align_right(str, pos, col = C_WHITE):
    '''Draw text aligned right on pos'''
    render = ft.render(str, False, col, 8)
    render_rect = render.get_rect()
    new_pos = (round(pos[0] - render_rect.w), pos[1])
    GAME_SURF.blit(render, new_pos)

#######################
###    DRAW MAZE    ###
#######################

def draw_maze():
    '''Draw maze and pellets'''
    #Clear surface
    clear_screen()

    flash = game['complete']

    # Maze flashes when completed
    clear_flash = flash and time.get_ticks() % 500 < 250

    #Blit maze
    maze_rect = (SHEET_MAZE[0] + SHEET_MAZE[2] * game_settings['maze'],
                SHEET_MAZE[1] + SHEET_MAZE[3] * clear_flash,
                SHEET_MAZE[2], SHEET_MAZE[3])
    GAME_SURF.blit(mazes, (0,MAZE_YOFFSET,SHEET_MAZE[2],SHEET_MAZE[3]), maze_rect)

    for row in range(0, MAZE_HEIGHT):
        for i in range(0, MAZE_WIDTH):

            pos = (i*TILE_SIZE, MAZE_YOFFSET + row * TILE_SIZE, TILE_SIZE, TILE_SIZE)

            #Draw dot
            if layout[row][i] == COLL_DOT:
                GAME_SURF.blit(sprites, pos, SHEET_DOT)

            #Draw power pellet
            if layout[row][i] == COLL_POW and time.get_ticks() % 500 < 250:
                GAME_SURF.blit(sprites, pos, SHEET_POW)

def draw_targets():
    '''Draw target tiles'''
    target_color = {'blinky':(255,0,0), 'inky':(0,255,255),'pinky':(255,0,255),'clyde':(255,128,0)}
    for g in ghosts:
        draw.rect(GAME_SURF, target_color[g.type], (g.target_x*TILE_SIZE, g.target_y*TILE_SIZE+MAZE_YOFFSET, TILE_SIZE, TILE_SIZE))

#######################
###       HUD       ###
#######################

def draw_hud():
    '''Draw HUD'''
    # Blit text
    pos = [(24,0), (176,0)]
    score_pos = [(36,12), (188,12)]
    total_pos = [(36,20), (188,20)]

    # Draw scores and lives
    for i in range(min (game_settings['player_nb'], PLAYERNB_MAX)):
        GAME_SURF.blit(ft.render(str(i+1) + 'UP', False, C_WHITE), pos[i])
        draw_text_centered(str(player[i].score), score_pos[i])
        # Total score for 2 player vs mode
        if player[i].prev_score > 0:
            draw_text_centered(str(player[i].score + player[i].prev_score), total_pos[i], C_GRAY)

        # Draw lives
        x, y = player[i].skin
        x0, y0, w, h = SHEET_LIVES
        life_icon = (x0 + x*w, y0 + y*h,\
            w, h)

        x, y = (SCREEN_W-w) * i, SCREEN_H - h

        draw_dir= 1 if i==0 else -1

        for j in range(player[i].lives):

            GAME_SURF.blit(sprites, (x+j*SHEET_LIVES[2]*draw_dir, y), life_icon)

def draw_prompt(text=['INSERT COIN', 'PRESS ENTER'], x=SCREEN_HW, y=SCREEN_H-6):
    '''Draw credits prompt'''
    flash_delay = 600
    text_to_show = floor( (time.get_ticks() % (4*flash_delay)) / (2*flash_delay) )

    if time.get_ticks() % (2*flash_delay) < 1.5*flash_delay:
        draw_text_centered(text[text_to_show], (x, y))

#######################
###      INTRO      ###
#######################

def draw_intro(timer):
    '''Draw intro screen'''

    pacman_moves = 0 < timer-840 < 256

    clear_screen()
    draw_prompt()
    # Intro text
    intro_text = ['FytrapDev presents','Pygame-powered']
    for i in range(0,2):
        if timer >= 30 + 90 * i:
            draw_text_centered(intro_text[i], (SCREEN_HW, 16 + 16 * i))
    # Logo
    if timer >= 210 :
        logo_rect = logo.get_rect()
        logo_pos = (round(SCREEN_HW - logo_rect.w/2), 44)

        GAME_SURF.blit(logo, logo_pos)

    ghost_text = [s.upper() for s in GHOST_NAMES]
    ghost_colors = [C_BLINKY, C_PINKY, C_INKY, C_CLYDE]
    x0, y0, w, h = SHEET_GHOSTS
    ghost_sprites = [(x0, y0, w, h), (x0, y0+h, w, h), (x0, y0+2*h, w, h), (x0, y0+3*h, w, h)]

    # Ghost images
    if timer > 872 :
        x0, y0, w, h = SHEET_SCARED
        for i in range(4):
            if timer - 840 < 208 - i*40:
                # Scared
                img = (timer/12) % 2
                ghost_sprites[i] = (x0 + floor(img)*w, y0, w, h)
            else :
                # Eaten
                ghost_sprites[i] = (x0, y0+h, w, h)

    # Starring
    if timer >= 300:
        coords = (SCREEN_HW, 96)
        draw_text_centered('starring', coords)

    # Ghosts
    for i in range(4):
        if timer >= 390 + 90 * i:
            coords = (168, 112 + i*20)
            draw_text_align_right(ghost_text[i], coords, ghost_colors[i])
            coords = (56, 108 + i*20)
            GAME_SURF.blit(sprites, coords, ghost_sprites[i])

    # Characters
    player_text = ['PAC-MAN','MS','JR','OTTO']
    player_sprites = [(16, 32, 16, 16), (16, 144, 16, 16), (16, 224, 16, 16), (0, 336, 16, 16)]

    if timer >= 750:
        # Dots
        for i in range(2):
            if timer - 840 < 24 + i*16:
                coords = (60, 208 - i*8)
                GAME_SURF.blit(sprites, coords, SHEET_DOT)
        # Power pellet
        if timer - 840 < 56 and time.get_ticks() % 500 < 250:
            coords = (60, 192)
            GAME_SURF.blit(sprites, coords, SHEET_POW)
        # Draw characters
        for i in range(4):
            coords = (64 + 32*i, 240 + 12*(i%2))
            draw_text_centered(player_text[i], coords)
            if i > 0:
                coords = (56 + 32*i, 216)
            else:
                # Pacman moves
                pac_y = round(clamp(216 - (timer-840)/2, 88, 216))
                coords = (56, pac_y)
                # Pacman animation
                if pacman_moves:
                    player_sprites[0] = (16 * floor((timer/2)%4), 16, 16, 16)
            GAME_SURF.blit(characters, coords, player_sprites[i])

#######################
###      MENUS      ###
#######################

def draw_title(choice):
    '''Draw main menu'''
    clear_screen()

    # Draw logo
    logo_rect = logo.get_rect()
    logo_pos = (round(SCREEN_HW - logo_rect.w/2), 44)
    GAME_SURF.blit(logo, logo_pos)

    draw_menu(SCREEN_HW, 176, choice, ['START GAME', 'ONLINE GAME', 'SETTINGS', 'QUIT'])

def draw_options(choice):
    '''Draw options menu'''
    clear_screen()

    menu_text = ['N° OF PLAYERS', 'SELECT CHARACTER', 'N° OF LIVES', 'MAZE LAYOUT', 'CHANGE LAYOUT',\
        'FIRST LEVEL', 'BACK']
    layout_text = ['NEVER', 'ALWAYS', 'ASK', '1/2', '1/3']
    option_text = [str(game_settings['player_nb']), '', str(game_settings['lives']), MAZE_NAMES[game_settings['maze']],\
        layout_text[game_settings['change']], str(game_settings['starting_level']), '']

    if game_settings['lives'] == LIVES_INFINITE:
        option_text[2] = 'INFINITE'

    text_x = 32

    draw_menu(SCREEN_HW, 32, choice, menu_text, option_text)

def draw_skin_menu():
    '''Draw the skin menu'''
    clear_screen()

    nb = game_settings['player_nb']
    spr_size = SHEET_PACMAN[2]
    y = SCREEN_HH

    for i in range(nb):
        skin = player_skin[i]
        x = SCREEN_HW + ( 64*i - 32 * (nb - 1) )
        area = (SHEET_PACMAN[0] + spr_size * (3 + 4*skin[0]), SHEET_PACMAN[1] + spr_size*7 * skin[1], SHEET_PACMAN[2], SHEET_PACMAN[3])
        GAME_SURF.blit(characters, (x - spr_size/2, y - spr_size/2), area)

    draw_text_centered('PRESS ENTER WHEN FINISHED', (SCREEN_HW, y + 64))

def draw_results(choice = 0, maze = 0):
    '''Draw end of level screen'''
    clear_screen()
    draw_hud()

    width = SCREEN_W - 80
    player_nb = game_settings['player_nb']
    if player_nb > 1:
        # Get winner
        max_score = -1
        max_pl = 0
        max_i = 0
        for i in range(player_nb):
            if player[i].score > max_score:
                max_score = player[i].score
                max_pl = player[i]
                max_i = i
        # Draw winner
        winner_surf = Surface((SHEET_PACMAN[2], SHEET_PACMAN[3]))
        max_pl.draw(SHEET_PACMAN[2]/2, SHEET_PACMAN[3]/2, winner_surf)
        winner_surf_scale = transform.scale( winner_surf, (SHEET_PACMAN[2]*2, SHEET_PACMAN[3]*2) )

        GAME_SURF.blit(winner_surf_scale, (SCREEN_HW - SHEET_PACMAN[2], SCREEN_HH - SHEET_PACMAN[3]))
        draw_text_centered("PLAYER "+str(max_i+1)+" WINS !", (SCREEN_HW, SCREEN_HH + 32))

    # Draw menu
    if game_settings['change'] == CHANGE_ASK:
        draw_menu(SCREEN_HW, SCREEN_HH + 64, choice, ['LAYOUT', 'CONTINUE','QUIT'], [MAZE_NAMES[maze],'',''], width)
    else:
        draw_menu(SCREEN_HW, SCREEN_HH + 80, choice, ['CONTINUE','QUIT'], [], width)

def draw_net_menu(choice = 0):
    '''Draw netgame menu'''
    alt_text = [net_settings['ip'], str(net_settings['port'])]
    if len(net_settings['ip']) < 1:
        alt_text[0] = 'DEFAULT'
    if net_settings['port'] < 1:
        alt_text[1] = 'DEFAULT'
    clear_screen()
    # Draw logo
    logo_rect = logo.get_rect()
    logo_pos = (round(SCREEN_HW - logo_rect.w/2), 44)
    GAME_SURF.blit(logo, logo_pos)

    draw_menu(SCREEN_HW, 152, choice, ['IP','PORT'], alt_text)
    draw_menu(SCREEN_HW, 200, choice-2, ['HOST','JOIN','CANCEL'])

def draw_net_wait(net):
    '''Draw the net waiting screen'''
    clear_screen()
    text = 'LISTENING ON' if net_settings['type'] == NET_HOST else 'CONNECTING TO'
    GAME_SURF.blit(ft.render(text, False, C_WHITE), (32, 32))
    addr = net.get_name()
    addr_text = addr[0] + ':' + str(addr[1])
    GAME_SURF.blit(ft.render(addr_text, False, C_WHITE), (32, 56))

def draw_menu(x, y, choice, text, text_alt = [], width = SCREEN_W - 64):
    '''Draw a simple menu'''
    draw_alt = len(text_alt) > 0

    for i in range(len(text)):
        text_y = y + i*24

        if choice == i:
            draw.rect(GAME_SURF, C_WHITE, (x - (width/2 + 4), text_y-4, width + 8, 16))
            text_col = (0,0,0)
        else:
            text_col = C_WHITE

        if draw_alt :
            # Left aligned text
            text_x = x - width/2
            GAME_SURF.blit(ft.render(text[i], False, text_col), (text_x, text_y))
            # Right aligned text
            text_x = x + width/2
            draw_text_align_right(text_alt[i], (text_x, text_y), text_col)
        else :
            # Centered text
            text_x = x
            text_y += 4
            draw_text_centered(text[i], (SCREEN_HW, text_y), text_col)
