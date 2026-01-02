import pygame
from board.chessboard import board
from board.tile import Tile
import math
from pieces.nullpiece import nullpiece
from pieces.queen import queen
from pieces.rook import rook
from pieces.knight import knight
from pieces.bishop import bishop
from pieces.king import king
from pieces.pawn import pawn
from player.AI import AI
import copy
import pickle
import os
import sys

from board.move import move



pygame.init()
gamedisplay= pygame.display.set_mode((1000,800))
pygame.display.set_caption("pychess")
clock=pygame.time.Clock()

chessBoard=board()
chessBoard.createboard()
chessBoard.printboard()
movex=move()
ai=AI()

allTiles= []
allpieces=[]

# Load Sound Effects
try:
    move_sound = pygame.mixer.Sound('pieces/move.wav')
    capture_sound = pygame.mixer.Sound('pieces/capture.wav')
except pygame.error:
    print("Warning: Sound files (move.wav, capture.wav) not found. No sound will be played.")
    class DummySound:
        def play(self): pass
    move_sound = DummySound()
    capture_sound = DummySound()

######################
######################
# UI Colors
BACKGROUND_COLOR = (49, 46, 43)
BUTTON_COLOR = (118, 150, 86)
TEXT_COLOR = (255, 255, 255)

THEMES = [
    ((240, 217, 181), (181, 136, 99), "Classic"),
    ((238, 238, 210), (118, 150, 86), "Green"),
    ((232, 235, 239), (125, 135, 150), "Blue"),
    ((210, 180, 140), (139, 69, 19), "Wood"),
    ((140, 140, 140), (80, 80, 80), "Dark")
]
current_theme_idx = 0
BOARD_WHITE = THEMES[current_theme_idx][0]
BOARD_BLACK = THEMES[current_theme_idx][1]
HIGHLIGHT_COLOR = (186, 202, 68)
HINT_COLOR = (100, 200, 255)

font = pygame.font.Font('freesansbold.ttf', 32)
font_small = pygame.font.Font('freesansbold.ttf', 20)
text = font.render('pychess', True, TEXT_COLOR, BACKGROUND_COLOR)
text1 = font.render('AI',True,TEXT_COLOR)
text2 = font.render('2 player',True,TEXT_COLOR)
text3=font.render('Black won by checkmate', True, TEXT_COLOR)
text4=font.render('White won by checkmate', True, TEXT_COLOR)
text5=font.render('Draw (Stalemate/Material)', True, TEXT_COLOR)
text6=font.render('Made by: Kailash', True, TEXT_COLOR)
text_timeout_w = font.render('White lost on time', True, TEXT_COLOR)
text_timeout_b = font.render('Black lost on time', True, TEXT_COLOR)
text_resign_w = font.render('White Resigned - Black Wins', True, TEXT_COLOR)
text_resign_b = font.render('Black Resigned - White Wins', True, TEXT_COLOR)
text_easy = font.render('Easy', True, TEXT_COLOR)
text_medium = font.render('Medium', True, TEXT_COLOR)
text_hard = font.render('Hard', True, TEXT_COLOR)
text_tutorial = font.render('Tutorial', True, TEXT_COLOR)
text_mate1 = font.render('Mate in 1', True, TEXT_COLOR)
text_mate2 = font.render('Mate in 2', True, TEXT_COLOR)
text_success = font.render('Success! Checkmate.', True, TEXT_COLOR)
text_fail = font.render('Failed. Try Again.', True, TEXT_COLOR)
text_spectator = font.render('Spectator', True, TEXT_COLOR)

textRect = text.get_rect()
textRect1 = text1.get_rect()
textRect2 = text2.get_rect()
textRect3 = text3.get_rect()
textRect4 = text4.get_rect()
textRect5 = text5.get_rect()
textRect6 = text6.get_rect()
textRect_timeout_w = text_timeout_w.get_rect()
textRect_timeout_b = text_timeout_b.get_rect()
textRect_resign_w = text_resign_w.get_rect()
textRect_resign_b = text_resign_b.get_rect()

textRect.center = (500,100)
textRect1.center = (300,350)
textRect2.center = (700,350)
textRect3.center = (500,400)
textRect4.center = (500,400)
textRect5.center = (500,400)
textRect6.center = (500,700)
textRect_timeout_w.center = (500, 400)
textRect_timeout_b.center = (500, 400)
textRect_resign_w.center = (500, 400)
textRect_resign_b.center = (500, 400)





saki=''
menu_state = 'main'
ai_depth = 3
hint_move = []
puzzle_moves_limit = 0
moves_made_count = 0
last_move = []

quitgame=False

def square(x,y,w,h,color):
    pygame.draw.rect(gamedisplay,color,[x,y,w,h])
    allTiles.append([color, [x,y,w,h]])

def drawchesspieces(flipped=False):
    xpos= 0
    ypos= 0
    color= 0
    width= 100
    height= 100
    black= BOARD_BLACK
    white= BOARD_WHITE
    number=0

    for r in range(8):
        for c in range(8):
            if flipped:
                rows = 7 - r
                column = 7 - c
            else:
                rows = r
                column = c

            if [rows, column] in last_move:
                sq_color = HIGHLIGHT_COLOR
            elif color%2==0:
                sq_color = white
            else:
                sq_color = black
            
            square(xpos,ypos,width,height,sq_color)
            
            if not chessBoard.gameTiles[rows][column].pieceonTile.tostring() == "-":
                img = pygame.image.load("./chessart/"
                                        + chessBoard.gameTiles[rows][column].pieceonTile.alliance[0].upper()
                                        + chessBoard.gameTiles[rows][column].pieceonTile.tostring().upper()
                                        + ".png")
                img=pygame.transform.scale(img, (100,100))
                allpieces.append([img,[xpos,ypos],chessBoard.gameTiles[rows][column].pieceonTile])
            
            xpos += 100
            color +=1
            number +=1

        color +=1
        xpos=0
        ypos+=100
        for img in allpieces:
            gamedisplay.blit(img[0],img[1])

drawchesspieces()


def updateposition(x,y):
    a=x*8
    b=a+y
    return b

def givecolour(x,y):

    if y%2==0:
        if x%2==0:
            return BOARD_WHITE
        else:
            return BOARD_BLACK

    else:
        if x%2==0:
            return BOARD_BLACK
        else:
            return BOARD_WHITE

def get_notation(row, col):
    files = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
    return f"{files[col]}{8-row}"

def draw_move_log(move_log):
    title = font_small.render("Move Log:", True, TEXT_COLOR)
    gamedisplay.blit(title, (810, 100))
    start_index = max(0, len(move_log) - 6)
    for i in range(start_index, len(move_log)):
        text_str = f"{i+1}. {move_log[i]}"
        text_render = font_small.render(text_str, True, TEXT_COLOR)
        gamedisplay.blit(text_render, (810, 130 + (i - start_index) * 20))

def check_material(gametiles):
    count = 0
    for rows in range(8):
        for column in range(8):
            if gametiles[rows][column].pieceonTile.tostring() != '-':
                count += 1
    if count == 2:
        return True
    return False

def format_time(seconds):
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes:02}:{secs:02}"

def draw_timer(white_time, black_time):
    pygame.draw.rect(gamedisplay, BACKGROUND_COLOR, [800, 0, 200, 800])
    
    b_text = font.render(f"Black: {format_time(black_time)}", True, TEXT_COLOR)
    w_text = font.render(f"White: {format_time(white_time)}", True, TEXT_COLOR)
    
    gamedisplay.blit(b_text, (810, 50))
    gamedisplay.blit(w_text, (810, 700))

def draw_undo():
    pygame.draw.rect(gamedisplay, BUTTON_COLOR, [810, 350, 180, 50])
    text_undo = font.render('Undo', True, TEXT_COLOR)
    textRect_undo = text_undo.get_rect()
    textRect_undo.center = (900, 375)
    gamedisplay.blit(text_undo, textRect_undo)

def draw_reset():
    pygame.draw.rect(gamedisplay, BUTTON_COLOR, [810, 450, 180, 50])
    text_reset = font.render('Reset', True, TEXT_COLOR)
    textRect_reset = text_reset.get_rect()
    textRect_reset.center = (900, 475)
    gamedisplay.blit(text_reset, textRect_reset)

def draw_save_load():
    pygame.draw.rect(gamedisplay, BUTTON_COLOR, [810, 550, 180, 50])
    text_save = font.render('Save', True, TEXT_COLOR)
    textRect_save = text_save.get_rect()
    textRect_save.center = (900, 575)
    gamedisplay.blit(text_save, textRect_save)

    pygame.draw.rect(gamedisplay, BUTTON_COLOR, [810, 650, 180, 50])
    text_load = font.render('Load', True, TEXT_COLOR)
    textRect_load = text_load.get_rect()
    textRect_load.center = (900, 675)
    gamedisplay.blit(text_load, textRect_load)

def draw_pause(paused):
    pygame.draw.rect(gamedisplay, BUTTON_COLOR, [810, 250, 180, 50])
    text_str = 'Resume' if paused else 'Pause'
    text_pause = font.render(text_str, True, TEXT_COLOR)
    textRect_pause = text_pause.get_rect()
    textRect_pause.center = (900, 275)
    gamedisplay.blit(text_pause, textRect_pause)

def draw_flip_btn(flipped):
    pygame.draw.rect(gamedisplay, BUTTON_COLOR, [810, 180, 180, 50])
    text_str = 'Flip Board'
    text_flip = font.render(text_str, True, TEXT_COLOR)
    textRect_flip = text_flip.get_rect()
    textRect_flip.center = (900, 205)
    gamedisplay.blit(text_flip, textRect_flip)

def draw_resign_btn():
    pygame.draw.rect(gamedisplay, BUTTON_COLOR, [810, 740, 180, 50])
    text_res = font.render('Resign', True, TEXT_COLOR)
    textRect_res = text_res.get_rect()
    textRect_res.center = (900, 765)
    gamedisplay.blit(text_res, textRect_res)

def draw_hint_btn():
    pygame.draw.rect(gamedisplay, BUTTON_COLOR, [810, 80, 180, 40])
    text_str = 'Hint'
    text_hint = font_small.render(text_str, True, TEXT_COLOR)
    textRect_hint = text_hint.get_rect()
    textRect_hint.center = (900, 100)
    gamedisplay.blit(text_hint, textRect_hint)

def draw_popup(text_surface):
    # Draw Popup Box
    pygame.draw.rect(gamedisplay, BACKGROUND_COLOR, [200, 300, 600, 200])
    pygame.draw.rect(gamedisplay, HIGHLIGHT_COLOR, [200, 300, 600, 200], 5)
    # Center Text
    text_rect = text_surface.get_rect(center=(500, 360))
    gamedisplay.blit(text_surface, text_rect)
    
    # Draw Restart Button
    pygame.draw.rect(gamedisplay, BUTTON_COLOR, [425, 410, 150, 50])
    text_restart = font_small.render('Play Again', True, TEXT_COLOR)
    text_rect_restart = text_restart.get_rect(center=(500, 435))
    gamedisplay.blit(text_restart, text_rect_restart)

