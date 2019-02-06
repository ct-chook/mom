import pytest

from src.abstract.controller import ControllerInfoFactory
from src.components.board.board import Board
from src.components.board.monster import Monster
from src.controller.board_controller import BoardController
from src.helper.Misc.constants import Terrain, MonsterType, AiType
from src.helper.Misc.options_game import Options

Options.headless = True

roman_x = 1
roman_y = 19
roman_start_pos = (roman_x, roman_y)

chim_start_pos = (1, 17)
chimera_pos = (roman_x, roman_y - 2)

crusader_x = 5
crusader_y = 5
crusader_start_pos = (crusader_x, crusader_y)

left_of_roman_start_pos = (roman_x - 1, roman_y)
next_to_chimera_pos = (roman_x - 1, roman_y - 2)
crusader_south_once = (crusader_x, crusader_y + 3)
crusader_south_twice = (crusader_x, crusader_y + 5)

daimyou_pos = (1, 1)
left_of_daimyou_pos = (daimyou_pos[0] - 1, daimyou_pos[1])
right_of_daimyou_pos = (daimyou_pos[0] + 1, daimyou_pos[1])
far_right_of_daimyou_pos = (daimyou_pos[0] + 2, daimyou_pos[1])

tower_pos = (4, 4)


class TestCase:
    # noinspection PyAttributeOutsideInit
    @pytest.fixture
    def make_board(self):
        info = ControllerInfoFactory().make()
        self.controller = BoardController(0, 0, 500, 500, info)
        self.publisher = info.publisher

        self.model = self.controller.model
        self.board: Board = self.model.board
        self.precombat_window = self.controller.precombat_window
        self.player_1 = self.model.players[0]
        self.player_2 = self.model.players[1]
        self.board.place_new_monster(Monster.Type.ROMAN, roman_start_pos)
        self.board.place_new_monster(Monster.Type.FIGHTER, crusader_start_pos)
        self.board.place_new_monster(Monster.Type.CHIMERA, chim_start_pos,
                                     self.player_2)
        self.before_more()

    def before_more(self):
        pass

    def click_on(self, pos):
        self.controller.handle_tile_selection(pos)

    def end_turn(self):
        self.controller.handle_end_of_turn()
        # let AI skip its turn
        for _ in range(120):
            self.tick_events(15)
            if not self.controller.is_ai_controlled:
                break
        assert not self.controller.is_ai_controlled

    def tick_events(self, times=1):
        for _ in range(times):
            self.publisher.tick_events()


class TestMoving(TestCase):
    def before_more(self):
        self.roman = self.board.monster_at(roman_start_pos)

    def test_move_left(self, make_board):
        self.click_on(roman_start_pos)
        self.click_on(left_of_roman_start_pos)
        assert self.roman.pos == left_of_roman_start_pos
        assert self.board.monster_at(left_of_roman_start_pos) == self.roman
        assert self.board.monster_at(roman_start_pos) is None

    def test_cannot_move_within_mountains(self, make_board):
        # click on the roman surrounded by mountains
        surrounded_roman_pos = (1, 5)
        right_of_surrounded_roman = (2, 5)
        self.click_on(surrounded_roman_pos)
        self.click_on(right_of_surrounded_roman)
        assert self.board.monster_at(right_of_surrounded_roman) is None

    def test_cannot_move_twice_on_same_turn(self, make_board):
        self.move_roman_left()
        self.click_on(left_of_roman_start_pos)
        self.click_on(roman_start_pos)
        assert self.roman.pos == left_of_roman_start_pos
        assert self.board.monster_at(roman_start_pos) is None

    def test_move_for_two_turns(self, make_board):
        self.move_roman_left()
        self.end_turn()
        assert self.board.get_current_player() is self.player_1
        # now move back to starting position
        self.click_on(left_of_roman_start_pos)
        self.click_on(roman_start_pos)
        assert self.roman.pos == roman_start_pos
        assert self.board.monster_at(left_of_roman_start_pos) is None

    def test_see_highlighted_tiles(self, make_board):
        self.click_on(roman_start_pos)
        assert self.controller.view.tiles_to_highlight
        self.click_on(left_of_roman_start_pos)

    def test_no_highlighting_after_attacking_with_no_moving(self, make_board):
        # derived from bug
        monster_pos = (8, 8)
        enemy_pos = (8, 9)
        self.board.place_new_monster(Monster.Type.TRICORN, monster_pos,
                                     self.player_1)
        self.board.place_new_monster(Monster.Type.CAESER, enemy_pos,
                                     self.player_2)
        self.click_on(monster_pos)
        self.click_on(enemy_pos)
        assert self.controller.precombat_window.attacks is not None
        self.controller.precombat_window.handle_attack_choice(0)
        self.tick_events()
        self.controller.combat_window.handle_mouseclick()
        self.tick_events()
        assert not self.controller.view.tiles_to_highlight

    def move_roman_left(self):
        self.click_on(roman_start_pos)
        self.click_on(left_of_roman_start_pos)
        self.tick_events(50)


