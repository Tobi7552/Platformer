# importer Pygames filerne
import pygame
from pygame.locals import *
import pickle
from os import path
# Inasilisere pygames
pygame.init()

clock = pygame.time.Clock()
fps = 60

# Definere størelsen på spillevinduet
screen_width = 800
screen_height = 800

# Fukntione laver spillevinduet for os ved hjælp af vores variabler
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption('Platformer')

# Definer fonten til score
font = pygame.font.SysFont('Bauhaus 93', 70)
font_score = pygame.font.SysFont('Bauhaus 93', 30)

# Definer farve
white = (255, 255, 255)
blue = (0, 0, 255)

# definer spillevariabler
tile_size = 40
game_over = 0
main_menu = True
level = 1
max_levels = 7
score = 0

# Indsæt billeder fra mappe
sun_img = pygame.image.load('sun.png')
sky_img = pygame.image.load('sky.png')
restart_img = pygame.image.load('restart_btn.png')
start_img = pygame.image.load('start_btn.png')
exit_img = pygame.image.load('exit_btn.png')


def draw_text(text, font, text_col, x, y):
    img = font.render(text, True, text_col)
    screen.blit(img, (x, y))


# fuktion der reseter level
def reset_level(level):
    player.reset(100, screen_height - 117.5)
    lava_group.empty()
    blob_group.empty()
    exit_group.empty()

    # loader levels og laver banen
    if path.exists(f'level{level}_data'):
        pickle_in = open(f'level{level}_data', 'rb')
        world_data = pickle.load(pickle_in)
    world = World(world_data)

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

        # få museposition
        pos = pygame.mouse.get_pos()

        # Tjekker for mus over/ og klikkede conditions
        if self.rect.collidepoint(pos):
            if pygame.mouse.get_pressed()[0] == 1 and self.clicked == False:
                action = True
                self.clicked = True

        if pygame.mouse.get_pressed()[0] == 0:
            self.clicked = False
        # Tegner knappen
        screen.blit(self.image, self.rect)

        return action