def start_countdown():
    font_big = pygame.font.Font('freesansbold.ttf', 120)
    for i in range(3, 0, -1):
        pygame.event.pump()
        gamedisplay.fill(BACKGROUND_COLOR)
        global allTiles, allpieces
        allTiles.clear()
        allpieces.clear()
        drawchesspieces()
        text_count = font_big.render(str(i), True, (255, 50, 50))
        rect_count = text_count.get_rect(center=(400, 400))
        gamedisplay.blit(text_count, rect_count)
        if i == 1:
            text_msg = font.render("Click the piece to move", True, TEXT_COLOR)
            rect_msg = text_msg.get_rect(center=(400, 550))
            gamedisplay.blit(text_msg, rect_msg)
        pygame.display.update()
        pygame.time.wait(1000)

def setup_puzzle(puzzle_type):
    global puzzle_moves_limit, moves_made_count, turn
    # Clear board
    for r in range(8):
        for c in range(8):
            chessBoard.gameTiles[r][c] = Tile(r*8+c, nullpiece())
    
    turn = 0 # White starts
    moves_made_count = 0

    if puzzle_type == 1: # Mate in 1
        puzzle_moves_limit = 1
        chessBoard.gameTiles[2][1] = Tile(17, king("White", 17)) # King at b6
        chessBoard.gameTiles[7][7] = Tile(63, rook("White", 63)) # Rook at h1
        chessBoard.gameTiles[0][0] = Tile(0, king("Black", 0))   # King at a8

    elif puzzle_type == 2: # Mate in 2
        puzzle_moves_limit = 2
        chessBoard.gameTiles[2][5] = Tile(21, king("White", 21)) # King at f6
        chessBoard.gameTiles[7][0] = Tile(56, rook("White", 56)) # Rook at a1
        chessBoard.gameTiles[0][7] = Tile(7, king("Black", 7))   # King at h8

while not quitgame:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            quitgame= True
            pygame.quit()
            quit()

        gamedisplay.fill(BACKGROUND_COLOR)
        
        if menu_state == 'main':
            gamedisplay.blit(text, textRect)
            pygame.draw.rect(gamedisplay,BUTTON_COLOR,[200,300,200,100])
            gamedisplay.blit(text1,textRect1)
            pygame.draw.rect(gamedisplay,BUTTON_COLOR,[600,300,200,100])
            gamedisplay.blit(text2,textRect2)
            gamedisplay.blit(text6, textRect6)
            pygame.draw.rect(gamedisplay, BUTTON_COLOR, [400, 500, 200, 80])
            gamedisplay.blit(text_tutorial, text_tutorial.get_rect(center=(500, 540)))
            pygame.draw.rect(gamedisplay, BUTTON_COLOR, [400, 400, 200, 80])
            gamedisplay.blit(text_spectator, text_spectator.get_rect(center=(500, 440)))
            
            pygame.draw.rect(gamedisplay, BUTTON_COLOR, [400, 600, 200, 80])
            text_theme = font.render(f'Theme: {THEMES[current_theme_idx][2]}', True, TEXT_COLOR)
            gamedisplay.blit(text_theme, text_theme.get_rect(center=(500, 640)))

            if event.type==pygame.MOUSEBUTTONDOWN:
                coord = pygame.mouse.get_pos()
                if coord[0]>=200 and coord[0]<=400 and coord[1]>=300 and coord[1]<=400:
                    menu_state = 'difficulty'
                if coord[0]>=600 and coord[0]<=800 and coord[1]>=300 and coord[1]<=400:
                    saki='2 player'
                    quitgame=True
                if coord[0]>=400 and coord[0]<=600 and coord[1]>=500 and coord[1]<=580:
                    menu_state = 'tutorial_menu'
                if coord[0]>=400 and coord[0]<=600 and coord[1]>=400 and coord[1]<=480:
                    saki='spectator'
                    quitgame=True
                if coord[0]>=400 and coord[0]<=600 and coord[1]>=600 and coord[1]<=680:
                    current_theme_idx = (current_theme_idx + 1) % len(THEMES)
                    BOARD_WHITE = THEMES[current_theme_idx][0]
                    BOARD_BLACK = THEMES[current_theme_idx][1]
        
        elif menu_state == 'difficulty':
            title_diff = font.render('Select Difficulty', True, TEXT_COLOR)
            rect_diff = title_diff.get_rect(center=(500, 150))
            gamedisplay.blit(title_diff, rect_diff)

            pygame.draw.rect(gamedisplay, BUTTON_COLOR, [400, 250, 200, 80])
            gamedisplay.blit(text_easy, text_easy.get_rect(center=(500, 290)))

            pygame.draw.rect(gamedisplay, BUTTON_COLOR, [400, 350, 200, 80])
            gamedisplay.blit(text_medium, text_medium.get_rect(center=(500, 390)))

            pygame.draw.rect(gamedisplay, BUTTON_COLOR, [400, 450, 200, 80])
            gamedisplay.blit(text_hard, text_hard.get_rect(center=(500, 490)))

            if event.type==pygame.MOUSEBUTTONDOWN:
                coord = pygame.mouse.get_pos()
                if 400 <= coord[0] <= 600:
                    if 250 <= coord[1] <= 330: ai_depth = 1; saki='ai'; quitgame=True
                    elif 350 <= coord[1] <= 430: ai_depth = 2; saki='ai'; quitgame=True
                    elif 450 <= coord[1] <= 530: ai_depth = 3; saki='ai'; quitgame=True

        elif menu_state == 'tutorial_menu':
            title_tut = font.render('Select Puzzle', True, TEXT_COLOR)
            rect_tut = title_tut.get_rect(center=(500, 150))
            gamedisplay.blit(title_tut, rect_tut)

            pygame.draw.rect(gamedisplay, BUTTON_COLOR, [400, 250, 200, 80])
            gamedisplay.blit(text_mate1, text_mate1.get_rect(center=(500, 290)))

            pygame.draw.rect(gamedisplay, BUTTON_COLOR, [400, 350, 200, 80])
            gamedisplay.blit(text_mate2, text_mate2.get_rect(center=(500, 390)))

            if event.type==pygame.MOUSEBUTTONDOWN:
                coord = pygame.mouse.get_pos()
                if 400 <= coord[0] <= 600:
                    if 250 <= coord[1] <= 330: setup_puzzle(1); saki='tutorial'; quitgame=True
                    elif 350 <= coord[1] <= 430: setup_puzzle(2); saki='tutorial'; quitgame=True

        pygame.display.update()
        clock.tick(60)

TIME_LIMIT = 600 # 10 minutes