class TestAttacking(TestCase):
    def before_more(self):
        self.roman = self.board.monster_at(roman_start_pos)
        self.crusader = self.board.monster_at(crusader_start_pos)

    def attack_chimera(self):
        self.click_on(roman_start_pos)
        self.click_on(next_to_chimera_pos)
        self.click_on(chimera_pos)
        assert self.precombat_window.visible
        self.precombat_window.short_range_button.handle_mouseclick()
        assert not self.precombat_window.visible
        assert self.controller.combat_window.visible
        self.tick_events()
        self.controller.combat_window.handle_mouseclick()
        self.tick_events()
        assert not self.controller.combat_window.visible

    def test_attack_chimera(self, make_board):
        assert self.roman.exp == 0
        self.attack_chimera()
        assert self.roman.exp == 1

    def test_cannot_attack_from_distance(self, make_board):
        self.click_on(roman_start_pos)
        self.click_on(chimera_pos)
        assert not self.controller.precombat_window.visible

    def test_cannot_move_after_attacking(self, make_board):
        self.attack_chimera()
        self.click_on(next_to_chimera_pos)
        self.click_on(roman_start_pos)
        assert self.roman.pos == next_to_chimera_pos

    def test_cannot_select_and_move_after_attacking(self, make_board):
        self.attack_chimera()
        self.click_on(next_to_chimera_pos)
        self.click_on(left_of_roman_start_pos)
        assert self.roman.pos == next_to_chimera_pos

    def test_attack_without_moving(self, make_board):
        self.click_on(roman_start_pos)
        self.click_on(next_to_chimera_pos)
        self.click_on(next_to_chimera_pos)
        assert not self.precombat_window.visible
        assert self.roman.exp == 0
        self.tick_events(50)
        self.end_turn()
        self.click_on(next_to_chimera_pos)
        self.click_on(chimera_pos)
        assert self.precombat_window.visible
        self.precombat_window.short_range_button.handle_mouseclick()
        assert not self.precombat_window.visible
        assert self.controller.combat_window.visible
        self.tick_events()
        assert self.roman.exp == 0
        self.controller.combat_window.handle_mouseclick()
        self.tick_events()
        assert not self.controller.combat_window.visible
        assert self.roman.exp == 1

    def test_attack_then_move_next_turn(self, make_board):
        # derived from bug
        # attack with one monster then move with other, move again next turn
        self.attack_chimera()
        self.click_on(crusader_start_pos)
        self.click_on(crusader_south_once)
        assert self.crusader.pos == crusader_south_once
        self.end_turn()
        self.click_on(crusader_south_once)
        self.click_on(crusader_south_twice)
        assert self.crusader.pos != crusader_south_once
        assert self.crusader.pos == crusader_south_twice


