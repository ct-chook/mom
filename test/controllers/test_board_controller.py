import pytest

from src.helper.Misc.options_game import Options
from src.controller.tile_editor_controller import TileEditorWindow, \
    TileEditorButtons
from src.helper.Misc.constants import Terrain, MonsterType, AiType
from src.helper.events.events import Publisher, EventQueue
from src.controller.board_controller import BoardController
from src.components.board.board import Board

Options.headless = True

roman_x = 1
roman_y = 19
roman_start_pos = (roman_x, roman_y)
chim_start_pos = (1, 17)
crusader_x = 5
crusader_y = 5
crusader_start_pos = (crusader_x, crusader_y)

left_of_roman_start_pos = (roman_x - 1, roman_y)
next_to_chimera_pos = (roman_x - 1, roman_y - 2)
chimera_pos = (roman_x, roman_y - 2)

crusader_south_once = (crusader_x, crusader_y + 3)
crusader_south_twice = (crusader_x, crusader_y + 5)

daimyou_pos = (9, 11)
left_of_daimyou_pos = (8, 11)
right_of_daimyou_pos = (10, 11)
far_left_of_daimyou_pos = (7, 11)
tower_pos = (4, 4)


class TestCase:
    @pytest.fixture
    def before(self):
        self.board_controller = BoardController(0, 0, 500, 500)
        self.model = self.board_controller.model
        self.board: Board = self.model.board
        self.precombat_window = self.board_controller.precombat_window
        self.publisher = Publisher()
        EventQueue.set_publisher(self.publisher)
        self.before_more()

    def before_more(self):
        pass

    def move_monster_to_tile(self, monster, tile):
        tile.terrain = Terrain.TOWER
        self.board_controller.handle_tile_selection(monster.pos)
        self.board_controller.handle_tile_selection(tower_pos)

    def end_turn(self):
        self.board_controller.handle_end_of_turn()
        # let AI skip its turn
        self.tick_events(5)

    def tick_events(self, times=1):
        for _ in range(times):
            self.publisher.tick_events()

    def test(self):
        # for pycharm to recognize this as a testing class
        pass


class TestClicking(TestCase):
    def test_click_works(self, before):
        # click on the roman surrounded by mountains
        self.board_controller.mouse_pos = (70, 230)
        self.board_controller.handle_mouseclick()
        assert self.board_controller.view.tiles_to_highlight is not None


class TestOther(TestCase):
    def test_idle_ai_turns(self, before):
        self.board_controller.end_of_turn_window.yes.handle_mouseclick()
        self.tick_events(5)
        assert 0 == self.board.get_current_player_id()


class TestMoving(TestCase):
    @pytest.fixture
    def before(self):
        self.board_controller = BoardController(0, 0, 500, 500)
        self.model = self.board_controller.model
        self.board: Board = self.model.board
        self.precombat_window = self.board_controller.precombat_window
        self.publisher = Publisher()
        EventQueue.set_publisher(self.publisher)
        self.roman = self.board.monster_at(roman_start_pos)

    def move_roman_left(self):
        self.board_controller.handle_tile_selection(roman_start_pos)
        self.board_controller.handle_tile_selection(left_of_roman_start_pos)

    def test_move_roman_left(self, before):
        roman = self.board.monster_at(roman_start_pos)
        assert roman_start_pos == roman.pos
        self.move_roman_left()
        assert left_of_roman_start_pos == roman.pos
        assert self.roman == self.board.monster_at(left_of_roman_start_pos)
        assert None is self.board.monster_at(roman_start_pos)

    def test_cannot_move_twice_on_same_turn(self, before):
        self.move_roman_left()
        self.board_controller.handle_tile_selection(left_of_roman_start_pos)
        self.board_controller.handle_tile_selection(roman_start_pos)
        assert left_of_roman_start_pos == self.roman.pos

    def test_move_for_two_turns(self, before):
        self.move_roman_left()
        self.end_turn()
        assert 0 == self.board.get_current_player_id()
        # now move back to starting position
        self.board_controller.handle_tile_selection(left_of_roman_start_pos)
        self.board_controller.handle_tile_selection(roman_start_pos)
        assert self.roman.pos == roman_start_pos