if saki=='2 player':
    start_countdown()

    moves=[]
    enpassant=[]
    promote=[]
    promotion=False
    turn=0

    array=[]
    quitgame=False

    flipped = False
    hint_move = []
    paused = False
    move_log = []
    history = []
    white_time = TIME_LIMIT
    black_time = TIME_LIMIT
    clock.tick(60) # Reset clock delta

    while not quitgame:
        if not paused:
            dt = clock.get_time() / 1000
            if turn % 2 == 0:
                white_time -= dt
                if white_time <= 0:
                    saki = 'end_timeout_w'
                    quitgame = True
            else:
                black_time -= dt
                if black_time <= 0:
                    saki = 'end_timeout_b'
                    quitgame = True

        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                quitgame= True
                pygame.quit()
                quit()

            if check_material(chessBoard.gameTiles):
                saki='end3'
                quitgame=True

            if movex.checkw(chessBoard.gameTiles)[0]=='checked' and len(moves)==0 :
                array=movex.movesifcheckedw(chessBoard.gameTiles)
                if len(array)==0:
                    saki='end1'
                    quitgame=True

            if movex.checkb(chessBoard.gameTiles)[0]=='checked' and len(moves)==0 :
                array=movex.movesifcheckedb(chessBoard.gameTiles)
                if len(array)==0:
                    saki='end2'
                    quitgame=True


            if movex.checkb(chessBoard.gameTiles)[0]=='notchecked' and turn%2==1 and len(moves)==0 :
                check=False
                for x in range(8):
                    for y in range(8):
                        if chessBoard.gameTiles[y][x].pieceonTile.alliance=='Black' and turn%2==1:
                            moves1=chessBoard.gameTiles[y][x].pieceonTile.legalmoveb(chessBoard.gameTiles)
                            lx1=movex.pinnedb(chessBoard.gameTiles,moves1,y,x)
                            if len(lx1)==0:
                                continue
                            else:
                                check=True
                            if check==True:
                                break
                    if check==True:
                        break


                if check==False:
                    saki='end3'
                    quitgame=True

            if movex.checkw(chessBoard.gameTiles)[0]=='notchecked' and turn%2==0 and len(moves)==0 :
                check=False
                for x in range(8):
                    for y in range(8):
                        if chessBoard.gameTiles[y][x].pieceonTile.alliance=='White' and turn%2==0:
                            moves1=chessBoard.gameTiles[y][x].pieceonTile.legalmoveb(chessBoard.gameTiles)
                            lx1=movex.pinnedw(chessBoard.gameTiles,moves1,y,x)
                            if len(lx1)==0:
                                continue
                            else:
                                check=True
                            if check==True:
                                break
                    if check==True:
                        break


                if check==False:
                    saki='end3'
                    quitgame=True

                                









            if event.type==pygame.MOUSEBUTTONDOWN:
                coord = pygame.mouse.get_pos()
                if coord[0]>=810 and coord[0]<=990 and coord[1]>=250 and coord[1]<=300:
                    paused = not paused
                    continue
                
                if paused:
                    continue

                if coord[0]>=810 and coord[0]<=990 and coord[1]>=80 and coord[1]<=120:
                    # Hint Button Clicked
                    sc = copy.deepcopy(chessBoard.gameTiles)
                    # If turn is even (0, 2..), it's White's turn.
                    is_white = (turn % 2 == 0)
                    # Use depth 2 for hints to be quick
                    hy, hx, hfx, hfy = ai.evaluate(sc, 2, is_white)
                    hint_move = [[hy, hx], [hfx, hfy]]
                    continue

                if coord[0]>=810 and coord[0]<=990 and coord[1]>=180 and coord[1]<=230:
                    flipped = not flipped
                    allTiles.clear()
                    allpieces.clear()
                    drawchesspieces(flipped)
                    continue

                if coord[0]>=810 and coord[0]<=990 and coord[1]>=350 and coord[1]<=400:
                    if len(history) > 0:
                        state = history.pop()
                        chessBoard.gameTiles = copy.deepcopy(state[0])
                        turn = state[1]
                        white_time = state[2]
                        black_time = state[3]
                        enpassant = copy.deepcopy(state[4])
                        last_move = copy.deepcopy(state[5])
                        move_log = copy.deepcopy(state[6])
                        hint_move = []
                        moves = []
                        promote = []
                        promotion = False
                        allTiles.clear()
                        allpieces.clear()
                        chessBoard.printboard()
                        drawchesspieces(flipped)
                        continue

                if coord[0]>=810 and coord[0]<=990 and coord[1]>=450 and coord[1]<=500:
                    chessBoard = board()
                    chessBoard.createboard()
                    moves=[]
                    enpassant=[]
                    promote=[]
                    promotion=False
                    turn=0
                    flipped = False
                    hint_move = []
                    paused = False
                    move_log = []
                    history = []
                    white_time = TIME_LIMIT
                    black_time = TIME_LIMIT
                    last_move = []
                    allTiles.clear()
                    allpieces.clear()
                    chessBoard.printboard()
                    drawchesspieces(flipped)
                    continue

                if coord[0]>=810 and coord[0]<=990 and coord[1]>=550 and coord[1]<=600:
                    game_state = {
                        'tiles': chessBoard.gameTiles,
                        'turn': turn,
                        'white_time': white_time,
                        'black_time': black_time,
                        'enpassant': enpassant,
                        'last_move': last_move,
                        'history': history,
                        'move_log': move_log
                    }
                    with open('savegame.pkl', 'wb') as f:
                        pickle.dump(game_state, f)
                    continue

                if coord[0]>=810 and coord[0]<=990 and coord[1]>=650 and coord[1]<=700:
                    if os.path.exists('savegame.pkl'):
                        with open('savegame.pkl', 'rb') as f:
                            game_state = pickle.load(f)
                        chessBoard.gameTiles = game_state['tiles']
                        turn = game_state['turn']
                        white_time = game_state['white_time']
                        black_time = game_state['black_time']
                        enpassant = game_state['enpassant']
                        last_move = game_state['last_move']
                        history = game_state['history']
                        move_log = game_state.get('move_log', [])
                        hint_move = []
                        moves = []
                        promote = []
                        promotion = False
                        allTiles.clear()
                        allpieces.clear()
                        chessBoard.printboard()
                        drawchesspieces(flipped)
                    continue

                if coord[0]>=810 and coord[0]<=990 and coord[1]>=740 and coord[1]<=790:
                    if turn % 2 == 0:
                        saki = 'resigned_w'
                    else:
                        saki = 'resigned_b'
                    quitgame = True
                    continue

                if movex.checkw(chessBoard.gameTiles)[0]=='checked' and len(moves)==0 :
                    array=movex.movesifcheckedw(chessBoard.gameTiles)
                    coord=pygame.mouse.get_pos()
                    if coord[0] >= 800: continue
                    m=math.floor(coord[0]/100)
                    n=math.floor(coord[1]/100)
                    if flipped:
                        m = 7 - m
                        n = 7 - n
                    imgx=pygame.transform.scale(pygame.image.load("./chessart/red_square.png",), (100,100))
                    mx=[]
                    ma=[]
                    for move in array:
                        if(move[1]==m and move[0]==n):
                            mx=[move[3]*100,move[2]*100]
                            ma=[move[2],move[3]]
                            if flipped:
                                mx=[(7-move[3])*100, (7-move[2])*100]
                            moves.append(ma)
                            gamedisplay.blit(imgx,mx)
                            x=move[1]
                            y=move[0]
                    break

                if movex.checkb(chessBoard.gameTiles)[0]=='checked' and len(moves)==0 :
                    array=movex.movesifcheckedb(chessBoard.gameTiles)
                    coord=pygame.mouse.get_pos()
                    if coord[0] >= 800: continue
                    m=math.floor(coord[0]/100)
                    n=math.floor(coord[1]/100)
                    if flipped:
                        m = 7 - m
                        n = 7 - n
                    imgx=pygame.transform.scale(pygame.image.load("./chessart/red_square.png",), (100,100))
                    mx=[]
                    ma=[]
                    for move in array:
                        if(move[1]==m and move[0]==n):
                            mx=[move[3]*100,move[2]*100]
                            ma=[move[2],move[3]]
                            if flipped:
                                mx=[(7-move[3])*100, (7-move[2])*100]
                            moves.append(ma)
                            gamedisplay.blit(imgx,mx)
                            x=move[1]
                            y=move[0]
                    break

                if not len(promote)==0:
                    coord = pygame.mouse.get_pos()
                    if coord[0] >= 800: continue
                    m=math.floor(coord[0]/100)
                    n=math.floor(coord[1]/100)
                    if flipped:
                        m = 7 - m
                        n = 7 - n
                    if  chessBoard.gameTiles[promote[5][0]][promote[5][1]].pieceonTile.alliance=='Black':
                        for i in range(len(promote)):
                            if i==4:
                                turn=turn-1
                                break
                            if promote[i][0]==n and promote[i][1]==m:
                                if i==0:
                                    chessBoard.gameTiles[promote[4][1]][promote[4][0]].pieceonTile=queen('Black',updateposition(promote[4][1],promote[4][0]))
                                    chessBoard.gameTiles[promote[5][0]][promote[5][1]].pieceonTile=nullpiece()
                                    last_move = [[promote[5][0], promote[5][1]], [promote[4][1], promote[4][0]]]
                                    break
                                if i==1:
                                    chessBoard.gameTiles[promote[4][1]][promote[4][0]].pieceonTile=rook('Black',updateposition(promote[4][1],promote[4][0]))
                                    chessBoard.gameTiles[promote[5][0]][promote[5][1]].pieceonTile=nullpiece()
                                    last_move = [[promote[5][0], promote[5][1]], [promote[4][1], promote[4][0]]]
                                    break
                                if i==2:
                                    chessBoard.gameTiles[promote[4][1]][promote[4][0]].pieceonTile=knight('Black',updateposition(promote[4][1],promote[4][0]))
                                    chessBoard.gameTiles[promote[5][0]][promote[5][1]].pieceonTile=nullpiece()
                                    last_move = [[promote[5][0], promote[5][1]], [promote[4][1], promote[4][0]]]
                                    break
                                if i==3:
                                    chessBoard.gameTiles[promote[4][1]][promote[4][0]].pieceonTile=bishop('Black',updateposition(promote[4][1],promote[4][0]))
                                    chessBoard.gameTiles[promote[5][0]][promote[5][1]].pieceonTile=nullpiece()
                                    last_move = [[promote[5][0], promote[5][1]], [promote[4][1], promote[4][0]]]
                                    break

                    if  chessBoard.gameTiles[promote[5][0]][promote[5][1]].pieceonTile.alliance=='White':
                        for i in range(len(promote)):
                            if i==4:
                                turn=turn-1
                                break
                            if promote[i][0]==n and promote[i][1]==m:
                                if i==0:
                                    chessBoard.gameTiles[promote[4][1]][promote[4][0]].pieceonTile=queen('White',updateposition(promote[4][1],promote[4][0]))
                                    chessBoard.gameTiles[promote[5][0]][promote[5][1]].pieceonTile=nullpiece()
                                    last_move = [[promote[5][0], promote[5][1]], [promote[4][1], promote[4][0]]]
                                    break
                                if i==1:
                                    chessBoard.gameTiles[promote[4][1]][promote[4][0]].pieceonTile=rook('White',updateposition(promote[4][1],promote[4][0]))
                                    chessBoard.gameTiles[promote[5][0]][promote[5][1]].pieceonTile=nullpiece()
                                    last_move = [[promote[5][0], promote[5][1]], [promote[4][1], promote[4][0]]]
                                    break
                                if i==2:
                                    chessBoard.gameTiles[promote[4][1]][promote[4][0]].pieceonTile=knight('White',updateposition(promote[4][1],promote[4][0]))
                                    chessBoard.gameTiles[promote[5][0]][promote[5][1]].pieceonTile=nullpiece()
                                    last_move = [[promote[5][0], promote[5][1]], [promote[4][1], promote[4][0]]]
                                    break
                                if i==3:
                                    chessBoard.gameTiles[promote[4][1]][promote[4][0]].pieceonTile=bishop('White',updateposition(promote[4][1],promote[4][0]))
                                    chessBoard.gameTiles[promote[5][0]][promote[5][1]].pieceonTile=nullpiece()
                                    last_move = [[promote[5][0], promote[5][1]], [promote[4][1], promote[4][0]]]
                                    break

                    allTiles.clear()
                    allpieces.clear()
                    chessBoard.printboard()
                    drawchesspieces(flipped)
                    promote=[]
                    promotion=False







                if not len(moves)==0:
                    coord = pygame.mouse.get_pos()
                    if coord[0] >= 800: continue
                    m=math.floor(coord[0]/100)
                    n=math.floor(coord[1]/100)
                    if flipped:
                        m = 7 - m
                        n = 7 - n
                    
                    # Logic to allow re-selection:
                    # If a piece is already selected (moves > 0) but we clicked an invalid square,
                    # clear the selection so the code below can try to select the new piece.
                    if len(moves) > 0:
                        clicked_valid_move = False
                        for move in moves:
                            if move[0] == n and move[1] == m:
                                clicked_valid_move = True
                                break
                        if not clicked_valid_move:
                            moves = []
                            # We don't redraw here, the selection logic below will handle it.

                    for move in moves:
                        if move[0]==n and move[1]==m:
                            hint_move = [] # Clear hint on move
                            history.append((copy.deepcopy(chessBoard.gameTiles), turn, white_time, black_time, copy.deepcopy(enpassant), copy.deepcopy(last_move), copy.deepcopy(move_log)))
                            turn=turn+1
                            is_capture = False
                            if chessBoard.gameTiles[n][m].pieceonTile.tostring() != '-':
                                is_capture = True
                            if chessBoard.gameTiles[y][x].pieceonTile.tostring()=='K' or chessBoard.gameTiles[y][x].pieceonTile.tostring()=='R' or chessBoard.gameTiles[y][x].pieceonTile.tostring()=='k' or chessBoard.gameTiles[y][x].pieceonTile.tostring()=='r':
                                chessBoard.gameTiles[y][x].pieceonTile.moved=True


                            if chessBoard.gameTiles[y][x].pieceonTile.tostring()=='K' and m==x+2:
                                chessBoard.gameTiles[y][x+1].pieceonTile=chessBoard.gameTiles[y][x+3].pieceonTile
                                s=updateposition(y,x+1)
                                chessBoard.gameTiles[y][x+1].pieceonTile.position=s
                                chessBoard.gameTiles[y][x+3].pieceonTile=nullpiece()
                            if chessBoard.gameTiles[y][x].pieceonTile.tostring()=='K' and m==x-2:
                                chessBoard.gameTiles[y][x-1].pieceonTile=chessBoard.gameTiles[y][0].pieceonTile
                                s=updateposition(y,x-1)
                                chessBoard.gameTiles[y][x-1].pieceonTile.position=s
                                chessBoard.gameTiles[y][0].pieceonTile=nullpiece()

                            if chessBoard.gameTiles[y][x].pieceonTile.tostring()=='k' and m==x+2:
                                chessBoard.gameTiles[y][x+1].pieceonTile=chessBoard.gameTiles[y][x+3].pieceonTile
                                s=updateposition(y,x+1)
                                chessBoard.gameTiles[y][x+1].pieceonTile.position=s
                                chessBoard.gameTiles[y][x+3].pieceonTile=nullpiece()
                            if chessBoard.gameTiles[y][x].pieceonTile.tostring()=='k' and m==x-2:
                                chessBoard.gameTiles[y][x-1].pieceonTile=chessBoard.gameTiles[y][0].pieceonTile
                                s=updateposition(y,x-1)
                                chessBoard.gameTiles[y][x-1].pieceonTile.position=s
                                chessBoard.gameTiles[y][0].pieceonTile=nullpiece()



                            if not len(enpassant)==0:
                                chessBoard.gameTiles[enpassant[0]][enpassant[1]].pieceonTile.enpassant=False
                                enpassant=[]
                            if chessBoard.gameTiles[y][x].pieceonTile.tostring()=='P' and y+1==n and x+1==m and chessBoard.gameTiles[n][m].pieceonTile.tostring()=='-':
                                chessBoard.gameTiles[y][x+1].pieceonTile=nullpiece()
                                is_capture = True
                            if chessBoard.gameTiles[y][x].pieceonTile.tostring()=='P' and y+1==n and x-1==m and chessBoard.gameTiles[n][m].pieceonTile.tostring()=='-':
                                chessBoard.gameTiles[y][x-1].pieceonTile=nullpiece()
                                is_capture = True

                            if chessBoard.gameTiles[y][x].pieceonTile.tostring()=='p' and y-1==n and x+1==m and chessBoard.gameTiles[n][m].pieceonTile.tostring()=='-':
                                chessBoard.gameTiles[y][x+1].pieceonTile=nullpiece()
                                is_capture = True
                            if chessBoard.gameTiles[y][x].pieceonTile.tostring()=='p' and y-1==n and x-1==m and chessBoard.gameTiles[n][m].pieceonTile.tostring()=='-':
                                chessBoard.gameTiles[y][x-1].pieceonTile=nullpiece()
                                is_capture = True

                            if chessBoard.gameTiles[y][x].pieceonTile.tostring()=='p' and n==y-2:
                                chessBoard.gameTiles[y][x].pieceonTile.enpassant=True
                                enpassant=[n,m]

                            if chessBoard.gameTiles[y][x].pieceonTile.tostring()=='P' and n==y+2:
                                chessBoard.gameTiles[y][x].pieceonTile.enpassant=True
                                enpassant=[n,m]

                            if chessBoard.gameTiles[y][x].pieceonTile.tostring()=='P' and y+1==n and y==6:
                                promotion=True

                            if chessBoard.gameTiles[y][x].pieceonTile.tostring()=='p' and y-1==n and y==1:
                                promotion=True

                            if is_capture:
                                capture_sound.play()
                            else:
                                move_sound.play()

                            if promotion==False:
                                last_move = [[y, x], [n, m]]
                                move_log.append(f"{get_notation(y, x)} to {get_notation(n, m)}")
                                chessBoard.gameTiles[n][m].pieceonTile=chessBoard.gameTiles[y][x].pieceonTile
                                chessBoard.gameTiles[y][x].pieceonTile=nullpiece()
                                s=updateposition(n,m)
                                chessBoard.gameTiles[n][m].pieceonTile.position=s
                    if promotion==False:
                        allTiles.clear()
                        allpieces.clear()
                        chessBoard.printboard()
                        drawchesspieces(flipped)
                        moves=[]

                    if promotion==True:
                        if  chessBoard.gameTiles[y][x].pieceonTile.tostring()=='P' and x==7 and y==6:
                            pygame.draw.rect(gamedisplay,(255,255,255),[x*100-100,(y*100)-200,200,200])
                            imgx=pygame.transform.scale(pygame.image.load("./chessart/BQ.png",), (100,100))
                            imgx1=pygame.transform.scale(pygame.image.load("./chessart/BR.png",), (100,100))
                            imgx2=pygame.transform.scale(pygame.image.load("./chessart/BN.png",), (100,100))
                            imgx3=pygame.transform.scale(pygame.image.load("./chessart/BB.png",), (100,100))
                            gamedisplay.blit(imgx,[x*100-100,(y*100)-200])
                            gamedisplay.blit(imgx1,[(x*100),(y*100)-200])
                            gamedisplay.blit(imgx2,[x*100-100,(y*100)-100])
                            gamedisplay.blit(imgx3,[(x*100),(y*100)-100])
                            promote=[[y-2,x-1],[y-2,x],[y-1,x],[y-1,x],[m,n],[y,x]]
                            move_log.append(f"{get_notation(y, x)} to {get_notation(n, m)}")

                        elif chessBoard.gameTiles[y][x].pieceonTile.tostring()=='P':
                            pygame.draw.rect(gamedisplay,(255,255,255),[x*100,(y*100)-200,200,200])
                            imgx=pygame.transform.scale(pygame.image.load("./chessart/BQ.png",), (100,100))
                            imgx1=pygame.transform.scale(pygame.image.load("./chessart/BR.png",), (100,100))
                            imgx2=pygame.transform.scale(pygame.image.load("./chessart/BN.png",), (100,100))
                            imgx3=pygame.transform.scale(pygame.image.load("./chessart/BB.png",), (100,100))
                            gamedisplay.blit(imgx,[x*100,(y*100)-200])
                            gamedisplay.blit(imgx1,[(x*100)+100,(y*100)-200])
                            gamedisplay.blit(imgx2,[x*100,(y*100)-100])
                            gamedisplay.blit(imgx3,[(x*100)+100,(y*100)-100])
                            promote=[[y-2,x],[y-2,x+1],[y-1,x],[y-1,x+1],[m,n],[y,x]]
                            move_log.append(f"{get_notation(y, x)} to {get_notation(n, m)}")

                        elif  chessBoard.gameTiles[y][x].pieceonTile.tostring()=='p' and x==7 and y==1:
                            pygame.draw.rect(gamedisplay,(0,0,0),[x*100-100,(y*100)+100,200,200])
                            imgx=pygame.transform.scale(pygame.image.load("./chessart/WQ.png",), (100,100))
                            imgx1=pygame.transform.scale(pygame.image.load("./chessart/WR.png",), (100,100))
                            imgx2=pygame.transform.scale(pygame.image.load("./chessart/WN.png",), (100,100))
                            imgx3=pygame.transform.scale(pygame.image.load("./chessart/WB.png",), (100,100))
                            gamedisplay.blit(imgx,[x*100-100,(y*100)+200])
                            gamedisplay.blit(imgx1,[(x*100),(y*100)+200])
                            gamedisplay.blit(imgx2,[x*100-100,(y*100)+100])
                            gamedisplay.blit(imgx3,[(x*100),(y*100)+100])
                            promote=[[y+2,x-1],[y+2,x],[y+1,x],[y+1,x],[m,n],[y,x]]
                            move_log.append(f"{get_notation(y, x)} to {get_notation(n, m)}")

                        elif chessBoard.gameTiles[y][x].pieceonTile.tostring()=='p':
                            pygame.draw.rect(gamedisplay,(0,0,0),[x*100,(y*100)+100,200,200])
                            imgx=pygame.transform.scale(pygame.image.load("./chessart/WQ.png",), (100,100))
                            imgx1=pygame.transform.scale(pygame.image.load("./chessart/WR.png",), (100,100))
                            imgx2=pygame.transform.scale(pygame.image.load("./chessart/WN.png",), (100,100))
                            imgx3=pygame.transform.scale(pygame.image.load("./chessart/WB.png",), (100,100))
                            gamedisplay.blit(imgx,[x*100,(y*100)+200])
                            gamedisplay.blit(imgx1,[(x*100)+100,(y*100)+200])
                            gamedisplay.blit(imgx2,[x*100,(y*100)+100])
                            gamedisplay.blit(imgx3,[(x*100)+100,(y*100)+100])
                            promote=[[y+2,x],[y+2,x+1],[y+1,x],[y+1,x+1],[m,n],[y,x]]
                            move_log.append(f"{get_notation(y, x)} to {get_notation(n, m)}")










                else:
                    drawchesspieces(flipped)
                    coords = pygame.mouse.get_pos()
                    if coords[0] < 800:
                        x=math.floor(coords[0]/100)
                        y=math.floor(coords[1]/100)
                        if flipped:
                            x = 7 - x
                            y = 7 - y
                        mx=[]
                        if(not chessBoard.gameTiles[y][x].pieceonTile.tostring()=='-'):
                            moves=chessBoard.gameTiles[y][x].pieceonTile.legalmoveb(chessBoard.gameTiles)
                            if(chessBoard.gameTiles[y][x].pieceonTile.tostring()=='K'):
                                ax=movex.castlingb(chessBoard.gameTiles)
                                if not len(ax)==0:
                                    for l in ax:
                                        if l=='ks':
                                            moves.append([0,6])
                                        if l=='qs':
                                            moves.append([0,2])
                            if(chessBoard.gameTiles[y][x].pieceonTile.tostring()=='k'):
                                ax=movex.castlingw(chessBoard.gameTiles)
                                if not len(ax)==0:
                                    for l in ax:
                                        if l=='ks':
                                            moves.append([7,6])
                                        if l=='qs':
                                            moves.append([7,2])
                            if(chessBoard.gameTiles[y][x].pieceonTile.tostring()=='P'):
                                ay=movex.enpassantb(chessBoard.gameTiles,y,x)
                                if not len(ay)==0:
                                    if ay[1]=='r':
                                        moves.append([y+1,x+1])
                                    else:
                                        moves.append([y+1,x-1])

                            if(chessBoard.gameTiles[y][x].pieceonTile.tostring()=='p'):
                                ay=movex.enpassantb(chessBoard.gameTiles,y,x)
                                if not len(ay)==0:
                                    if ay[1]=='r':
                                        moves.append([y-1,x+1])
                                    else:
                                        moves.append([y-1,x-1])


                        if chessBoard.gameTiles[y][x].pieceonTile.alliance=='Black':
                            lx=movex.pinnedb(chessBoard.gameTiles,moves,y,x)
                        if chessBoard.gameTiles[y][x].pieceonTile.alliance=='White':
                            lx=movex.pinnedw(chessBoard.gameTiles,moves,y,x)
                        moves=lx

                        if turn%2==0:
                            if chessBoard.gameTiles[y][x].pieceonTile.alliance=='Black':
                                moves=[]
                        else:
                            if chessBoard.gameTiles[y][x].pieceonTile.alliance=='White':
                                moves=[]


                        imgx=pygame.transform.scale(pygame.image.load("./chessart/red_square.png",), (100,100))
                        for move in moves:
                            mx=[move[1]*100,move[0]*100]
                            if flipped:
                                mx=[(7-move[1])*100, (7-move[0])*100]
                            gamedisplay.blit(imgx,mx)









        if paused:
            pygame.draw.rect(gamedisplay, BACKGROUND_COLOR, [0, 0, 800, 800])
            text_p = font.render('PAUSED', True, TEXT_COLOR)
            rect_p = text_p.get_rect(center=(400, 400))
            gamedisplay.blit(text_p, rect_p)
        else:
            # Persistent Highlight Drawing
            if len(moves) > 0:
                img_highlight = pygame.transform.scale(pygame.image.load("./chessart/red_square.png"), (100, 100))
                for move in moves:
                    mx, my = move[1]*100, move[0]*100
                    if flipped: mx, my = (7-move[1])*100, (7-move[0])*100
                    gamedisplay.blit(img_highlight, (mx, my))
            if len(hint_move) > 0:
                img_hint = pygame.transform.scale(pygame.image.load("./chessart/red_square.png"), (100, 100))
                # You might want a different color image for hints, but reusing red_square or tinting it works.
                for h_sq in hint_move:
                    hx, hy = h_sq[1]*100, h_sq[0]*100
                    if flipped: hx, hy = (7-h_sq[1])*100, (7-h_sq[0])*100
                    # Draw a smaller rect or different indicator could be better, but this works
                    pygame.draw.rect(gamedisplay, HINT_COLOR, [hx, hy, 100, 100], 5)
            for img in allpieces:
                gamedisplay.blit(img[0],img[1])
        draw_timer(white_time, black_time)
        draw_undo()
        draw_reset()
        draw_save_load()
        draw_pause(paused)
        draw_move_log(move_log)
        draw_resign_btn()
        draw_flip_btn(flipped)
        draw_hint_btn()




        pygame.display.update()
        clock.tick(60)

