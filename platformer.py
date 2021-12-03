import pygame
from pygame.locals import *
from pygame import mixer
import pickle
from os import path

pygame.mixer.pre_init(44100, -16, 2, 512)
mixer.init()
pygame.init()

clock = pygame.time.Clock()
fps = 60

screen_width = 1000
screen_height = 1000

screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Osrelia's Grand Adventure")

#font
font = pygame.font.SysFont('Bauhaus 93', 70)
font_score = pygame.font.SysFont('Bauhaus 93', 30)

#variables
tile_size = 50
game_over = 0
main_menu = True
level = 1
max_levels = 7
score = 0
current_score = 0

#colors
white = (255, 255, 255)
blue = (0, 0, 255)


#load images
sun_img = pygame.image.load('img/sun.png')
bg_img = pygame.image.load('img/sky.png')
bg2_img = pygame.image.load('img/sky2.png')
bg3_img = pygame.image.load('img/sky3.png')
bg4_img = pygame.image.load('img/sky4.png')
bg5_img = pygame.image.load('img/sky5.png')
bg6_img = pygame.image.load('img/sky6.png')
bg7_img = pygame.image.load('img/sky7.png')
restart_img = pygame.image.load('img/restart_btn.png')
start_img = pygame.image.load('img/start_btn.png')
exit_img = pygame.image.load('img/exit_btn.png')
gray_img = pygame.image.load('img/graybg.png')

#load sounds
pygame.mixer.music.load('img/music.wav')
pygame.mixer.music.play(-1, 0.0, 5000)
coin_fx = pygame.mixer.Sound('img/coin.wav')
coin_fx.set_volume(0.5)
jump_fx = pygame.mixer.Sound('img/jump.wav')
jump_fx.set_volume(0.5)
gameover_fx = pygame.mixer.Sound('img/game_over.wav')
gameover_fx.set_volume(0.5)


def draw_text(text, font, text_col, x, y):
    img = font.render(text, True, text_col)
    screen.blit(img, (x, y))