class TestAttacking(TestCase):
    @pytest.fixture
    def before(self):
        self.board_controller = BoardController(0, 0, 500, 500)
        self.model = self.board_controller.model
        self.board: Board = self.model.board
        self.precombat_window = self.board_controller.precombat_window
        self.publisher = Publisher()
        EventQueue.set_publisher(self.publisher)
        self.roman = self.board.monster_at(roman_start_pos)
        self.crusader = self.board.monster_at(crusader_start_pos)

    def attack_chimera(self):
        self.board_controller.handle_tile_selection(roman_start_pos)
        self.board_controller.handle_tile_selection(next_to_chimera_pos)
        self.board_controller.handle_tile_selection(chimera_pos)
        assert self.precombat_window.visible
        self.precombat_window.short_range_button.handle_mouseclick()
        assert not self.precombat_window.visible
        assert self.board_controller.combat_window.visible
        self.tick_events()
        self.board_controller.combat_window.handle_mouseclick()
        self.tick_events()
        assert not self.board_controller.combat_window.visible

    def test_attack_chimera(self, before):
        assert 0 == self.roman.exp
        self.attack_chimera()
        assert 1 == self.roman.exp

    def test_cannot_attack_from_distance(self, before):
        self.board_controller.handle_tile_selection(roman_start_pos)
        self.board_controller.handle_tile_selection(chimera_pos)
        assert not self.board_controller.precombat_window.visible

    def test_cannot_move_after_attacking(self, before):
        self.attack_chimera()
        self.board_controller.handle_tile_selection(next_to_chimera_pos)
        self.board_controller.handle_tile_selection(roman_start_pos)
        assert next_to_chimera_pos == self.roman.pos

    def test_cannot_select_and_move_after_attacking(self, before):
        self.attack_chimera()
        self.board_controller.handle_tile_selection(next_to_chimera_pos)
        self.board_controller.handle_tile_selection(left_of_roman_start_pos)
        assert next_to_chimera_pos == self.roman.pos

    def test_attack_without_moving(self, before):
        self.board_controller.handle_tile_selection(roman_start_pos)
        self.board_controller.handle_tile_selection(next_to_chimera_pos)
        self.board_controller.handle_tile_selection(next_to_chimera_pos)
        assert not self.precombat_window.visible
        assert 0 == self.roman.exp
        self.end_turn()
        self.board_controller.handle_tile_selection(next_to_chimera_pos)
        self.board_controller.handle_tile_selection(chimera_pos)
        assert self.precombat_window.visible
        self.precombat_window.short_range_button.handle_mouseclick()
        assert not self.precombat_window.visible
        assert self.board_controller.combat_window.visible
        self.tick_events()
        assert 0 == self.roman.exp
        self.board_controller.combat_window.handle_mouseclick()
        self.tick_events()
        assert not self.board_controller.combat_window.visible
        assert 1 == self.roman.exp

    def test_attack_then_move_next_turn(self, before):
        # derived from bug
        # attack with one monster then move with other, move again next turn
        self.attack_chimera()
        self.board_controller.handle_tile_selection(crusader_start_pos)
        self.board_controller.handle_tile_selection(crusader_south_once)
        assert crusader_south_once == self.crusader.pos
        self.end_turn()
        self.board_controller.handle_tile_selection(crusader_south_once)
        self.board_controller.handle_tile_selection(crusader_south_twice)
        assert crusader_south_once != self.crusader.pos
        assert crusader_south_twice == self.crusader.pos


class TestSummoning(TestCase):
    def test_summon_monster(self, before):
        left_of_daimyou = self.board.tile_at(left_of_daimyou_pos)
        assert None is left_of_daimyou.monster
        # open summon window
        self.board_controller.handle_tile_selection(left_of_daimyou_pos)
        summon_window = self.board_controller.summon_window
        assert summon_window.visible

        # make summon choice
        summon_window.handle_summon_choice(0)
        assert False is summon_window.visible
        summoned_monster = left_of_daimyou.monster
        assert summoned_monster
        assert MonsterType.DRAGON_DY == summoned_monster.type
        assert summoned_monster.moved

    def test_cannot_summon_far_away(self, before):
        far_left_of_daimyou = self.board.tile_at(far_left_of_daimyou_pos)
        assert None is far_left_of_daimyou.monster
        # open summon window
        self.board_controller.handle_tile_selection(far_left_of_daimyou_pos)
        assert not self.board_controller.summon_window.visible

    def test_cannot_summon_on_top_of_monster(self, before):
        # create monsters left and right to daimyou
        assert None is self.board.monster_at(left_of_daimyou_pos)
        self.board.place_new_monster(
            MonsterType.CYCLOPS, left_of_daimyou_pos, 0)
        self.board.place_new_monster(
            MonsterType.PEGASUS, right_of_daimyou_pos, 1)
        assert self.board.monster_at(left_of_daimyou_pos)
        assert self.board.monster_at(right_of_daimyou_pos)
        # try summon monster left and right of daimyou
        left_of_daimyou = self.board.tile_at(left_of_daimyou_pos)
        assert left_of_daimyou.monster
        self.board_controller.handle_tile_selection(left_of_daimyou_pos)
        assert not self.board_controller.summon_window.visible
        self.board_controller.handle_tile_selection(right_of_daimyou_pos)
        assert not self.board_controller.summon_window.visible