if saki=='ai':
    start_countdown()

    moves=[]
    enpassant=[]
    promote=[]
    promotion=False
    turn=0

    array=[]
    quitgame=False

    flipped = False
    hint_move = []
    paused = False
    move_log = []
    history = []
    white_time = TIME_LIMIT
    black_time = TIME_LIMIT
    clock.tick(60)

    while not quitgame:
        if not paused:
            dt = clock.get_time() / 1000
            if turn % 2 == 0:
                white_time -= dt
                if white_time <= 0:
                    saki = 'end_timeout_w'
                    quitgame = True
            else:
                black_time -= dt
                if black_time <= 0:
                    saki = 'end_timeout_b'
                    quitgame = True

        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                quitgame= True
                pygame.quit()
                quit()

            if check_material(chessBoard.gameTiles):
                saki='end3'
                quitgame=True
                break

            if movex.checkw(chessBoard.gameTiles)[0]=='checked' and len(moves)==0 :
                array=movex.movesifcheckedw(chessBoard.gameTiles)
                if len(array)==0:
                    saki='end1'
                    quitgame=True
                    break

            if movex.checkb(chessBoard.gameTiles)[0]=='checked' and len(moves)==0 :
                array=movex.movesifcheckedb(chessBoard.gameTiles)
                if len(array)==0:
                    saki='end2'
                    quitgame=True
                    break


            if movex.checkb(chessBoard.gameTiles)[0]=='notchecked' and turn%2==1 and len(moves)==0 :
                check=False
                for x in range(8):
                    for y in range(8):
                        if chessBoard.gameTiles[y][x].pieceonTile.alliance=='Black' and turn%2==1:
                            moves1=chessBoard.gameTiles[y][x].pieceonTile.legalmoveb(chessBoard.gameTiles)
                            lx1=movex.pinnedb(chessBoard.gameTiles,moves1,y,x)
                            if len(lx1)==0:
                                continue
                            else:
                                check=True
                            if check==True:
                                break
                    if check==True:
                        break


                if check==False:
                    saki='end3'
                    quitgame=True
                    break

            if movex.checkw(chessBoard.gameTiles)[0]=='notchecked' and turn%2==0 and len(moves)==0 :
                check=False
                for x in range(8):
                    for y in range(8):
                        if chessBoard.gameTiles[y][x].pieceonTile.alliance=='White' and turn%2==0:
                            moves1=chessBoard.gameTiles[y][x].pieceonTile.legalmoveb(chessBoard.gameTiles)
                            lx1=movex.pinnedw(chessBoard.gameTiles,moves1,y,x)
                            if len(lx1)==0:
                                continue
                            else:
                                check=True
                            if check==True:
                                break
                    if check==True:
                        break


                if check==False:
                    saki='end3'
                    quitgame=True





            if not turn%2==0 and promotion==False and not paused:

                turn=turn+1
                sc=copy.deepcopy(chessBoard.gameTiles)
                y,x,fx,fy=ai.evaluate(sc, ai_depth)
                m=fy
                n=fx
                is_capture = False
                if chessBoard.gameTiles[n][m].pieceonTile.tostring() != '-':
                    is_capture = True
                if chessBoard.gameTiles[y][x].pieceonTile.tostring()=='K' or chessBoard.gameTiles[y][x].pieceonTile.tostring()=='R':
                    chessBoard.gameTiles[y][x].pieceonTile.moved=True

                if chessBoard.gameTiles[y][x].pieceonTile.tostring()=='K' and m==x+2:
                    chessBoard.gameTiles[y][x+1].pieceonTile=chessBoard.gameTiles[y][x+3].pieceonTile
                    s=updateposition(y,x+1)
                    chessBoard.gameTiles[y][x+1].pieceonTile.position=s
                    chessBoard.gameTiles[y][x+3].pieceonTile=nullpiece()
                if chessBoard.gameTiles[y][x].pieceonTile.tostring()=='K' and m==x-2:
                    chessBoard.gameTiles[y][x-1].pieceonTile=chessBoard.gameTiles[y][0].pieceonTile
                    s=updateposition(y,x-1)
                    chessBoard.gameTiles[y][x-1].pieceonTile.position=s
                    chessBoard.gameTiles[y][0].pieceonTile=nullpiece()


                if not len(enpassant)==0:
                    chessBoard.gameTiles[enpassant[0]][enpassant[1]].pieceonTile.enpassant=False
                    enpassant=[]
                if chessBoard.gameTiles[y][x].pieceonTile.tostring()=='P' and y+1==n and x+1==m and chessBoard.gameTiles[n][m].pieceonTile.tostring()=='-':
                    chessBoard.gameTiles[y][x+1].pieceonTile=nullpiece()
                    is_capture = True
                if chessBoard.gameTiles[y][x].pieceonTile.tostring()=='P' and y+1==n and x-1==m and chessBoard.gameTiles[n][m].pieceonTile.tostring()=='-':
                    chessBoard.gameTiles[y][x-1].pieceonTile=nullpiece()
                    is_capture = True

                if chessBoard.gameTiles[y][x].pieceonTile.tostring()=='P' and n==y+2:
                    chessBoard.gameTiles[y][x].pieceonTile.enpassant=True
                    enpassant=[n,m]

                if chessBoard.gameTiles[y][x].pieceonTile.tostring()=='P' and y+1==n and y==6:
                    promotion=True

                if is_capture:
                    capture_sound.play()
                else:
                    move_sound.play()

                if promotion==False:
                    last_move = [[y, x], [n, m]]
                    move_log.append(f"{get_notation(y, x)} to {get_notation(n, m)}")
                    chessBoard.gameTiles[n][m].pieceonTile=chessBoard.gameTiles[y][x].pieceonTile
                    chessBoard.gameTiles[y][x].pieceonTile=nullpiece()
                    s=updateposition(n,m)
                    chessBoard.gameTiles[n][m].pieceonTile.position=s
                    allTiles.clear()
                    allpieces.clear()
                    chessBoard.printboard()
                    drawchesspieces()
                    moves=[]

                if promotion==True:

                    if chessBoard.gameTiles[y][x].pieceonTile.tostring()=='P':
                        chessBoard.gameTiles[y][x].pieceonTile=nullpiece()
                        chessBoard.gameTiles[n][m].pieceonTile=queen('Black',updateposition(n,m))
                        move_log.append(f"{get_notation(y, x)} to {get_notation(n, m)}")
                        last_move = [[y, x], [n, m]]
                        allTiles.clear()
                        allpieces.clear()
                        chessBoard.printboard()
                        drawchesspieces(flipped)
                        moves=[]
                        promote=[]
                        promotion=False






            if event.type==pygame.MOUSEBUTTONDOWN:
                coord = pygame.mouse.get_pos()
                if coord[0]>=810 and coord[0]<=990 and coord[1]>=250 and coord[1]<=300:
                    paused = not paused
                    continue
                
                if paused:
                    continue

                if coord[0]>=810 and coord[0]<=990 and coord[1]>=80 and coord[1]<=120:
                    # Hint Button Clicked (AI Mode)
                    sc = copy.deepcopy(chessBoard.gameTiles)
                    # In AI mode, player is usually White (turn % 2 == 0)
                    is_white = (turn % 2 == 0)
                    # Use depth 2 for hints
                    hy, hx, hfx, hfy = ai.evaluate(sc, 2, is_white)
                    hint_move = [[hy, hx], [hfx, hfy]]
                    continue

                if coord[0]>=810 and coord[0]<=990 and coord[1]>=350 and coord[1]<=400:
                    if len(history) > 0:
                        state = history.pop()
                        chessBoard.gameTiles = copy.deepcopy(state[0])
                        turn = state[1]
                        white_time = state[2]
                        black_time = state[3]
                        enpassant = copy.deepcopy(state[4])
                        last_move = copy.deepcopy(state[5])
                        move_log = copy.deepcopy(state[6])
                        hint_move = []
                        moves = []
                        promote = []
                        promotion = False
                        allTiles.clear()
                        allpieces.clear()
                        chessBoard.printboard()
                        drawchesspieces()
                        continue

                if coord[0]>=810 and coord[0]<=990 and coord[1]>=450 and coord[1]<=500:
                    chessBoard = board()
                    chessBoard.createboard()
                    moves=[]
                    enpassant=[]
                    promote=[]
                    promotion=False
                    turn=0
                    flipped = False
                    hint_move = []
                    paused = False
                    move_log = []
                    history = []
                    white_time = TIME_LIMIT
                    black_time = TIME_LIMIT
                    last_move = []
                    allTiles.clear()
                    allpieces.clear()
                    chessBoard.printboard()
                    drawchesspieces()
                    continue

                if coord[0]>=810 and coord[0]<=990 and coord[1]>=550 and coord[1]<=600:
                    game_state = {
                        'tiles': chessBoard.gameTiles,
                        'turn': turn,
                        'white_time': white_time,
                        'black_time': black_time,
                        'enpassant': enpassant,
                        'last_move': last_move,
                        'history': history,
                        'move_log': move_log
                    }
                    with open('savegame.pkl', 'wb') as f:
                        pickle.dump(game_state, f)
                    continue

                if coord[0]>=810 and coord[0]<=990 and coord[1]>=650 and coord[1]<=700:
                    if os.path.exists('savegame.pkl'):
                        with open('savegame.pkl', 'rb') as f:
                            game_state = pickle.load(f)
                        chessBoard.gameTiles = game_state['tiles']
                        turn = game_state['turn']
                        white_time = game_state['white_time']
                        black_time = game_state['black_time']
                        enpassant = game_state['enpassant']
                        last_move = game_state['last_move']
                        history = game_state['history']
                        move_log = game_state.get('move_log', [])
                        hint_move = []
                        moves = []
                        promote = []
                        promotion = False
                        allTiles.clear()
                        allpieces.clear()
                        chessBoard.printboard()
                        drawchesspieces()
                    continue

                if coord[0]>=810 and coord[0]<=990 and coord[1]>=740 and coord[1]<=790:
                    saki = 'resigned_w'
                    quitgame = True
                    continue

                if movex.checkw(chessBoard.gameTiles)[0]=='checked' and len(moves)==0 :
                    array=movex.movesifcheckedw(chessBoard.gameTiles)
                    coord=pygame.mouse.get_pos()
                    if coord[0] >= 800: continue
                    m=math.floor(coord[0]/100)
                    n=math.floor(coord[1]/100)
                    imgx=pygame.transform.scale(pygame.image.load("./chessart/red_square.png",), (100,100))
                    mx=[]
                    ma=[]
                    for move in array:
                        if(move[1]==m and move[0]==n):
                            mx=[move[3]*100,move[2]*100]
                            ma=[move[2],move[3]]
                            moves.append(ma)
                            gamedisplay.blit(imgx,mx)
                            x=move[1]
                            y=move[0]
                    break

                if not len(promote)==0:
                    coord = pygame.mouse.get_pos()
                    if coord[0] >= 800: continue
                    m=math.floor(coord[0]/100)
                    n=math.floor(coord[1]/100)
                    if  chessBoard.gameTiles[promote[5][0]][promote[5][1]].pieceonTile.alliance=='White':
                        for i in range(len(promote)):
                            if i==4:
                                turn=turn-1
                                break
                            if promote[i][0]==n and promote[i][1]==m:
                                if i==0:
                                    chessBoard.gameTiles[promote[4][1]][promote[4][0]].pieceonTile=queen('White',updateposition(promote[4][1],promote[4][0]))
                                    chessBoard.gameTiles[promote[5][0]][promote[5][1]].pieceonTile=nullpiece()
                                    last_move = [[promote[5][0], promote[5][1]], [promote[4][1], promote[4][0]]]
                                    break
                                if i==1:
                                    chessBoard.gameTiles[promote[4][1]][promote[4][0]].pieceonTile=rook('White',updateposition(promote[4][1],promote[4][0]))
                                    chessBoard.gameTiles[promote[5][0]][promote[5][1]].pieceonTile=nullpiece()
                                    last_move = [[promote[5][0], promote[5][1]], [promote[4][1], promote[4][0]]]
                                    break
                                if i==2:
                                    chessBoard.gameTiles[promote[4][1]][promote[4][0]].pieceonTile=knight('White',updateposition(promote[4][1],promote[4][0]))
                                    chessBoard.gameTiles[promote[5][0]][promote[5][1]].pieceonTile=nullpiece()
                                    last_move = [[promote[5][0], promote[5][1]], [promote[4][1], promote[4][0]]]
                                    break
                                if i==3:
                                    chessBoard.gameTiles[promote[4][1]][promote[4][0]].pieceonTile=bishop('White',updateposition(promote[4][1],promote[4][0]))
                                    chessBoard.gameTiles[promote[5][0]][promote[5][1]].pieceonTile=nullpiece()
                                    last_move = [[promote[5][0], promote[5][1]], [promote[4][1], promote[4][0]]]
                                    break

                    allTiles.clear()
                    allpieces.clear()
                    chessBoard.printboard()
                    drawchesspieces()
                    promote=[]
                    promotion=False







                if not len(moves)==0:
                    coord = pygame.mouse.get_pos()
                    if coord[0] >= 800: continue
                    m=math.floor(coord[0]/100)
                    n=math.floor(coord[1]/100)

                    # Logic to allow re-selection (AI Mode)
                    if len(moves) > 0:
                        clicked_valid_move = False
                        for move in moves:
                            if move[0] == n and move[1] == m:
                                clicked_valid_move = True
                                break
                        if not clicked_valid_move:
                            moves = []

                    for move in moves:
                        if move[0]==n and move[1]==m:
                            hint_move = [] # Clear hint
                            history.append((copy.deepcopy(chessBoard.gameTiles), turn, white_time, black_time, copy.deepcopy(enpassant), copy.deepcopy(last_move), copy.deepcopy(move_log)))
                            turn=turn+1
                            is_capture = False
                            if chessBoard.gameTiles[n][m].pieceonTile.tostring() != '-':
                                is_capture = True
                            if chessBoard.gameTiles[y][x].pieceonTile.tostring()=='k' or chessBoard.gameTiles[y][x].pieceonTile.tostring()=='r':
                                chessBoard.gameTiles[y][x].pieceonTile.moved=True



                            if chessBoard.gameTiles[y][x].pieceonTile.tostring()=='k' and m==x+2:
                                chessBoard.gameTiles[y][x+1].pieceonTile=chessBoard.gameTiles[y][x+3].pieceonTile
                                s=updateposition(y,x+1)
                                chessBoard.gameTiles[y][x+1].pieceonTile.position=s
                                chessBoard.gameTiles[y][x+3].pieceonTile=nullpiece()
                            if chessBoard.gameTiles[y][x].pieceonTile.tostring()=='k' and m==x-2:
                                chessBoard.gameTiles[y][x-1].pieceonTile=chessBoard.gameTiles[y][0].pieceonTile
                                s=updateposition(y,x-1)
                                chessBoard.gameTiles[y][x-1].pieceonTile.position=s
                                chessBoard.gameTiles[y][0].pieceonTile=nullpiece()



                            if not len(enpassant)==0:
                                chessBoard.gameTiles[enpassant[0]][enpassant[1]].pieceonTile.enpassant=False
                                enpassant=[]

                            if chessBoard.gameTiles[y][x].pieceonTile.tostring()=='p' and y-1==n and x+1==m and chessBoard.gameTiles[n][m].pieceonTile.tostring()=='-':
                                chessBoard.gameTiles[y][x+1].pieceonTile=nullpiece()
                                is_capture = True
                            if chessBoard.gameTiles[y][x].pieceonTile.tostring()=='p' and y-1==n and x-1==m and chessBoard.gameTiles[n][m].pieceonTile.tostring()=='-':
                                chessBoard.gameTiles[y][x-1].pieceonTile=nullpiece()
                                is_capture = True

                            if chessBoard.gameTiles[y][x].pieceonTile.tostring()=='p' and n==y-2:
                                chessBoard.gameTiles[y][x].pieceonTile.enpassant=True
                                enpassant=[n,m]


                            if chessBoard.gameTiles[y][x].pieceonTile.tostring()=='p' and y-1==n and y==1:
                                promotion=True

                            if is_capture:
                                capture_sound.play()
                            else:
                                move_sound.play()


                            if promotion==False:
                                last_move = [[y, x], [n, m]]
                                move_log.append(f"{get_notation(y, x)} to {get_notation(n, m)}")
                                chessBoard.gameTiles[n][m].pieceonTile=chessBoard.gameTiles[y][x].pieceonTile
                                chessBoard.gameTiles[y][x].pieceonTile=nullpiece()
                                s=updateposition(n,m)
                                chessBoard.gameTiles[n][m].pieceonTile.position=s
                    if promotion==False:
                        allTiles.clear()
                        allpieces.clear()
                        chessBoard.printboard()
                        drawchesspieces(flipped)
                        moves=[]

                    if promotion==True:




                        if  chessBoard.gameTiles[y][x].pieceonTile.tostring()=='p' and x==7 and y==1:
                            pygame.draw.rect(gamedisplay,(0,0,0),[x*100-100,(y*100)+100,200,200])
                            imgx=pygame.transform.scale(pygame.image.load("./chessart/WQ.png",), (100,100))
                            imgx1=pygame.transform.scale(pygame.image.load("./chessart/WR.png",), (100,100))
                            imgx2=pygame.transform.scale(pygame.image.load("./chessart/WN.png",), (100,100))
                            imgx3=pygame.transform.scale(pygame.image.load("./chessart/WB.png",), (100,100))
                            gamedisplay.blit(imgx,[x*100-100,(y*100)+200])
                            gamedisplay.blit(imgx1,[(x*100),(y*100)+200])
                            gamedisplay.blit(imgx2,[x*100-100,(y*100)+100])
                            gamedisplay.blit(imgx3,[(x*100),(y*100)+100])
                            promote=[[y+2,x-1],[y+2,x],[y+1,x],[y+1,x],[m,n],[y,x]]
                            move_log.append(f"{get_notation(y, x)} to {get_notation(n, m)}")

                        elif chessBoard.gameTiles[y][x].pieceonTile.tostring()=='p':
                            pygame.draw.rect(gamedisplay,(0,0,0),[x*100,(y*100)+100,200,200])
                            imgx=pygame.transform.scale(pygame.image.load("./chessart/WQ.png",), (100,100))
                            imgx1=pygame.transform.scale(pygame.image.load("./chessart/WR.png",), (100,100))
                            imgx2=pygame.transform.scale(pygame.image.load("./chessart/WN.png",), (100,100))
                            imgx3=pygame.transform.scale(pygame.image.load("./chessart/WB.png",), (100,100))
                            gamedisplay.blit(imgx,[x*100,(y*100)+200])
                            gamedisplay.blit(imgx1,[(x*100)+100,(y*100)+200])
                            gamedisplay.blit(imgx2,[x*100,(y*100)+100])
                            gamedisplay.blit(imgx3,[(x*100)+100,(y*100)+100])
                            promote=[[y+2,x],[y+2,x+1],[y+1,x],[y+1,x+1],[m,n],[y,x]]
                            move_log.append(f"{get_notation(y, x)} to {get_notation(n, m)}")










                else:
                    drawchesspieces()
                    coords = pygame.mouse.get_pos()
                    if coords[0] < 800:
                        x=math.floor(coords[0]/100)
                        y=math.floor(coords[1]/100)
                        mx=[]
                        if(chessBoard.gameTiles[y][x].pieceonTile.alliance=='White'):
                            moves=chessBoard.gameTiles[y][x].pieceonTile.legalmoveb(chessBoard.gameTiles)
                            if(chessBoard.gameTiles[y][x].pieceonTile.tostring()=='k'):
                                ax=movex.castlingw(chessBoard.gameTiles)
                                if not len(ax)==0:
                                    for l in ax:
                                        if l=='ks':
                                            moves.append([7,6])
                                        if l=='qs':
                                            moves.append([7,2])
                            if(chessBoard.gameTiles[y][x].pieceonTile.tostring()=='p'):
                                ay=movex.enpassantb(chessBoard.gameTiles,y,x)
                                if not len(ay)==0:
                                    if ay[1]=='r':
                                        moves.append([y-1,x+1])
                                    else:
                                        moves.append([y-1,x-1])


                        if chessBoard.gameTiles[y][x].pieceonTile.alliance=='White':
                            lx=movex.pinnedw(chessBoard.gameTiles,moves,y,x)
                        moves=lx

                        if not turn%2==0:
                            moves=[]

                        if chessBoard.gameTiles[y][x].pieceonTile.alliance=='Black':
                            moves=[]

                        if chessBoard.gameTiles[y][x].pieceonTile.tostring()=='-':
                            moves=[]


                        imgx=pygame.transform.scale(pygame.image.load("./chessart/red_square.png",), (100,100))
                        for move in moves:
                            mx=[move[1]*100,move[0]*100]
                            gamedisplay.blit(imgx,mx)









        if paused:
            pygame.draw.rect(gamedisplay, BACKGROUND_COLOR, [0, 0, 800, 800])
            text_p = font.render('PAUSED', True, TEXT_COLOR)
            rect_p = text_p.get_rect(center=(400, 400))
            gamedisplay.blit(text_p, rect_p)
        else:
            # Persistent Highlight Drawing (AI Mode)
            if len(moves) > 0:
                img_highlight = pygame.transform.scale(pygame.image.load("./chessart/red_square.png"), (100, 100))
                for move in moves:
                    gamedisplay.blit(img_highlight, (move[1]*100, move[0]*100))
            for img in allpieces:
                gamedisplay.blit(img[0],img[1])
            if len(hint_move) > 0:
                for h_sq in hint_move:
                    hx, hy = h_sq[1]*100, h_sq[0]*100
                    if flipped: hx, hy = (7-h_sq[1])*100, (7-h_sq[0])*100
                    pygame.draw.rect(gamedisplay, HINT_COLOR, [hx, hy, 100, 100], 5)
        draw_timer(white_time, black_time)
        draw_undo()
        draw_reset()
        draw_save_load()
        draw_pause(paused)
        draw_move_log(move_log)
        draw_resign_btn()
        draw_hint_btn()




        pygame.display.update()
        clock.tick(60)


