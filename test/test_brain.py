import logging

import pytest

from src.components.board.brain import PlayerDefaultBrain, PlayerIdleBrain
from src.components.board.monster import Monster
from src.controller.board_controller import BoardController
from src.controller.mainmenu_controller import MapOptions
from src.helper.Misc.constants import Terrain, MonsterBehavior
from src.helper.Misc.options_game import Options
from src.helper.events.events import EventList, EventQueue

Options.headless = True

chim_start_pos = (3, 3)


class AiType:
    (human, idle, default) = range(3)


class TestCase:
    # noinspection PyAttributeOutsideInit
    @pytest.fixture
    def before(self):
        mapoptions = MapOptions()
        mapoptions.mapname = 'testempty.map'
        mapoptions.set_number_of_players(2)
        mapoptions.set_players()
        self.controller = BoardController(0, 0, 500, 500, mapoptions)
        self.model = self.controller.model
        assert len(self.model.players) == 2
        self.board = self.model.board
        self.publisher = EventQueue()
        EventList.set_publisher(self.publisher)
        # put lords in corners
        daimyou = self.board.lords[0]
        self.board.set_monster_pos(daimyou, (19, 0))
        wizard = self.board.lords[1]
        self.board.set_monster_pos(wizard, (19, 19))
        self.add_chim()
        self.before_more()

    def before_more(self):
        # override this for extra before options
        pass

    def tick_event(self, times=1):
        for _ in range(times):
            self.publisher.tick_events()

    def skip_x_turns(self, x):
        for _ in range(x):
            self.model.on_end_turn()

    def set_ai_type(self, ai_type):
        player = self.model.get_player_of_number(1)
        player.ai_type = ai_type
        if ai_type == AiType.idle:
            brain_class = PlayerIdleBrain
        elif ai_type == AiType.default:
            brain_class = PlayerDefaultBrain
        else:
            assert False, f'invalid ai type {ai_type}'
        self.controller.add_brain_for_player(brain_class, player)

    def create_tower_at(self, pos, owner=None):
        self.board.set_terrain_to(pos, Terrain.TOWER)
        if owner is not None:
            self.board.capture_terrain_at(pos, owner)

    def add_chim(self):
        # remove all monsters but lord and chim
        # noinspection PyAttributeOutsideInit
        self.chim = self.board.place_new_monster(
            Monster.Type.CHIMERA, chim_start_pos, 1)

    def summon_troll_at(self, pos):
        return self.summon_monster_at(Monster.Type.TROLL, pos)

    def ensure_player_x_turn(self, number):
        assert self.board.get_current_player_id() == number, (
            f'It is still player {self.board.get_current_player_id()}\'s turn')

    def end_turn(self):
        self.controller.end_of_turn_window.yes.handle_mouseclick()
        # the ai doesn't act until next event
        self.tick_event()

    def check_move_action(self, pos):
        self.end_turn()
        self.check_chim_pos(pos)

    def set_mana_of_player_to(self, player_id, mana):
        self.model.get_player_of_number(player_id).mana = mana

    def set_chim_pos(self, pos):
        self.board.set_monster_pos(self.chim, pos)

    def check_chim_pos(self, pos):
        assert self.chim.pos == pos, \
            f'Monster was at {self.chim.pos} instead of {pos} \
                      {self.board.debug_print()}'

    def summon_monster_at(self, type_, pos):
        monster = self.board.place_new_monster(type_, pos, 0)
        assert monster is not None
        return monster


class TestIdleBrain(TestCase):
    def test_idle_ai_turns(self, before):
        self.set_ai_type(AiType.idle)
        self.end_turn()
        self.ensure_player_x_turn(0)