class TestTowerCapture(TestCase):
    def before_more(self):
        self.crusader = self.board.monster_at(crusader_start_pos)
        self.tower_tile = self.board.tile_at(tower_pos)

    def test_tower_capture(self, before):
        self.move_crusader_to_tower()
        assert self.board_controller.tower_capture_window.visible
        # now wait for window animation
        self.tick_events(300)
        # then after a while the window should be gone
        self.assert_tower_captured_by(self.crusader)

    def test_tower_capture_close_window(self, before):
        self.move_crusader_to_tower()
        assert self.board_controller.tower_capture_window.visible
        # close window before_zigzag animation finishes
        self.board_controller.tower_capture_window.handle_mouseclick()
        # now window should be closed
        self.assert_tower_captured_by(self.crusader)

    def test_capture_by_enemy(self, before):
        # set enemy AI to human
        enemy = self.board_controller.model.players.get_player_by_id(1)
        enemy.ai_type = AiType.human
        # create enemy unit
        enemy_pos = (3, 3)
        roc = self.board.summon_monster(MonsterType.LOC, enemy_pos, 1)
        # player 1 turn
        self.move_crusader_to_tower()
        self.board_controller.tower_capture_window.handle_mouseclick()
        self.assert_tower_captured_by(self.crusader)
        self.end_turn()
        # player 2 turn
        self.end_turn()
        # player 1 turn: move away from tower
        self.board_controller.handle_tile_selection(tower_pos)
        self.board_controller.handle_tile_selection(crusader_start_pos)
        self.end_turn()
        # player 2 turn: move to to tower
        self.board_controller.handle_tile_selection(enemy_pos)
        self.board_controller.handle_tile_selection(tower_pos)
        self.assert_tower_captured_by(roc)
        assert 0 == self.model.players.get_player_by_id(0).tower_count

    def move_crusader_to_tower(self):
        crusader = self.board.monster_at(crusader_start_pos)
        tower_tile = self.board.tile_at(tower_pos)
        self.move_monster_to_tile(crusader, tower_tile)
        # now monster has to walk there
        self.tick_events(30)
        # then window should be visible
        return crusader, tower_tile

    def assert_tower_captured_by(self, monster):
        assert not self.board_controller.tower_capture_window.visible
        assert monster == self.board.monster_at(tower_pos)
        assert monster.owner == self.board.terrain_owner_of(tower_pos)
        player = self.model.players.get_player_by_id(monster.owner)
        assert 1 == player.tower_count


class TestComputerBrain(TestCase):
    def before_more(self):
        pass

    def test_move_action(self):
        action = self.model.get_brain_action()
        self.model.execute_brain_action()


class TestTileEditor(TestCase):
    def before_more(self):
        self.tile_editor: TileEditorWindow = \
            self.board_controller.tile_editor_window
        self.buttons: TileEditorButtons = self.tile_editor.buttons

    def test_set_main_fortress(self, before):
        tile_pos = (0, 0)
        assert None is self.tile_editor.selected_terrain
        self.buttons._handle_button_click(0)
        assert Terrain.MAIN_FORTRESS == self.tile_editor.selected_terrain
        assert Terrain.GRASS == self.board.terrain_at(tile_pos)
        self.board_controller.handle_tile_selection(tile_pos)
        assert Terrain.MAIN_FORTRESS == self.board.terrain_at(tile_pos)

    def test_button_off(self, before):
        tile_pos = (0, 0)
        assert None is self.tile_editor.selected_terrain
        self.buttons._handle_button_click(0)
        assert Terrain.MAIN_FORTRESS == self.tile_editor.selected_terrain
        # now turn button off
        self.buttons._handle_button_click(0)
        assert None is self.tile_editor.selected_terrain
        assert Terrain.GRASS == self.board.terrain_at(tile_pos)
        self.board_controller.handle_tile_selection(tile_pos)
        assert Terrain.GRASS == self.board.terrain_at(tile_pos)