if saki=='end1':
    quitgame=False
    while not quitgame:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quitgame= True
                pygame.quit()
                quit()
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                coord = pygame.mouse.get_pos()
                if 425 <= coord[0] <= 575 and 410 <= coord[1] <= 460:
                    os.execl(sys.executable, sys.executable, *sys.argv)

            gamedisplay.fill(BACKGROUND_COLOR)
            for tile in allTiles:
                pygame.draw.rect(gamedisplay, tile[0], tile[1])
            for img in allpieces:
                gamedisplay.blit(img[0],img[1])
            draw_timer(white_time, black_time)
            draw_move_log(move_log)
            
            draw_popup(text3)

            pygame.display.update()
            clock.tick(60)

if saki=='resigned_w':
    quitgame=False
    while not quitgame:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quitgame= True
                pygame.quit()
                quit()
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                coord = pygame.mouse.get_pos()
                if 425 <= coord[0] <= 575 and 410 <= coord[1] <= 460:
                    os.execl(sys.executable, sys.executable, *sys.argv)

            gamedisplay.fill(BACKGROUND_COLOR)
            for tile in allTiles:
                pygame.draw.rect(gamedisplay, tile[0], tile[1])
            for img in allpieces:
                gamedisplay.blit(img[0],img[1])
            draw_timer(white_time, black_time)
            draw_move_log(move_log)
            draw_popup(text_resign_w)
            pygame.display.update()
            clock.tick(60)