class Player():
    def __init__(self, x, y):
        self.reset(x, y)

    def update(self, game_over):
        dx = 0
        dy = 0
        walk_cooldown = 5

        if game_over == 0:
            # Spiller input
            key = pygame.key.get_pressed()
            if key[pygame.K_SPACE] and self.jumped == False and self.in_air == False:
                self.vel_y = -15
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

            # Animation
            if self.counter > walk_cooldown:
                self.counter = 0
                self.index += 1
                if self.index >= len(self.images_right):
                    self.index = 0
                if self.direction == 1:
                    self.image = self.images_right[self.index]
                if self.direction == -1:
                    self.image = self.images_left[self.index]

            # Tilføjer tyngdekræft så spilleren ikke bare flyver
            self.vel_y += 1
            if self.vel_y > 10:
                self.vel_y = 10
            dy += self.vel_y

            # Check for collision
            self.in_air = True
            for tile in world.tile_list:
                # Tjekker for collision i x-aksen
                if tile[1].colliderect(self.rect.x+dx, self.rect.y, self.width, self.height):
                    dx = 0
                    # Tjekker for collision i y-aksen
                if tile[1].colliderect(self.rect.x, self.rect.y+dy, self.width, self.height):
                    # Tjekker hvis den er under spilleren, fx når man hoppe
                    if self.vel_y < 0:
                        dy = tile[1].bottom - self.rect.top
                        self.vel_y = 0
                        # Tjekker hvis den er over spilleren, fx når man falder
                    elif self.vel_y >= 0:
                        dy = tile[1].top - self.rect.bottom
                        self.vel_y = 0
                        self.in_air = False

            # check for collision med enemys
            if pygame.sprite.spritecollide(self, blob_group, False):
                game_over = -1
            # Tjekker for kollision med lava
            if pygame.sprite.spritecollide(self, lava_group, False):
                game_over = -1
            # Tjekker for kollision med exit
            if pygame.sprite.spritecollide(self, exit_group, False):
                game_over = 1

            # Opdater spiller kordinatter
            self.rect.x += dx
            self.rect.y += dy

        elif game_over == -1:
            self.image = self.dead_image
            self.rect.y -= 5

        # tegner spilleren
        screen.blit(self.image, self.rect)
        pygame.draw.rect(screen, (255, 255, 255), self.rect, 2)

        return game_over

    def reset(self, x, y):
        self.images_right = []
        self.images_left = []
        self.index = 0
        self.counter = 0
        for num in range(1, 5):
            img_right = pygame.image.load(f'guy{num}.png')
            img_right = pygame.transform.scale(img_right, (32, 64))
            img_left = pygame.transform.flip(img_right, True, False)
            self.images_right.append(img_right)
            self.images_left.append(img_left)
        self.dead_image = pygame.image.load('ghost.png')
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

        # indlæs billederne
        dirt_img = pygame.image.load('/Users/tobi7552/Desktop/Platformer/dirt.png')
        grass_img = pygame.image.load('/Users/tobi7552/Desktop/Platformer/grass.png')

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
                    blob = Enemy(col_count * tile_size, row_count * tile_size + 7.5)
                    blob_group.add(blob)
                if tile == 6:
                    lava = Lava(col_count * tile_size, row_count * tile_size + (tile_size // 2))
                    lava_group.add(lava)
                if tile == 7:
                    coin = Coin(col_count * tile_size + (tile_size // 2),
                                row_count * tile_size + (tile_size // 2))
                    coin_group.add(coin)
                if tile == 8:
                    exit = Exit(col_count * tile_size, row_count * tile_size - (tile_size // 2))
                    exit_group.add(exit)
                col_count += 1
            row_count += 1

    def draw(self):
        for tile in self.tile_list:
            screen.blit(tile[0], tile[1])
            pygame.draw.rect(screen, (255, 255, 255), tile[1], 2)


class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        img = pygame.image.load('blob.png')
        self.image = pygame.transform.scale(img, (38, 34))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.move_direction = 1
        self.move_counter = 0

    def update(self):
        self.rect.x += self.move_direction
        self.move_counter += 1
        if abs(self.move_counter) > self.rect.width:
            self.move_direction *= -1
            self.move_counter *= -1


class Lava(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        img = pygame.image.load('lava.png')
        self.image = pygame.transform.scale(img, (tile_size, tile_size // 2))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y


class Coin(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        img = pygame.image.load('coin.png')
        self.image = pygame.transform.scale(img, (tile_size // 2, tile_size // 2))
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)


class Exit(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        img = pygame.image.load('exit.png')
        self.image = pygame.transform.scale(img, (tile_size, int(tile_size * 1.5)))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y


player = Player(100, screen_height - 117.5)

blob_group = pygame.sprite.Group()
lava_group = pygame.sprite.Group()
coin_group = pygame.sprite.Group()
exit_group = pygame.sprite.Group()

# Laver coin til score
score_coin = Coin(tile_size // 2, tile_size // 2)
coin_group.add(score_coin)

# Loader leveldata og skaber verdene
if path.exists(f'level{level}_data'):
    pickle_in = open(f'level{level}_data', 'rb')
    world_data = pickle.load(pickle_in)
world = World(world_data)

# Laver knappen
restart_button = Button(screen_width // 2 - 50, screen_height // 2 - 50, restart_img)
start_button = Button(screen_width // 2 - 350, screen_height // 3, start_img)
exit_button = Button(screen_width // 2 + 110, screen_height // 3, exit_img)

# Sætter run = True gør sålede at vinduet ikke lukker når spillet køre


run = True
# Main loopet
# Laver en while lykke
while run:

    clock.tick(fps)

    # Loader billederne i koden. Vigtigt at det billede der skal loades først
    # er den første i koden
    screen.blit(sky_img, (0, 0))
    screen.blit(sun_img, (100, 100))

    if main_menu == True:
        if exit_button.draw():
            run = False
        if start_button.draw():
            main_menu = False
    else:
        world.draw()

        if game_over == 0:
            blob_group.update()
            # Opdatere scoren
            # se om coinen er blevet samlet op
            if pygame.sprite.spritecollide(player, coin_group, True):
                score += 1
            draw_text('Coins ' + str(score), font_score, white, tile_size - 10, 10)

        blob_group.draw(screen)
        lava_group.draw(screen)
        coin_group.draw(screen)
        exit_group.draw(screen)

        game_over = player.update(game_over)

        # Hvis spilelren dør
        if game_over == -1:
            if restart_button.draw():
                world_data = []
                world = reset_level(level)
                game_over = 0
                score = 0

        # Hvis du gennemføre banen
        if game_over == 1:
            # restart spillet og gå til næste level
            level += 1
            if level <= max_levels:
                draw_text('You Win!', font, blue, (screen_width // 2) - 140, screen_height // 2)
                # restart level
                world_data = []
                world = reset_level(level)
                game_over = 0
            else:
                if restart_button.draw():
                    level = 1
                    # restart level
                    world_data = []
                    world = reset_level(level)
                    game_over = 0
                    score = 0

        # Gør således at spillet lukker når man trykker på krydset.
        # Dette gør den ved at sætte run=False
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False

        # Opdatere display
    pygame.display.update()
pygame.quit()