#reset and change level
def reset_level(level):
    player.reset(100, screen_height - 130)
    blob_group.empty()
    platform_group.empty()
    coin_group.empty()
    lava_group.empty()
    exit_group.empty()

    if path.exists(f'level{level}_data'):
        pickle_in = open(f'level{level}_data', 'rb')
        world_data = pickle.load(pickle_in)
    world = World(world_data)
    
    score_coin = Coin(tile_size // 2, tile_size // 2)
    coin_group.add(score_coin)
    return world


class Button():
    def __init__(self, x, y, image):
        self.image = image
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.clicked = False

    def draw(self):
        action = False

        #mouse position check
        pos = pygame.mouse.get_pos()

        #button click
        if self.rect.collidepoint(pos):
            if pygame.mouse.get_pressed()[0] == 1 and self.clicked == False:
                action = True
                self.clicked = True

        if pygame.mouse.get_pressed()[0] == 0:
            self.clicked = False


        screen.blit(self.image, self.rect)

        return action

class Player():
    def __init__(self, x, y):
        self.reset(x, y)

    def update(self, game_over):
        dx = 0
        dy = 0
        walk_cooldown = 5
        col_thresh = 20


        if game_over == 0:
            #keypresses and movement
            key = pygame.key.get_pressed()
            if key[pygame.K_SPACE] and self.jumped == False and self.in_air == False:
                jump_fx.play()
                self.vel_y = -15.5
                self.jumped = True
            if key[pygame.K_SPACE] == False:
                self.jumped = False

            if key[pygame.K_LEFT]:
                dx -= 5
                self.counter += 1
                self.direction = -1
            if key[pygame.K_RIGHT]:
                dx += 5
                self.counter += 1
                self.direction = 1
            if key[pygame.K_LEFT] == False and key[pygame.K_RIGHT] == False:
                self.counter = 0
                self.index = 0
                if self.direction == 1:
                    self.image = self.images_right[self.index]
                if self.direction == -1:
                    self.image = self.images_left[self.index]


            #movement animation
            if self.counter > walk_cooldown:
                self.counter = 0
                self.index += 1
                if self.index >= len(self.images_right):
                    self.index = 0
                if self.direction == 1:
                    self.image = self.images_right[self.index]
                if self.direction == -1:
                    self.image = self.images_left[self.index]

            #gravity
            self.vel_y += 1
            if self.vel_y > 10:
                self.vel_y = 10
            dy += self.vel_y


            #collision
            self.in_air = True
            for tile in world.tile_list:
                #x axis check
                if tile[1].colliderect(self.rect.x + dx, self.rect.y, self.width, self.height):
                    dx = 0

                #y axis check
                if tile[1].colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
                    #jump check
                    if self.vel_y < 0:
                        dy = tile[1].bottom - self.rect.top
                        self.vel_y = 0
                    #fall check
                    elif self.vel_y >= 0:
                        dy = tile[1].top - self.rect.bottom   
                        self.vel_y = 0
                        self.in_air = False


            #enemy collision
            if pygame.sprite.spritecollide(self, blob_group, False):
                game_over = -1
                gameover_fx.play()

            #lava collision
            if pygame.sprite.spritecollide(self, lava_group, False):
                game_over = -1
                gameover_fx.play()

            #exit collision
            if pygame.sprite.spritecollide(self, exit_group, False):
                game_over = 1

            #platform collision
            for platform in platform_group:
                #horizontal movement
                if platform.rect.colliderect(self.rect.x + dx, self.rect.y, self.width, self.height):
                    dx = 0
                #vertical movement
                if platform.rect.colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
                    #if below platform
                    if abs((self.rect.top + dy) - platform.rect.bottom) < col_thresh:
                        self.vel_y = 0
                        dy = platform.rect.bottom - self.rect.top
                    #if above platform
                    elif abs((self.rect.bottom + dy) - platform.rect.top) < col_thresh:
                        self.rect.bottom = platform.rect.top - 1
                        self.in_air = False
                        dy = 0
                    #move with platform
                    if platform.move_x != 0:
                        self.rect.x += platform.move_direction


            #update position
            self.rect.x += dx
            self.rect.y += dy

        elif game_over == -1:
            self.image = self.dead_image
            draw_text('GAME OVER!', font, blue, (screen_width // 2 ) - 140, (screen_height // 2 ))
            if self.rect.y > 200:
                self.rect.y -= 5


        #draw player
        screen.blit(self.image, self.rect)
        #pygame.draw.rect(screen, (255, 255, 255), self.rect, 2)

        return game_over

    #player data after resetting position
    def reset(self, x, y):
        self.images_right = []
        self.images_left = []
        self.index = 0
        self.counter = 0
        for num in range(1, 5):
            img_right = pygame.image.load(f'img/guy{num}.png')
            img_right = pygame.transform.scale(img_right, (40, 80))
            img_left = pygame.transform.flip(img_right, True, False)
            self.images_right.append(img_right)
            self.images_left.append(img_left)
        self.dead_image = pygame.image.load('img/ghost.png')
        self.image = self.images_right[self.index]
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.width = self.image.get_width()
        self.height = self.image.get_height()
        self.vel_y = 0
        self.jumped = False
        self.direction = 0
        self.in_air = True

class World():
    def __init__(self, data):
        self.tile_list = []

        #load tile images
        dirt_img = pygame.image.load('img/dirt.png')
        grass_img = pygame.image.load('img/grass.png')

        #create tileset
        row_count = 0
        for row in data:
            col_count = 0
            for tile in row:
                if tile == 1:
                    img = pygame.transform.scale(dirt_img, (tile_size, tile_size))
                    img_rect = img.get_rect()
                    img_rect.x = col_count * tile_size
                    img_rect.y = row_count * tile_size
                    tile = (img, img_rect)
                    self.tile_list.append(tile)
                if tile == 2:
                    img = pygame.transform.scale(grass_img, (tile_size, tile_size))
                    img_rect = img.get_rect()
                    img_rect.x = col_count * tile_size
                    img_rect.y = row_count * tile_size
                    tile = (img, img_rect)
                    self.tile_list.append(tile)
                if tile == 3:
                    blob = Enemy(col_count * tile_size, row_count * tile_size + 15)
                    blob_group.add(blob)
                if tile == 4:
                    platform = Platform(col_count * tile_size, row_count * tile_size, 1, 0)
                    platform_group.add(platform)
                if tile == 5:
                    platform = Platform(col_count * tile_size, row_count * tile_size, 0, 1)
                    platform_group.add(platform)
                if tile == 6:
                    lava = Lava(col_count * tile_size, row_count * tile_size + (tile_size // 2))
                    lava_group.add(lava)
                if tile == 7:
                    coin = Coin(col_count * tile_size + (tile_size // 2), row_count * tile_size + (tile_size // 2))
                    coin_group.add(coin)
                if tile == 8:
                    exit = Exit(col_count * tile_size, row_count * tile_size - (tile_size // 2))
                    exit_group.add(exit)
                if tile == 9:
                    platform = Platform(col_count * tile_size, row_count * tile_size, 1, 1)
                    platform_group.add(platform)
                col_count += 1
            row_count += 1

    def draw(self):
        for tile in self.tile_list:
            screen.blit(tile[0], tile[1])
            #pygame.draw.rect(screen, (255, 255, 255), tile[1], 2)


class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.image.load('img/blob.png')
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.move_direction = 1
        self.move_counter = 0

    #enemy movement
    def update(self):
        self.rect.x += self.move_direction 
         
        self.move_counter += 1
        if abs(self.move_counter) > 50:
            self.move_direction *= -1
            self.move_counter *= -1


class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, move_x, move_y):
        pygame.sprite.Sprite.__init__(self)
        img = pygame.image.load('img/platform.png')
        self.image = pygame.transform.scale(img, (tile_size, tile_size // 2))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.move_direction = 1
        self.move_counter = 0
        self.move_x = move_x
        self.move_y = move_y

    #platform movement
    def update(self):
        self.rect.x += self.move_direction * self.move_x
        self.rect.y += self.move_direction * self.move_y
        self.move_counter += 1
        if abs(self.move_counter) > 50:
            self.move_direction *= -1
            self.move_counter *= -1 



            
class Lava(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        img = pygame.image.load('img/lava.png')
        self.image = pygame.transform.scale(img, (tile_size, tile_size // 2 ))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

class Coin(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        img = pygame.image.load('img/heart.png')
        self.image = pygame.transform.scale(img, (tile_size // 2, tile_size // 2 ))
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        
        

class Exit(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        img = pygame.image.load('img/exit.png')
        self.image = pygame.transform.scale(img, (tile_size, int(tile_size * 1.5 )))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
       




#player starting position
player = Player(100, screen_height - 130)

#sprites
blob_group = pygame.sprite.Group()
platform_group = pygame.sprite.Group()
lava_group = pygame.sprite.Group()
coin_group = pygame.sprite.Group()
exit_group = pygame.sprite.Group()

#visual coin for coin counter
score_coin = Coin(tile_size // 2, tile_size // 2)
coin_group.add(score_coin)


#create world from level data
if path.exists(f'level{level}_data'):
    pickle_in = open(f'level{level}_data', 'rb')
    world_data = pickle.load(pickle_in)
world = World(world_data)

#create buttons
restart_button = Button(screen_width // 2 - 50, screen_height // 2 + 100, restart_img)
start_button = Button(screen_width // 2 - 350, screen_height // 2, start_img)
exit_button = Button(screen_width // 2 + 150, screen_height // 2, exit_img)




run = True
while run:

    clock.tick(fps)

    if level == 0:
        screen.blit(bg_img, (0, 0))
        
        

    if level == 1:
        screen.blit(bg_img, (0, 0))
        

    if level == 2:
        screen.blit(bg2_img, (0, 0))
        
        

    if level == 3:
        screen.blit(bg3_img, (0, 0))
        

    if level == 4:
        screen.blit(bg4_img, (0, 0))
        

    if level == 5:
        screen.blit(bg5_img, (0, 0))
        

    if level == 6:
        screen.blit(bg6_img, (0, 0))
        

    if level == 7:
        screen.blit(bg7_img, (0, 0))
        

    if main_menu == True:
        if exit_button.draw():
            run = False
        if start_button.draw():
            main_menu = False
    else:

        world.draw()

        if game_over == 0:
            blob_group.update()
            platform_group.update()
            if pygame.sprite.spritecollide(player, coin_group, True):
                score += 1
                coin_fx.play()

            draw_text('X ' + str(score), font_score, white, tile_size - 10, 10)

        blob_group.draw(screen)
        platform_group.draw(screen)
        lava_group.draw(screen)
        coin_group.draw(screen)
        exit_group.draw(screen)

        

        game_over = player.update(game_over)

        #game over function
        if game_over == -1:
            if restart_button.draw():
                world_data = []
                world = reset_level(level)
                game_over = 0
                score = current_score

        #next level or end game
        if game_over == 1:
            level += 1
            current_score = score
            if level <= max_levels:
                world_data = []
                world = reset_level(level)
                game_over = 0

            #special ending screen for collecting all hearts    
            elif game_over == 1 and score >= 35:
                draw_text('Good night, sweet dreams!', font, blue, (screen_width // 2) - 300, screen_height // 2 )
                if restart_button.draw():
                    level = 1
                    world_data = []
                    world = reset_level(level)
                    game_over = 0
                    score = current_score

            #regular ending screen
            else:
                draw_text('Good night!', font, blue, (screen_width // 2) - 140, screen_height // 2 )
                if restart_button.draw():
                    level = 1
                    world_data = []
                    world = reset_level(level)
                    game_over = 0
                    score = current_score


    

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False

    pygame.display.update()

pygame.quit()