if saki=='resigned_b':
    quitgame=False
    while not quitgame:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quitgame= True
                pygame.quit()
                quit()
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                coord = pygame.mouse.get_pos()
                if 425 <= coord[0] <= 575 and 410 <= coord[1] <= 460:
                    os.execl(sys.executable, sys.executable, *sys.argv)

            gamedisplay.fill(BACKGROUND_COLOR)
            for tile in allTiles:
                pygame.draw.rect(gamedisplay, tile[0], tile[1])
            for img in allpieces:
                gamedisplay.blit(img[0],img[1])
            draw_timer(white_time, black_time)
            draw_move_log(move_log)
            draw_popup(text_resign_b)
            pygame.display.update()
            clock.tick(60)

if saki=='end_timeout_w':
    quitgame=False
    while not quitgame:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quitgame= True
                pygame.quit()
                quit()
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                coord = pygame.mouse.get_pos()
                if 425 <= coord[0] <= 575 and 410 <= coord[1] <= 460:
                    os.execl(sys.executable, sys.executable, *sys.argv)

            gamedisplay.fill(BACKGROUND_COLOR)
            for tile in allTiles:
                pygame.draw.rect(gamedisplay, tile[0], tile[1])
            for img in allpieces:
                gamedisplay.blit(img[0],img[1])
            draw_timer(white_time, black_time)
            draw_move_log(move_log)
            draw_popup(text_timeout_w)
            pygame.display.update()
            clock.tick(60)