class TestSummoning(TestCase):
    def before_more(self):
        self.surround_pos_with_captured_towers(daimyou_pos)
        # add some more towers to compensate for starting monsters
        self.surround_pos_with_captured_towers((15, 15))

    def test_summon_monster(self, make_board):
        left_of_daimyou = self.board.tile_at(left_of_daimyou_pos)
        assert left_of_daimyou.monster is None
        # open summon window
        self.click_on(left_of_daimyou_pos)
        summon_window = self.controller.summon_window
        assert summon_window.visible
        # make summon choice
        summon_window.handle_summon_choice(0)
        assert summon_window.visible is False
        summoned_monster = left_of_daimyou.monster
        assert summoned_monster.type == MonsterType.DRAGON_DY
        assert summoned_monster.moved

    def test_cannot_summon_far_away(self, make_board):
        far_left_of_daimyou = self.board.tile_at(far_right_of_daimyou_pos)
        assert far_left_of_daimyou.monster is None
        # open summon window
        self.click_on(far_right_of_daimyou_pos)
        assert not self.controller.summon_window.visible

    def test_cannot_summon_on_top_of_monster(self, make_board):
        # create monsters left and right to daimyou
        assert self.board.monster_at(left_of_daimyou_pos) is None
        self.board.place_new_monster(
            MonsterType.CYCLOPS, left_of_daimyou_pos, self.player_1)
        self.board.place_new_monster(
            MonsterType.PEGASUS, right_of_daimyou_pos, self.player_2)
        assert self.board.monster_at(left_of_daimyou_pos)
        assert self.board.monster_at(right_of_daimyou_pos)
        # try summon monster left and right of daimyou
        left_of_daimyou = self.board.tile_at(left_of_daimyou_pos)
        assert left_of_daimyou.monster
        self.click_on(left_of_daimyou_pos)
        assert not self.controller.summon_window.visible
        self.click_on(right_of_daimyou_pos)
        assert not self.controller.summon_window.visible

    def surround_pos_with_captured_towers(self, pos):
        posses = self.board.get_posses_adjacent_to(pos)
        for adj_pos in posses:
            self.board.on_tile(adj_pos).set_terrain_to(Terrain.TOWER)
            self.board.capture_terrain_at(adj_pos, self.player_1)


class TestTowerCapture(TestCase):
    def before_more(self):
        self.crusader = self.board.monster_at(crusader_start_pos)
        self.tower_tile = self.board.tile_at(tower_pos)

    def test_tower_capture(self, make_board):
        self.move_crusader_to_tower()
        assert self.controller.tower_capture_window.visible
        # now wait for window animation
        self.tick_events(400)
        # then after a while the window should be gone
        self.assert_tower_captured_by(self.crusader)

    def test_tower_capture_close_window(self, make_board):
        self.move_crusader_to_tower()
        assert self.controller.tower_capture_window.visible
        # close window before_zigzag animation finishes
        self.controller.tower_capture_window.handle_mouseclick()
        # now window should be closed
        self.assert_tower_captured_by(self.crusader)

    def test_capture_by_enemy(self, make_board):
        # set enemy AI to human
        enemy = self.controller.model.players.get_player_by_id(1)
        enemy.ai_type = AiType.human
        # create enemy unit
        enemy_pos = (3, 3)
        roc = self.board.place_new_monster(MonsterType.LOC, enemy_pos,
                                           self.player_2)
        old_tower_count = self.model.get_current_player().tower_count
        # player 1 turn
        self.move_crusader_to_tower()
        self.controller.tower_capture_window.handle_mouseclick()
        self.assert_tower_captured_by(self.crusader)
        self.end_turn()
        # player 2 turn
        self.end_turn()
        # player 1 turn: move away from tower
        self.click_on(tower_pos)
        self.click_on(crusader_start_pos)
        self.end_turn()
        # player 2 turn: move to to tower
        self.click_on(enemy_pos)
        self.click_on(tower_pos)
        self.assert_tower_captured_by(roc)
        assert (self.model.players.get_player_by_id(0).tower_count
                == old_tower_count)

    def move_crusader_to_tower(self):
        crusader = self.board.monster_at(crusader_start_pos)
        self.set_tile_to_tower_and_move_monster(crusader, tower_pos)
        # now monster has to walk there
        self.tick_events(50)
        # then window should be visible

    def set_tile_to_tower_and_move_monster(self, monster, pos):
        self.board.set_terrain_to(pos, Terrain.TOWER)
        self.click_on(monster.pos)
        self.click_on(tower_pos)

    def assert_tower_captured_by(self, monster):
        assert not self.controller.tower_capture_window.visible
        assert self.board.monster_at(tower_pos) == monster, (
            'monster was not at tower')
        assert self.board.tower_owner_at(tower_pos) == monster.owner, (
            'Wrong owner')
        player = monster.owner
        # assumes player starts with 6 towers (adjacent tiles)
        assert player.tower_count == 7