class TestMoveToNearbyTarget(TestCase):
    def test_move_to_nearby_tower(self, before):
        # Add tower next to monster
        closest_tower_pos = (chim_start_pos[0], chim_start_pos[1] - 2)
        self.create_tower_at(closest_tower_pos)
        self.check_move_action(closest_tower_pos)

    def test_move_to_closest_tower(self, before):
        # Add tower next to monster
        closest_tower_pos = (chim_start_pos[0] + 2, chim_start_pos[1] - 3)
        self.create_tower_at(closest_tower_pos)
        # Add tower a bit further away
        self.create_tower_at(
            (chim_start_pos[0] + 3, chim_start_pos[1] - 3))
        # check if monster went to closest tower
        self.check_move_action(closest_tower_pos)

    def test_move_to_enemy_lord(self, before):
        # no tower so chim will move next to daimyou
        self.set_chim_pos((16, 0))
        self.check_move_action((18, 0))


class TestHandleNearbyEnemy(TestCase):
    def test_attack_weakened_monster(self, before):
        dragon_pos = (5, 3)
        self.summon_weakened_dragon_at(dragon_pos)
        self.end_turn()
        self.tick_event(5000)
        self.ensure_player_x_turn(0)
        self.check_chim_pos((4, 3))
        self.ensure_monster_is_dead(dragon_pos)
        self.end_turn()

    def test_ignore_phys_immune_monster(self, before):
        # ignore this monster because chim's attacks are ineffective
        wraith_pos = (5, 3)
        self.summon_wraith_at(wraith_pos)
        self.end_turn()
        self.tick_event(200)
        self.ensure_player_x_turn(0)
        self.check_chim_pos((7, 0))

    def test_attack_other_chim(self, before):
        other_chim_pos = (5, 3)
        self.summon_chim_at(other_chim_pos)
        self.end_turn()
        self.tick_event(5000)
        self.ensure_player_x_turn(0)
        self.check_chim_pos((4, 3))

    def ensure_monster_is_dead(self, pos):
        assert self.board.monster_at(pos) is None

    def summon_weakened_dragon_at(self, pos):
        dragon = self.summon_dragon_at(pos)
        dragon.hp = 1

    def summon_dragon_at(self, pos):
        return self.summon_monster_at(Monster.Type.KING_D, pos)

    def summon_wraith_at(self, pos):
        self.summon_monster_at(Monster.Type.BLACK_W, pos)

    def summon_chim_at(self, pos):
        self.summon_monster_at(Monster.Type.CHIMERA, pos)


class TestMoveToFarTower(TestCase):
    def test_move_toward_far_tower(self, before):
        # add tower far from chim
        self.create_tower_at((15, 3))
        # with 5 move points, the chim can move to the following pos:
        self.check_move_action((8, 3))

    def test_towards_lord(self, before):
        """don't add tower so chim will move to lord"""
        self.check_if_pos_changes_over_2_turns()
        self.check_chim_pos((chim_start_pos[0] + 9, 0))

    def test_move_towards_tower_for_two_turns(self, before):
        self.create_tower_at((0, 0))
        self.board.set_monster_pos(self.chim, (0, 12))
        self.check_if_pos_changes_over_2_turns()

    def check_if_pos_changes_over_2_turns(self):
        self.end_turn()  # start AI turn
        new_pos = self.chim.pos
        assert new_pos != chim_start_pos
        self.ensure_player_x_turn(1)
        self.tick_event(120)
        self.ensure_player_x_turn(0)
        self.end_turn()
        assert self.chim.pos != new_pos


class TestWithTwoTowers(TestCase):
    def before_more(self):
        # set the player to attacker and create brain for it
        self.tower = (8, 3)
        self.board.on_tile(self.tower).set_terrain_to(Terrain.TOWER)

    def test_go_to_enemy_tower(self, before):
        # let's create a tower and set owner to the enemy
        enemy_tower_pos = (0, 0)
        self.create_tower_at(enemy_tower_pos, 0)
        # also create a tower that is self-owned, this should be ignored
        own_tower_pos = (3, 0)
        self.create_tower_at(own_tower_pos, 1)
        self.check_move_action(enemy_tower_pos)

    def test_attack_monster_on_tower(self, before):
        # there is an enemy on top of the tower
        self.summon_troll_at(self.tower)
        # monster is almost dead, easy target
        self.board.monster_at(self.tower).hp = 1
        # chim should move next so it can attack it
        left_of_tower = (self.tower[0] - 5, self.tower[1])
        next_to_tower = (self.tower[0] - 1, self.tower[1])
        self.board.set_monster_pos(
            self.chim, left_of_tower)
        self.check_move_action(next_to_tower)

    def test_go_to_enemy_lord(self, before):
        # tower is owned so now the only target is player 0's lord
        old_chim_pos = self.chim.pos
        self.board.capture_terrain_at(self.tower, 1)
        self.check_move_action((old_chim_pos[0] + 4, old_chim_pos[1] - 3))


