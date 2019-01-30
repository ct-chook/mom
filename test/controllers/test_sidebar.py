import pytest

from components.board.players import Player
from helper.events.events import Publisher
from src.helper.Misc.options_game import Options
from src.components.board.monster import Monster
from src.components.board.tile import Tile
from src.helper.Misc.constants import Terrain, MonsterType
from src.controller.sidebar_controller import Sidebar

Options.headless = True

class TestCase:
    @pytest.fixture
    def before(self):
        self.sidebar = Sidebar()
        self.view = self.sidebar.view
        self.player_1 = Player(0, 0, 0, 0, 0)

    def test(self):
        # for pycharm to recognize this as a testing class
        pass

    def display_tile_with_terrain(self, terrain):
        tile = self.create_tile(terrain)
        self.display_tile_info_for(tile)
        return tile

    def create_tile(self, terrain):
        return Tile(terrain)

    def display_tile_info_for(self, tile):
        self.sidebar.display_tile_info(tile)
        self.view.update_sprites()

    def assert_terrain_is(self, terrain_text):
        assert terrain_text == self.view.terrain.text

    def assert_no_monster_info(self):
        self.assert_monster_info('', '', '', '')

    def assert_monster_info(self, name, hp, max_hp, owner):
        assert name == self.view.monster_name.text
        assert str(hp) == self.view.monster_hp.text
        assert str(max_hp) == self.view.monster_max_hp.text
        assert owner == self.view.monster_owner.text

    def assert_no_terrain_owner(self):
        self.assert_terrain_owner('')

    def assert_terrain_owner(self, owner_text):
        assert owner_text == self.view.terrain_owner.text


class TestMouseoverDisplay(TestCase):
    def test_grass_with_no_monster(self, before):
        self.display_tile_with_terrain(Terrain.GRASS)
        self.assert_terrain_is('Grassland')
        self.assert_no_monster_info()

    def test_ocean_with_no_monster(self, before):
        self.display_tile_with_terrain(Terrain.OCEAN)
        self.assert_terrain_is('Ocean')
        self.assert_no_monster_info()

    def test_unclaimed_tower_with_no_monster(self, before):
        self.display_tile_with_terrain(Terrain.TOWER)
        self.assert_terrain_is('Tower')
        self.assert_terrain_owner('')
        self.assert_no_monster_info()

    def test_claimed_tower_with_no_monster(self, before):
        tile = self.create_tile(Terrain.TOWER)
        tile.owner = 0
        self.display_tile_info_for(tile)
        self.assert_terrain_is('Tower')
        self.assert_no_monster_info()

    def test_dune_with_lizard(self, before):
        tile = self.create_tile(Terrain.DUNE)
        monster = Monster(MonsterType.LIZARD, (0, 0), self.player_1,
                          Terrain.DUNE)
        tile.monster = monster
        monster.hp = 15
        self.display_tile_info_for(tile)
        self.assert_terrain_is('Dune')
        self.assert_monster_info('Lizard', 15, 30, 'Player 0')

    def test_two_mouseovers_monster(self, before):
        tile = self.create_tile(Terrain.GRASS)
        tile.monster = Monster(MonsterType.SPHINX, (0, 0), self.player_1,
                               Terrain.GRASS)
        self.display_tile_info_for(tile)
        self.display_tile_with_terrain(Terrain.ROCKY)
        self.assert_terrain_is('Rocky Tracts')
        self.assert_no_monster_info()

    def test_two_mouseovers_tower(self, before):
        tile = self.create_tile(Terrain.TOWER)
        tile.owner = 1
        self.display_tile_info_for(tile)
        self.display_tile_with_terrain(Terrain.TOWER)
        self.assert_terrain_is('Tower')
        assert '' == self.view.terrain_owner.text
        self.assert_no_monster_info()
