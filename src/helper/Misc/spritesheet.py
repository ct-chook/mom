import pygame
from math import floor
from src.helper.Misc.constants import ROOT, Color, Terrain, TERRAIN_COUNT, \
    MONSTER_COUNT
from src.helper.Misc.options_game import Options

monster_spritesheet_filename = \
    f'{ROOT}src/data/monsters/monsters_spritesheet.png'
terrain_spritesheet_filename = f'{ROOT}src/data/terrain/terrain_spritesheet.png'


player_colors = (
            Color.PLAYER_BLUE, Color.PLAYER_RED, Color.PLAYER_GREEN,
            Color.PLAYER_YELLOW)


class SpriteSheet:
    scale = Options.scale

    # specify filename of spritesheet, and how many columns
    # of sprites (read left to right, top to bottom)
    def __init__(self, filename, size, max_rows, max_columns):
        self.tile_width = size
        self.tile_height = size
        self.max_rows = max_rows
        self.max_columns = max_columns
        self.sprites = []

        if not filename or Options.headless:
            self.sheet = None
        else:
            self.sheet = pygame.image.load(filename).convert()

    def get_sprite(self, index):
        return self.sprites[index]

    def replace_color_of_sheet(self, source_color, target_color):
        self.replace_color_of_surface(self.sheet, source_color, target_color)

    @staticmethod
    def replace_color_of_surface(surface, source_color, target_color):
        if Options.headless:
            return
        pixel_array = pygame.PixelArray(surface)
        pixel_array.replace(source_color, target_color)
        del pixel_array  # needed to unlock the surface

    def generate_sprites(self):
        #  below needs +1 for monsters
        max_index = (1 + self.max_rows) * self.max_columns
        for index in range(max_index):
            self.sprites.append(self._generate_sprite(index))
    # noinspection PyArgumentList

    def _generate_sprite(self, index):
        if Options.headless:
            return None
        sprite_rect = self._get_sprite_rectangle(index)
        sprite = pygame.Surface(sprite_rect.size).convert()
        sprite.blit(self.sheet, (0, 0), sprite_rect)
        # set spritesheet background to transparent
        sprite.set_colorkey(Color.MAGENTA_BACKGROUND, pygame.RLEACCEL)
        sprite = self._scale_sprite(sprite).convert()
        return sprite

    def generate_tower_sprites(self):
        for index in range(Options.player_count):
            sprite = self._generate_sprite(Terrain.TOWER_CLAIMED)
            self.replace_color_of_surface(
                sprite, Color.PLAYER_BLUE, player_colors[index])
            self.sprites.append(sprite)

    def _scale_sprite(self, sprite):
        if self.scale == 1:
            return sprite
        scaled_dimensions = (
            self.tile_width * self.scale, self.tile_height * self.scale)
        return pygame.transform.scale(sprite, scaled_dimensions)

    def _get_sprite_rectangle(self, index):
        sheet_y = floor(index / self.max_columns) * self.tile_height
        sheet_x = (index % self.max_columns) * self.tile_width
        rect = pygame.Rect(
            (sheet_x, sheet_y, self.tile_width, self.tile_height))
        return rect

    def generate_mini_terrain_sprites(self, size):
        # + 4 to take owned towers into account
        for i in range(TERRAIN_COUNT + 4):
            sprite = pygame.Surface((size, size))
            sprite.fill(TERRAIN_COLORS[i])
            self.sprites.append(sprite)

    def generate_mini_monster_sprites(self, size, player):
        sprite = pygame.Surface((size, size))
        sprite.fill(player_colors[player])
        for n in range(MONSTER_COUNT):
            self.sprites.append(sprite)


TERRAIN_COLORS = (Color.WHITE, Color.GRAY, Color.RED, Color.MAGENTA,
                  Color.YELLOW,
                  Color.GREEN, Color.DARK_GREEN, Color.LIGHT_BLUE, Color.BLUE,
                  Color.BLACK, Color.BLACK, Color.BLACK, Color.BLACK,
                  Color.BLACK, Color.BLACK, Color.BLACK, Color.BLACK,
                  Color.BLACK)


class MonsterSpriteSheet:
    """A slightly different version that requires to specify player color"""
    def __init__(self, max_players):
        self.sprites = {}
        self.max_players = max_players

    def get_sprite(self, index, owner):
        return self.sprites[owner].get_sprite(index)

    def generate_sprites(self):
        for player_id in range(self.max_players):
            spritesheet = SpriteSheet(
                monster_spritesheet_filename,
                size=24, max_rows=10, max_columns=8)
            self.sprites[player_id] = spritesheet
            player_color = player_colors[player_id]
            spritesheet.replace_color_of_sheet(
                Color.PLAYER_BLUE, player_color)
            spritesheet.generate_sprites()

    def generate_mini_sprites(self, size):
        for player_id in range(self.max_players):
            spritesheet = SpriteSheet(
                '',
                size=24, max_rows=10, max_columns=8)
            self.sprites[player_id] = spritesheet
            spritesheet.generate_mini_monster_sprites(size, player_id)


class SpriteSheetFactory:
    """Used to retrieve sprite sheets using the flyweight pattern

    The factory should be used to get spritesheets.
    """
    terrain_spritesheet = None
    monster_spritesheet = None
    minimap_monsters = None
    minimap_terrain = None

    def get_monster_spritesheets(self) -> MonsterSpriteSheet:
        if not self.monster_spritesheet:
            self._load_monster_sprites()
        return self.monster_spritesheet

    def get_terrain_spritesheet(self) -> SpriteSheet:
        if not self.terrain_spritesheet:
            self._load_terrain_sprites()
        return self.terrain_spritesheet

    def _load_terrain_sprites(self):
        self.terrain_spritesheet = SpriteSheet(
            terrain_spritesheet_filename, size=24, max_rows=1, max_columns=99)
        self.terrain_spritesheet.generate_sprites()
        self.terrain_spritesheet.generate_tower_sprites()

    def _load_monster_sprites(self):
        for player_id in range(Options.player_count):
            self.monster_spritesheet = MonsterSpriteSheet(Options.player_count)
            self.monster_spritesheet.generate_sprites()

    def get_minimap_terrain(self, size) -> SpriteSheet:
        if not self.minimap_terrain:
            self.minimap_terrain = SpriteSheet(
                '', size=24, max_rows=1, max_columns=99)
            self.minimap_terrain.generate_mini_terrain_sprites(size)
        return self.minimap_terrain

    def get_minimap_monsters(self, size) -> MonsterSpriteSheet:
        if not self.minimap_monsters:
            self.minimap_monsters = MonsterSpriteSheet(Options.player_count)
            self.minimap_monsters.generate_mini_sprites(size)
        return self.minimap_monsters
