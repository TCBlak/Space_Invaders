import pygame, sys
from player import Player
import obstacle
from alien import Alien, UFO
from random import choice, randint
from laser import Laser

class Game:
    def __init__(self):
        # Player setup
        player_sprite = Player(pos=(screen_width / 2, screen_height), screen_width=screen_width, speed=5)
        self.player = pygame.sprite.GroupSingle(player_sprite)

        # health and score setup
        self.lives = 3
        self.live_surf = pygame.image.load('graphics/player.png')
        self.live_x_start_pos = screen_width - (self.live_surf.get_size()[0] * 2 + 20)
        self.score = 0
        self.font = pygame.font.Font('font/Pixeled.ttf', 20)

        # Obstacle setup
        self.shape = obstacle.shape
        self.block_size = 6
        self.blocks = pygame.sprite.Group()
        self.obstacle_amount = 4
        self.obstacle_x_positions = [num * (screen_width / self.obstacle_amount) for num in range(self.obstacle_amount)]
        x_start = (screen_width - (self.obstacle_x_positions[-1] + (len(obstacle.shape[0]) * self.block_size))) // 2
        self.create_multiple_obstacles(*self.obstacle_x_positions, x_start=x_start, y_start=480)

        # Alien setup
        #self.aliens = ExtendedGroup()
        self.aliens = pygame.sprite.Group()
        self.alien_lasers = pygame.sprite.Group()
        self.alien_setup(rows=6, cols=8)
        self.alien_direction = 1

        # UFO setup
        self.ufo = pygame.sprite.GroupSingle()
        self.ufo_spawn_time = randint(400, 800)

        # Audio
        self.music = pygame.mixer.Sound('audio/music.wav')
        self.music.set_volume(0.1)
        self.music.play(-1)

        self.laser_sound = pygame.mixer.Sound('audio/laser.wav')
        self.laser_sound.set_volume(0.2)
        self.explosion_sound = pygame.mixer.Sound('audio/explosion.wav')
        self.explosion_sound.set_volume(0.2)

    def create_obstacle(self, x_start, y_start, offset_x):
        for row_index, row in enumerate(self.shape):
            for col_index, col in enumerate(row):
                if col == 'X':
                    x = x_start + col_index * self.block_size + offset_x
                    y = y_start + row_index * self.block_size
                    block = obstacle.Block(self.block_size, (241, 79, 80), x, y)
                    self.blocks.add(block)

    def create_multiple_obstacles(self, *offset, x_start, y_start):
        for offset_x in offset:
            self.create_obstacle(x_start, y_start, offset_x)

    def alien_setup(self, rows, cols, x_distance=60, y_distance=48, x_offset=70, y_offset=100):
        for row_index in range(rows):
            for col_index in range(cols):
                x = col_index * x_distance + x_offset
                y = row_index * y_distance + y_offset
                if row_index == 0: alien_sprite = Alien('yellow', x, y)
                elif 1 <= row_index <= 2: alien_sprite = Alien('green', x, y)
                else: alien_sprite = Alien('red', x, y)
                self.aliens.add(alien_sprite)

    def alien_position_checker(self):
        all_aliens = self.aliens.sprites()
        for alien in all_aliens:
            if alien.rect.left <= 0 or alien.rect.right >= screen_width:
                self.alien_direction *= -1
                self.alien_move_down(2)
                break

    def alien_move_down(self, distance):
        if self.aliens:
            for alien in self.aliens.sprites():
                alien.rect.y += distance

    def alien_shoot(self):
        if self.aliens.sprites():
            random_alien = choice(self.aliens.sprites())
            laser_sprite = Laser(random_alien.rect.center, 6, screen_height, random_alien.color)
            self.laser_sound.play()
            self.alien_lasers.add(laser_sprite)

    def ufo_timer(self):
        self.ufo_spawn_time -= 1
        if self.ufo_spawn_time <= 0:
            self.ufo.add(UFO(side=choice(['right', 'left']), screen_width=screen_width))
            self.ufo_spawn_time = randint(400, 800)

    def collision_checks(self):
        # player lasers
        if self.player.sprite.lasers:
            for laser in self.player.sprite.lasers:
                # obstacle collisions
                if pygame.sprite.spritecollide(laser, self.blocks, True):
                    self.explosion_sound.play()
                    laser.kill()

                # alien collisions
                aliens_hit = pygame.sprite.spritecollide(laser, self.aliens, True)
                if aliens_hit:
                    self.explosion_sound.play()
                    for alien in aliens_hit:
                        self.score += alien.value
                    laser.kill()

                # ufo collision
                if pygame.sprite.spritecollide(laser, self.ufo, True):
                    self.score += 500
                    self.explosion_sound.play()
                    laser.kill()

        # alien lasers
        if self.alien_lasers:
            for laser in self.alien_lasers:
                # obstacle collisions
                if pygame.sprite.spritecollide(laser, self.blocks, True):
                    self.explosion_sound.play()
                    laser.kill()

                # player collision
                if pygame.sprite.spritecollide(laser, self.player, False):
                    laser.kill()
                    self.explosion_sound.play()
                    self.lives -= 1
                    if self.lives <= 0:
                        self.music.stop()
                        self.aliens.empty()

        # alien
        if self.aliens:
            for alien in self.aliens:
                pygame.sprite.spritecollide(alien, self.blocks, True)

                if pygame.sprite.spritecollide(alien, self.player, False):
                    self.music.stop()


    def display_lives(self):
        for live in range(self.lives - 1):
            x = self.live_x_start_pos + (live * (self.live_surf.get_size()[0] + 10))
            screen.blit(self.live_surf, (x, 8))

    def display_score(self):
        score_surf = self.font.render(f'Score: {self.score}', False, 'white')
        score_rect = score_surf.get_rect(topleft=(10, -10))
        screen.blit(score_surf, score_rect)

    def victory_message(self):
        if not self.aliens.sprites() and self.lives > 0:
            victory_surf = self.font.render('You won', False, 'white')
            victory_rect = victory_surf.get_rect(center=(screen_width / 2, screen_height / 2))
            screen.blit(victory_surf, victory_rect)

    def loser_message(self):
        if self.lives <= 0:
            lose_surf = self.font.render('You lose. The world is destroyed.', False, 'white')
            lose_rect = lose_surf.get_rect(center=(screen_width / 2, screen_height / 2))
            screen.blit(lose_surf, lose_rect)

    def run(self):
        # update sprite groups
        self.player.update()
        self.alien_lasers.update()
        self.ufo.update()

        self.aliens.update(self.alien_direction)
        self.alien_position_checker()
        self.ufo_timer()
        self.collision_checks()

        # draw
        self.player.sprite.lasers.draw(screen)
        self.player.draw(screen)
        self.blocks.draw(screen)
        self.aliens.draw(screen)
        self.alien_lasers.draw(screen)
        self.ufo.draw(screen)
        self.display_lives()
        self.display_score()
        self.victory_message()
        self.loser_message()

class CRT:
    def __init__(self):
        self.tv = pygame.image.load('graphics/tv.png').convert_alpha()
        self.tv = pygame.transform.scale(self.tv, (screen_width, screen_height))

    def create_crt_lines(self):
        line_height = 3
        line_amount = int(screen_height / line_height)
        for line in range(line_amount):
            y_pos = line * line_height
            pygame.draw.line(self.tv, 'black', (0, y_pos), (screen_width, y_pos), 1)

    def draw(self):
        self.tv.set_alpha(randint(75, 90))
        #self.tv.set_alpha(125)
        self.create_crt_lines()
        screen.blit(self.tv, (0, 0))


if __name__ == '__main__':
    pygame.init()
    screen_width = 600
    screen_height = 600
    screen = pygame.display.set_mode((screen_width, screen_height))
    clock = pygame.time.Clock()
    game = Game()
    crt = CRT()

    ALIENLASER = pygame.USEREVENT + 1
    pygame.time.set_timer(ALIENLASER, 800)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == ALIENLASER:
                game.alien_shoot()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()

        screen.fill((30, 30, 30))
        game.run()
        crt.draw()

        pygame.display.flip()
        clock.tick(60)