if saki=='end_timeout_b':
    quitgame=False
    while not quitgame:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quitgame= True
                pygame.quit()
                quit()
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                coord = pygame.mouse.get_pos()
                if 425 <= coord[0] <= 575 and 410 <= coord[1] <= 460:
                    os.execl(sys.executable, sys.executable, *sys.argv)

            gamedisplay.fill(BACKGROUND_COLOR)
            for tile in allTiles:
                pygame.draw.rect(gamedisplay, tile[0], tile[1])
            for img in allpieces:
                gamedisplay.blit(img[0],img[1])
            draw_timer(white_time, black_time)
            draw_move_log(move_log)
            draw_popup(text_timeout_b)
            pygame.display.update()
            clock.tick(60)

if saki=='end2':
    quitgame=False
    while not quitgame:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quitgame= True
                pygame.quit()
                quit()
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                coord = pygame.mouse.get_pos()
                if 425 <= coord[0] <= 575 and 410 <= coord[1] <= 460:
                    os.execl(sys.executable, sys.executable, *sys.argv)

            gamedisplay.fill(BACKGROUND_COLOR)
            for tile in allTiles:
                pygame.draw.rect(gamedisplay, tile[0], tile[1])
            for img in allpieces:
                gamedisplay.blit(img[0],img[1])
            draw_timer(white_time, black_time)
            draw_move_log(move_log)
            draw_popup(text4)

            pygame.display.update()
            clock.tick(60)

if saki=='end3':
    quitgame=False
    while not quitgame:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quitgame= True
                pygame.quit()
                quit()
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                coord = pygame.mouse.get_pos()
                if 425 <= coord[0] <= 575 and 410 <= coord[1] <= 460:
                    os.execl(sys.executable, sys.executable, *sys.argv)

            gamedisplay.fill(BACKGROUND_COLOR)
            for tile in allTiles:
                pygame.draw.rect(gamedisplay, tile[0], tile[1])
            for img in allpieces:
                gamedisplay.blit(img[0],img[1])
            draw_timer(white_time, black_time)
            draw_move_log(move_log)
            draw_popup(text5)

            pygame.display.update()
            clock.tick(60)