class TestSummoning(TestCase):
    def before_more(self):
        self.wizard = self.board.lords[1]
        self.board.set_monster_pos(self.wizard, (1, 1))
        self.chim.moved = True

    def test_summon_monsters(self, before):
        self.set_mana_of_player_to(1, 220)
        monsters = self.get_monsters_after_turn()
        assert len(monsters) > 2

    def test_no_mana_to_summon(self, before):
        self.set_mana_of_player_to(1, 0)
        monsters = self.get_monsters_after_turn()
        assert len(monsters) == 2

    def test_summon_6_monsters_on_single_turn(self, before):
        self.set_mana_of_player_to(1, 1000)
        monsters = self.get_monsters_after_turn()
        assert len(monsters) == 8

    def test_summon_monsters_on_map_edge(self, before):
        self.set_mana_of_player_to(1, 1000)
        self.board.set_monster_pos(self.wizard, (0, 1))
        monsters = self.get_monsters_after_turn()
        # should be 5 + chim and wizard
        assert len(monsters) == 7

    def get_monsters_after_turn(self):
        monsters = self.model.get_monsters_of_player(1)
        assert len(monsters) == 2, f'Player 1 has {len(monsters)} monsters'
        self.end_turn()
        self.tick_event(10)  # give time to summon
        self.ensure_player_x_turn(0)
        return self.model.get_monsters_of_player(1)


class TestTwoMonsters(TestCase):
    def before_more(self):
        self.create_tower_at((19, 19))
        self.create_tower_at((17, 19))

    def test_move_two_monsters(self, before):
        # make AI move to the tower created
        self.set_mana_of_player_to(1, 0)  # prevents summoning
        self.add_troll()

        self.check_if_ai_monsters_move_after_ending_turn()
        self.check_if_ai_monsters_move_after_ending_turn()

    def check_if_ai_monsters_move_after_ending_turn(self):
        old_troll_pos = self.troll.pos
        old_chim_pos = self.chim.pos
        self.ensure_player_x_turn(0)
        self.end_turn()
        self.ensure_player_x_turn(1)
        self.tick_event(90)  # wait for monsters to move
        assert_new_pos(self.chim, old_chim_pos)
        assert_new_pos(self.troll, old_troll_pos)

    def add_troll(self):
        # noinspection PyAttributeOutsideInit
        self.troll = self.board.summon_monster(Monster.Type.TROLL, (2, 2), 1)
        self.troll.moved = False


class TestHandleEnemy(TestCase):
    def test_ignore_occupied_tower(self, before):
        # create tower and put enemy on it
        closest_tower_pos = (0, 3)
        self.create_tower_at(closest_tower_pos)
        self.summon_troll_at(closest_tower_pos)
        # monster should be next to closest tower
        other_tower_pos = (7, 4)
        self.create_tower_at(other_tower_pos)
        next_to_closest_tower = (closest_tower_pos[0] + 1, closest_tower_pos[1])
        self.check_move_action(next_to_closest_tower)


class TestNormalScenario(TestCase):
    def before_more(self):
        self.create_tower_at((19, 19))
        self.create_tower_at((17, 19))

    def test_ai_doesnt_lock_up_the_game(self, before):
        self.end_turn()
        self.tick_event(200)
        self.ensure_player_x_turn(0)


def assert_new_pos(monster, old_monster_pos):
    assert monster.pos != old_monster_pos, f'monster still at {monster.pos}'
