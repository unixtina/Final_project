import pygame
import numpy as np

import camera
from player import Player
from enemy_controller import EnemyController
from config import *


class Menu:
    def __init__(self):
        self.options_bottoms = []
        self.functions = []
        self.current = 0

    def new_option(self, option, function):
        self.options_bottoms.append(font1.render(option, True, RED))
        self.functions.append(function)

    def switch(self, direction):
        self.current = max(0, min(self.current + direction, len(self.options_bottoms) - 1))

    def select(self):
        self.functions[self.current]()

    def draw(self, surface, x, y, distance):
        for i, option in enumerate(self.options_bottoms):
            option_rect = option.get_rect()
            option_rect.topleft = (x, y + i * distance)
            if i == self.current:
                pygame.draw.rect(surface, (100, 100, 75), option_rect)
            surface.blit(option, option_rect)


def get_range(x1, y1, x2, y2):
    return ((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5


def get_direction(x1, y1, x2, y2):
    direction = np.array([x2 - x1, y2 - y1])
    return direction / np.linalg.norm(direction)


def draw_menu(filename, score):
    """отрисовка меню после смерти"""
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_w:
                    menu.switch(-1)
                elif event.key == pygame.K_s:
                    menu.switch(1)
                elif event.key == pygame.K_SPACE:
                    running = menu.select()
        menu_bg = pygame.image.load(filename)

        screen.blit(menu_bg, (0, 0))
        menu.draw(screen, 200, 400, 75)
        if score >= 0:
            text = font1.render(f'Your score: {score}', True, RED)
            screen.blit(text, (760, 720))

        pygame.display.flip()
    pygame.quit()


class Game:
    colliders = []
    collider_map = COLLIDE_MAP

    def __init__(self, screen: pygame.Surface, clock: pygame.time.Clock, spawn_time: int, font_style: pygame.font.Font,
                 player, enemy_controller) -> None:
        self.lvlups = pygame.image.load(LVLUPS).convert_alpha()
        self.lvlups_list = [(0, 0), (0, 80), (0, 160), (0, 240), (0, 320), (0, 400)]
        self.screen = screen
        self.clock = clock
        self.spawn_time = spawn_time
        self.font_style = font_style
        self.player = player
        self.enemy_controler = enemy_controller
        self.score = 0
        self.timer = 0

    def parse_colliders(self):
        """добавление коллизий"""
        with open(self.collider_map) as f:
            for line in f.readlines():
                line = list(map(int, line.split()))
                self.colliders.append(pygame.Rect((line[0], line[1], line[2] - line[0], line[3] - line[1])))

    def render_level(self):
        """отрисовка карты"""
        lvl = self.font_style.render(f'Level: {self.player.level}', False, (255, 255, 255))
        self.screen.blit(lvl, (10, 190))

    def add_lvl_up(self, i):
        """варианты улучшений"""
        match i:
            case 0:
                self.player.max_health = int(self.player.max_health * 1.2)
                self.player.health = int(self.player.health * 1.2)
            case 1:
                self.player.heal(self.player.max_health * 0.3)
            case 2:
                self.enemy_controler.damage_reduce *= 0.9
            case 3:
                self.player.orbits[0].new_weapon(self.player)
            case 4:
                for orbit in self.player.orbits:
                    orbit.set_damage(1.1)
                self.player.damage *= 1.1
            case 5:
                self.player.orbits[0].vampire += 0.1

    def render_exp(self):
        """отрисовка уровня игрока"""
        pygame.draw.rect(self.screen, (170, 170, 170), (10, 90, 300, 30), border_radius=1)
        pygame.draw.rect(self.screen, WHITE, (10, 90, self.player.exp / self.player.exp_for_lvlup * 300, 30))

    def collision_handing(self, player, direction):
        """проверка колллизий"""
        for collider in self.colliders:
            if direction[0] > 0:
                deltax = player.rect.right - collider.left - direction[0] * player.v
            else:
                deltax = collider.right - player.rect.left + direction[0] * player.v
            if direction[1] > 0:
                deltay = collider.bottom - player.rect.top - direction[1] * player.v
            else:
                deltay = player.rect.bottom + direction[1] * player.v - collider.top

            if pygame.Rect.colliderect(collider, player.rect):
                if deltax < player.v:
                    direction[0] = 0
                if deltay < player.v:
                    direction[1] = 0

        return direction

    def render_score(self):
        """выыодит на экран текущий счет"""
        health = self.font_style.render(f'Score: {self.score}', False, (255, 255, 255))
        self.screen.blit(health, (10, 140))

    def health_render(self):
        """"выводит на экран здоровье игрока"""
        health = self.font_style.render(f'{int(self.player.health)} / {self.player.max_health}', False, (0, 200, 0))
        self.screen.blit(health, (10, 50))

    def render_colliders(self):
        """устонавливает коллизии обЪектов"""
        for collider in self.colliders:
            pygame.draw.rect(self.screen, RED, collider)

    def add_time(self):
        self.timer += 1 / FPS
        if self.timer >= WIN_TIME:
            draw_menu(WIN_MENU, self.score)
        time = self.font_style.render(
            f'Time: {int((WIN_TIME - self.timer) // 60)} : {int((WIN_TIME - self.timer) % 60)}', False, (255, 255, 255))
        self.screen.blit(time, (10, 250))

    def get_direction(self, keys, player):
        """считывает нажатия клавиш и задаёт направление игроку"""
        direction = np.array([0, 0])
        if keys[pygame.K_s]:
            direction[1] -= 1
            player.direction = 1
        elif keys[pygame.K_w]:
            direction[1] += 1
            player.direction = 2
        if keys[pygame.K_d]:
            direction[0] += 1
            player.direction = 0
        elif keys[pygame.K_a]:
            direction[0] -= 1
            player.direction = 3

        norm = np.linalg.norm(direction)
        if norm:
            player.animator.start_animation()
            return direction / norm
        player.animator.stop_animation()
        return direction


def init():
    """Инициализация игры"""
    font_style = pygame.font.Font(None, 36)
    clock = pygame.time.Clock()
    return (font_style, clock)


def loop(game):
    """основной игровой цикл"""
    game._map = pygame.image.load(MAP_LEVEL).convert_alpha()
    map_pixels = pygame.surfarray.array2d(game._map)
    game.parse_colliders()
    finished = False
    while not finished:
        game.clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                finished = True
        if game.player.new_level == 1:
            pygame.draw.rect(game.screen, BLACK, (WIDTH / 2 - 200, HEIGHT / 2 - 150, 400, 300))
            en = list(enumerate(game.lvlups_list))
            np.random.shuffle(en)
            rects = []
            for i in range(3):
                game.screen.blit(game.lvlups, (WIDTH / 2 - 190, HEIGHT / 2 - 140 + 100 * i), (*en[i][1], 380, 80))
                rects.append([en[i][0], pygame.rect.Rect(WIDTH / 2 - 190, HEIGHT / 2 - 140 + 100 * i, 380, 80)])
            game.player.new_level = 2
        elif game.player.new_level == 2:
            if pygame.mouse.get_pressed()[0]:
                position = pygame.mouse.get_pos()
                for (i, rect) in rects:
                    if pygame.rect.Rect.collidepoint(rect, *position):
                        game.add_lvl_up(i)
                        game.player.new_level = 0
        else:
            x_to_array, x_to_render, y_to_array, y_to_render = camera.edge_handing(game.player.rect.x,
                                                                                   game.player.rect.y,
                                                                                   map_pixels.shape[0],
                                                                                   map_pixels.shape[1])
            keys = pygame.key.get_pressed()
            game.enemy_controler.add_time(1 / FPS)
            game.enemy_controler.wall_handler(game.colliders)
            game.enemy_controler.is_atack()
            game.score += game.enemy_controler.is_atacked()
            game.screen.blit(game._map, (0, 0), camera.camera_move(x_to_array, y_to_array))
            game.enemy_controler.draw_enemy(x_to_array, y_to_array)
            game.player.move(game.collision_handing(game.player, game.get_direction(keys, game.player)))
            game.player.draw(game.screen, x_to_render, y_to_render)
            game.health_render()
            game.render_score()
            game.render_exp()
            game.render_level()
            game.add_time()
        if game.player.death:
            draw_menu(LOSE_MENU, -1)
        else:
            pygame.display.update()
    pygame.quit()


def start():
    """запуск игры"""
    font_style, clock = init()
    player = Player(900, 700, 10, PLAYER_SPRITES)
    game = Game(screen, clock, 500, font_style, player, EnemyController(screen, 0.2, 10, player, 5))
    game.enemy_controler.spawn_enemy()
    return game


def game_start():
    game = start()
    loop(game)


if __name__ == '__main__':
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    font1 = pygame.font.SysFont(MENU_FONT, 50)
    menu = Menu()
    menu.new_option("start", lambda: game_start())
    menu.new_option("quit", lambda: False)
    pygame.display.set_caption(GAMENAME)
    draw_menu(START_MENU, -1)