if saki=='tutorial':
    start_countdown()
    moves=[]
    enpassant=[]
    promote=[]
    promotion=False
    # turn is set in setup_puzzle
    
    array=[]
    quitgame=False
    flipped = False
    hint_move = []
    paused = False
    move_log = []
    history = []
    
    # No timer needed for tutorial usually, but we keep variables to avoid errors
    white_time = 9999
    black_time = 9999
    
    tutorial_status = "" # "success" or "fail"
    selected_piece_pos = None

    while not quitgame:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quitgame= True
                pygame.quit()
                quit()
            
            # Check win/loss conditions
            if movex.checkb(chessBoard.gameTiles)[0]=='checked':
                array=movex.movesifcheckedb(chessBoard.gameTiles)
                if len(array)==0:
                    tutorial_status = "success"
            
            if tutorial_status == "" and moves_made_count >= puzzle_moves_limit and turn % 2 == 0:
                 # If we used up our moves and it's back to our turn (or we just moved), and no mate
                 # Actually, checkmate is checked above. If we are here, we failed.
                 tutorial_status = "fail"

            if event.type==pygame.MOUSEBUTTONDOWN:
                coord = pygame.mouse.get_pos()
                
                # Handle Restart/Menu if status is set
                if tutorial_status != "":
                    if 425 <= coord[0] <= 575 and 410 <= coord[1] <= 460:
                         os.execl(sys.executable, sys.executable, *sys.argv)
                    continue

                # Hint Button
                if coord[0]>=810 and coord[0]<=990 and coord[1]>=80 and coord[1]<=120:
                    sc = copy.deepcopy(chessBoard.gameTiles)
                    is_white = (turn % 2 == 0)
                    hy, hx, hfx, hfy = ai.evaluate(sc, 3, is_white)
                    hint_move = [[hy, hx], [hfx, hfy]]
                    continue

                # Board Interaction (Only allow White moves)
                if turn % 2 == 0:
                    if coord[0] < 800:
                        x=math.floor(coord[0]/100)
                        y=math.floor(coord[1]/100)
                        
                        # Selection Logic
                        if len(moves) > 0:
                            # Check if clicked on a valid move
                            clicked_move = None
                            for move in moves:
                                if move[0]==y and move[1]==x: # Note: move is [row, col] -> [y, x]
                                    clicked_move = move
                                    break
                            
                            if clicked_move:
                                # Execute Move
                                n, m = y, x
                                y_start, x_start = selected_piece_pos
                                
                                chessBoard.gameTiles[n][m].pieceonTile = chessBoard.gameTiles[y_start][x_start].pieceonTile
                                chessBoard.gameTiles[y_start][x_start].pieceonTile = nullpiece()
                                chessBoard.gameTiles[n][m].pieceonTile.position = updateposition(n, m)
                                chessBoard.gameTiles[n][m].pieceonTile.moved = True
                                
                                move_sound.play()
                                moves = []
                                hint_move = []
                                turn += 1
                                moves_made_count += 1
                                allTiles.clear()
                                allpieces.clear()
                                chessBoard.printboard()
                                drawchesspieces()
                                continue
                            else:
                                moves = [] # Deselect
                        
                        # Select Piece
                        if chessBoard.gameTiles[y][x].pieceonTile.alliance == 'White':
                            moves = chessBoard.gameTiles[y][x].pieceonTile.legalmoveb(chessBoard.gameTiles)
                            # Filter moves that leave king in check
                            moves = movex.pinnedw(chessBoard.gameTiles, moves, y, x)
                            selected_piece_pos = [y, x]

            # AI Turn (Black)
            if turn % 2 == 1 and tutorial_status == "":
                # Check if Black has any legal moves (Stalemate check)
                has_moves = False
                for x in range(8):
                    for y in range(8):
                        if chessBoard.gameTiles[y][x].pieceonTile.alliance == 'Black':
                            moves1 = chessBoard.gameTiles[y][x].pieceonTile.legalmoveb(chessBoard.gameTiles)
                            lx1 = movex.pinnedb(chessBoard.gameTiles, moves1, y, x)
                            if len(lx1) > 0:
                                has_moves = True
                                break
                    if has_moves: break
                
                if not has_moves:
                    tutorial_status = "fail"
                    continue

                # Simple AI move
                sc = copy.deepcopy(chessBoard.gameTiles)
                # AI plays Black, depth 2 is enough for puzzles
                y_ai, x_ai, fy_ai, fx_ai = ai.evaluate(sc, 2, False)
                
                if y_ai is None:
                    continue
                
                chessBoard.gameTiles[fx_ai][fy_ai].pieceonTile = chessBoard.gameTiles[y_ai][x_ai].pieceonTile
                chessBoard.gameTiles[y_ai][x_ai].pieceonTile = nullpiece()
                chessBoard.gameTiles[fx_ai][fy_ai].pieceonTile.position = updateposition(fx_ai, fy_ai)
                
                move_sound.play()
                turn += 1
                allTiles.clear()
                allpieces.clear()
                chessBoard.printboard()
                drawchesspieces()

        # Drawing
        gamedisplay.fill(BACKGROUND_COLOR)
        
        # Highlight selected
        if len(moves) > 0:
            img_highlight = pygame.transform.scale(pygame.image.load("./chessart/red_square.png"), (100, 100))
            for move in moves:
                gamedisplay.blit(img_highlight, (move[1]*100, move[0]*100))
        
        # Highlight hint
        if len(hint_move) > 0:
            for h_sq in hint_move:
                hx, hy = h_sq[1]*100, h_sq[0]*100
                pygame.draw.rect(gamedisplay, HINT_COLOR, [hx, hy, 100, 100], 5)

        for img in allpieces:
            gamedisplay.blit(img[0],img[1])
        
        draw_hint_btn()
        
        # Draw Instructions
        instr = f"Puzzle: Mate in {puzzle_moves_limit}"
        text_instr = font_small.render(instr, True, TEXT_COLOR)
        gamedisplay.blit(text_instr, (810, 50))
        
        # Draw Status Popup
        if tutorial_status == "success":
            draw_popup(text_success)
        elif tutorial_status == "fail":
            draw_popup(text_fail)

        pygame.display.update()
        clock.tick(60)

if saki=='spectator':
    start_countdown()
    moves=[]
    enpassant=[]
    promote=[]
    promotion=False
    turn=0
    
    array=[]
    quitgame=False
    flipped = False
    hint_move = []
    paused = False
    move_log = []
    history = []
    white_time = TIME_LIMIT
    black_time = TIME_LIMIT
    clock.tick(60)

    while not quitgame:
        if not paused:
            dt = clock.get_time() / 1000
            if turn % 2 == 0:
                white_time -= dt
                if white_time <= 0: saki = 'end_timeout_w'; quitgame = True
            else:
                black_time -= dt
                if black_time <= 0: saki = 'end_timeout_b'; quitgame = True

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quitgame= True
                pygame.quit()
                quit()
            
            # Check Game Over Conditions
            if check_material(chessBoard.gameTiles): saki='end3'; quitgame=True; break
            if movex.checkw(chessBoard.gameTiles)[0]=='checked':
                if len(movex.movesifcheckedw(chessBoard.gameTiles))==0: saki='end1'; quitgame=True; break
            if movex.checkb(chessBoard.gameTiles)[0]=='checked':
                if len(movex.movesifcheckedb(chessBoard.gameTiles))==0: saki='end2'; quitgame=True; break
            
            # Check Stalemate
            if movex.checkb(chessBoard.gameTiles)[0]=='notchecked' and turn%2==1:
                check=False
                for x in range(8):
                    for y in range(8):
                        if chessBoard.gameTiles[y][x].pieceonTile.alliance=='Black':
                            if len(movex.pinnedb(chessBoard.gameTiles, chessBoard.gameTiles[y][x].pieceonTile.legalmoveb(chessBoard.gameTiles), y, x)) > 0:
                                check=True; break
                    if check: break
                if not check: saki='end3'; quitgame=True; break

            if movex.checkw(chessBoard.gameTiles)[0]=='notchecked' and turn%2==0:
                check=False
                for x in range(8):
                    for y in range(8):
                        if chessBoard.gameTiles[y][x].pieceonTile.alliance=='White':
                            if len(movex.pinnedw(chessBoard.gameTiles, chessBoard.gameTiles[y][x].pieceonTile.legalmoveb(chessBoard.gameTiles), y, x)) > 0:
                                check=True; break
                    if check: break
                if not check: saki='end3'; quitgame=True; break

            if event.type==pygame.MOUSEBUTTONDOWN:
                coord = pygame.mouse.get_pos()
                # Pause
                if coord[0]>=810 and coord[0]<=990 and coord[1]>=250 and coord[1]<=300:
                    paused = not paused
                # Reset
                if coord[0]>=810 and coord[0]<=990 and coord[1]>=450 and coord[1]<=500:
                    chessBoard = board(); chessBoard.createboard(); moves=[]; enpassant=[]; promote=[]; promotion=False; turn=0; flipped=False; hint_move=[]; paused=False; move_log=[]; history=[]; white_time=TIME_LIMIT; black_time=TIME_LIMIT; last_move=[]; allTiles.clear(); allpieces.clear(); chessBoard.printboard(); drawchesspieces(flipped)
                # Menu/Quit (Resign button acts as quit to menu here)
                if coord[0]>=810 and coord[0]<=990 and coord[1]>=740 and coord[1]<=790:
                    quitgame=True; pygame.quit(); quit()

        if not paused and not quitgame:
            # AI Logic
            sc = copy.deepcopy(chessBoard.gameTiles)
            is_white_turn = (turn % 2 == 0)
            
            # Calculate Move
            y, x, fx, fy = ai.evaluate(sc, ai_depth, is_white_turn)
            
            # Execute Move
            m, n = fy, fx
            is_capture = False
            if chessBoard.gameTiles[n][m].pieceonTile.tostring() != '-': is_capture = True
            
            # Handle Castling Flag
            if chessBoard.gameTiles[y][x].pieceonTile.tostring() in ['K', 'R', 'k', 'r']:
                chessBoard.gameTiles[y][x].pieceonTile.moved = True

            # Handle Castling Move
            piece_char = chessBoard.gameTiles[y][x].pieceonTile.tostring()
            if piece_char in ['K', 'k']:
                if m == x + 2: # Kingside
                    chessBoard.gameTiles[y][x+1].pieceonTile = chessBoard.gameTiles[y][x+3].pieceonTile
                    chessBoard.gameTiles[y][x+1].pieceonTile.position = updateposition(y, x+1)
                    chessBoard.gameTiles[y][x+3].pieceonTile = nullpiece()
                elif m == x - 2: # Queenside
                    chessBoard.gameTiles[y][x-1].pieceonTile = chessBoard.gameTiles[y][0].pieceonTile
                    chessBoard.gameTiles[y][x-1].pieceonTile.position = updateposition(y, x-1)
                    chessBoard.gameTiles[y][0].pieceonTile = nullpiece()

            # Handle En Passant Capture
            if piece_char in ['P', 'p']:
                if y+1==n and x+1==m and chessBoard.gameTiles[n][m].pieceonTile.tostring()=='-':
                    chessBoard.gameTiles[y][x+1].pieceonTile=nullpiece(); is_capture=True
                if y+1==n and x-1==m and chessBoard.gameTiles[n][m].pieceonTile.tostring()=='-':
                    chessBoard.gameTiles[y][x-1].pieceonTile=nullpiece(); is_capture=True
                if y-1==n and x+1==m and chessBoard.gameTiles[n][m].pieceonTile.tostring()=='-':
                    chessBoard.gameTiles[y][x+1].pieceonTile=nullpiece(); is_capture=True
                if y-1==n and x-1==m and chessBoard.gameTiles[n][m].pieceonTile.tostring()=='-':
                    chessBoard.gameTiles[y][x-1].pieceonTile=nullpiece(); is_capture=True

            # Set En Passant Flag
            if not len(enpassant)==0:
                chessBoard.gameTiles[enpassant[0]][enpassant[1]].pieceonTile.enpassant=False
                enpassant=[]
            if piece_char == 'p' and n == y - 2:
                chessBoard.gameTiles[y][x].pieceonTile.enpassant = True; enpassant = [n, m]
            if piece_char == 'P' and n == y + 2:
                chessBoard.gameTiles[y][x].pieceonTile.enpassant = True; enpassant = [n, m]

            # Move Piece
            chessBoard.gameTiles[n][m].pieceonTile = chessBoard.gameTiles[y][x].pieceonTile
            chessBoard.gameTiles[y][x].pieceonTile = nullpiece()
            chessBoard.gameTiles[n][m].pieceonTile.position = updateposition(n, m)

            # Handle Promotion (Auto-Queen)
            if piece_char == 'P' and n == 7:
                chessBoard.gameTiles[n][m].pieceonTile = queen('Black', updateposition(n, m))
            if piece_char == 'p' and n == 0:
                chessBoard.gameTiles[n][m].pieceonTile = queen('White', updateposition(n, m))

            # Play Sound
            if is_capture: capture_sound.play()
            else: move_sound.play()

            # Update State
            last_move = [[y, x], [n, m]]
            move_log.append(f"{get_notation(y, x)} to {get_notation(n, m)}")
            turn += 1
            
            # Redraw
            allTiles.clear()
            allpieces.clear()
            chessBoard.printboard()
            drawchesspieces(flipped)
            
            # Small delay to make it watchable
            pygame.display.update()
            pygame.time.wait(200) 

        # Draw UI
        gamedisplay.fill(BACKGROUND_COLOR)
        for img in allpieces: gamedisplay.blit(img[0],img[1])
        draw_timer(white_time, black_time)
        draw_reset()
        draw_pause(paused)
        draw_move_log(move_log)
        
        pygame.display.update()
        clock.tick(60)
