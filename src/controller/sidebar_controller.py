import pygame

from helper.Misc.constants import Color
from src.abstract.view import View
from src.abstract.window import Window
import src.components.board.players
from src.components.board.tile import Tile
from src.helper.Misc.datatables import DataTables
from src.helper.Misc.spritesheet import SpriteSheetFactory


class Sidebar(Window):
    def __init__(self):
        super().__init__(800, 0, 200, 600)
        self.view: SidebarView = self.add_view(SidebarView)

    def display_tile_info(self, tile):
        self.view.update_tile_info(tile)

    def display_turn_info(self, player, sun_stance):
        self.view.update_turn_info(sun_stance, player)


class SidebarView(View):
    def __init__(self, rectangle):
        super().__init__(rectangle)
        self.tile_displayed = None
        self.set_bg_color(Color.BLACK)

        self.monster_sprites = SpriteSheetFactory().get_monster_spritesheets()
        # terrain info
        terrain_y_offset = 25
        self.terrain = self.add_text(
            '', size=24, offset=(0, terrain_y_offset + 50))
        self.terrain_owner = self.add_text(
            '', size=24, offset=(0, terrain_y_offset + 75))

        # monster info
        monster_y_offset = 150
        self.monster_name = self.add_text(
            '', size=24, offset=(0, monster_y_offset))
        self.monster_owner = self.add_text(
            '', size=24, offset=(0, monster_y_offset + 25))
        self.monster_hp = self.add_text(
            '', size=24, offset=(0, monster_y_offset + 75))
        self.hp_divisor = self.add_text(
            '/', size=24, offset=(50, monster_y_offset + 75))
        self.monster_max_hp = self.add_text(
            '', size=24, offset=(70, monster_y_offset + 75))

        self.blank_surface = pygame.Surface((0, 0))
        self.monster_sprite = self.add_sprite(
            self.blank_surface, offset=(30, monster_y_offset + 210))

        # player info
        player_y_offset = 25
        self.player_mana = self.add_text(
            '', size=24, offset=(50, player_y_offset))
        self.player_id = self.add_text(
            '', size=24, offset=(0, player_y_offset))
        self.tower_count = self.add_text(
            '', size=24, offset=(100, player_y_offset))

        # turn info
        turn_y_offset = 300
        self.sun_stance = self.add_text(
            '', size=24, offset=(50, turn_y_offset))
        self.active_player = self.add_text(
            '', size=24, offset=(150, turn_y_offset))

    sun_stance_to_text = {0: 'Dawn', 1: 'Day', 2: 'Dusk', 3: 'Night'}

    def update_turn_info(self, sun_stance,
                         active_player: src.components.board.players.Player):
        self.sun_stance.set_text(self.sun_stance_to_text[sun_stance])
        self.active_player.set_text(active_player.id_)
        self.player_mana.set_text(active_player.mana)
        self.tower_count.set_text(active_player.tower_count)
        # todo show this on sidebar
        # print(f'Player mana: {self.player_mana.text}')
        # print(f'Sun stance: {self.sun_stance.text}')
        # print(f'Active player: {self.active_player.text}')
        # print(f'Tower count: {self.tower_count.text}')
        self.queue_for_sprite_update()

    def update_tile_info(self, tile: Tile):
        if self.tile_displayed != tile:
            self._set_terrain_info_for(tile)
            self._set_monster_info_for(tile)
            self.tile_displayed = tile
            self.queue_for_sprite_update()

    def _set_terrain_info_for(self, tile):
        terrain_name = DataTables.terrain_name[tile.terrain]
        self.terrain.set_text(terrain_name)

    def _set_monster_info_for(self, tile):
        if tile.monster:
            monster = tile.monster
            name = monster.name
            owner = self._get_owner_text(monster)
            hp = str(monster.hp)
            max_hp = str(monster.stats.max_hp)
            sprite = self.monster_sprites.get_sprite(
                monster.type, monster.owner.id_)
            hp_divisor = '/'
        else:
            name = ''
            owner = ''
            hp = ''
            hp_divisor = ''
            max_hp = ''
            sprite = self.blank_surface
        self.monster_name.set_text(name)
        self.monster_owner.set_text(owner)
        self.monster_hp.set_text(hp)
        self.hp_divisor.set_text(hp_divisor)
        self.monster_max_hp.set_text(max_hp)
        self.monster_sprite.surface = sprite

    def _get_owner_text(self, owned_object):
        return 'Player ' + str(owned_object.owner.id_)
