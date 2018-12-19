import pytest

from src.components.board.brain import PlayerDefaultBrain, PlayerIdleBrain
from src.components.board.monster import Monster
from src.controller.board_controller import BoardController
from src.controller.mainmenu_controller import MapOptions
from src.helper.Misc.constants import Terrain, MonsterBehavior
from src.helper.Misc.options_game import Options
from src.helper.events.events import EventList, EventQueue

Options.headless = True


class PlayerNoSummonBrain(PlayerDefaultBrain):
    def _handle_summon(self):
        """Doesn't summon anything so the set of monsters remains the same"""
        self.did_action = False


class PlayerScoutBrain(PlayerNoSummonBrain):
    """Only makes scouts"""

    def _create_brain_for_monster(self, monster):
        super()._create_brain_for_monster(monster)
        monster.brain.type = MonsterBehavior.SCOUT


class PlayerAttackerBrain(PlayerNoSummonBrain):
    """Only makes attackers"""

    def _create_brain_for_monster(self, monster):
        super()._create_brain_for_monster(monster)
        monster.brain.type = MonsterBehavior.ATTACKER


class PlayerDefenderBrain(PlayerNoSummonBrain):
    """Only makes attackers"""

    def _create_brain_for_monster(self, monster):
        super()._create_brain_for_monster(monster)
        monster.brain.type = MonsterBehavior.DEFENDER


class PlayerSummonBrain(PlayerDefaultBrain):
    """Only summons monsters, doesn't move them"""

    def _handle_monsters(self):
        pass


class AiType:
    (human, idle, default, scout, attacker, defender, summoner) = range(7)


class TestCase:
    # noinspection PyAttributeOutsideInit
    @pytest.fixture
    def before(self):
        mapoptions = MapOptions()
        mapoptions.mapname = 'testempty.map'
        mapoptions.set_number_of_players(2)
        self.controller = BoardController(0, 0, 500, 500, mapoptions)
        self.model = self.controller.model
        self.board = self.model.board
        self.publisher = EventQueue()
        EventList.set_publisher(self.publisher)
        # move lords away
        for n in range(2):
            monsters = self.model.get_monsters_of_player(n)
            for monster in monsters:
                self.board.set_monster_pos(monster, (18 + n, 0))
        self.add_chim()
        self.before_more()

    def tick_event(self, times=1):
        for _ in range(times):
            self.publisher.tick_events()

    def before_more(self):
        # override this for extra before options
        pass

    def skip_x_turns(self, x):
        for _ in range(x):
            self.model.on_end_turn()

    def set_ai_type(self, ai_type):
        player = self.model.get_player_of_number(1)
        player.ai_type = ai_type
        if ai_type == AiType.idle:
            brain_class = PlayerIdleBrain
        elif ai_type == AiType.scout:
            brain_class = PlayerScoutBrain
        elif ai_type == AiType.attacker:
            brain_class = PlayerAttackerBrain
        elif ai_type == AiType.defender:
            brain_class = PlayerDefenderBrain
        elif ai_type == AiType.summoner:
            brain_class = PlayerSummonBrain
        elif ai_type == AiType.default:
            brain_class = PlayerDefaultBrain
        else:
            assert False, f'invalid ai type {ai_type}'
        self.controller.add_brain_for_player(brain_class, player)

    def summon_monster_at(self, pos):
        return self.board.summon_monster(Monster.Type.TROLL, pos, 0)

    def create_tower_at(self, pos, owner=None):
        self.board.on_tile(pos).set_terrain_to(Terrain.TOWER)
        if owner is not None:
            self.board.capture_terrain_at(pos, owner)

    def add_chim(self):
        # remove all monsters but lord and chim
        # noinspection PyAttributeOutsideInit
        self.chim = self.board.summon_monster(Monster.Type.CHIMERA, (3, 3), 1)
        self.chim.moved = False

    def ensure_player_x_turn(self, number):
        assert self.board.get_current_player_id() == number

    def end_turn(self):
        self.controller.end_of_turn_window.yes.handle_mouseclick()
        # the ai doesn't act until next event
        self.tick_event()

    def check_move_action(self, pos):
        self.end_turn()
        assert self.board.monster_at(pos) == self.chim, \
            f'Monster was at {self.chim.pos} instead of {pos} \
              {self.board.debug_print()}'

    def set_mana_of_player_to(self, player_id, mana):
        self.model.get_player_of_number(player_id).mana = mana


class TestIdleBrain(TestCase):
    def test_idle_ai_turns(self, before):
        self.set_ai_type(AiType.idle)
        self.end_turn()
        self.ensure_player_x_turn(0)


class TestScoutBrain(TestCase):
    def before_more(self):
        # set the player to scout and create brain for it
        self.set_ai_type(AiType.scout)

    def test_move_to_nearby_tower(self, before):
        # Set tower next to monster
        closest_tower_pos = (self.chim.pos[0], self.chim.pos[1] - 2)
        self.create_tower_at(closest_tower_pos)
        self.check_move_action(closest_tower_pos)

    def test_move_toward_far_tower(self, before):
        # add tower far from chim
        self.create_tower_at((15, 3))
        # with 5 move points, the chim can move to the following pos:
        self.check_move_action((8, 3))

    def test_move_to_closest_tower(self, before):
        # Set tower next to monster
        closest_tower_pos = (5, self.chim.pos[1] - 3)
        # move monster closer to both
        self.create_tower_at(closest_tower_pos)
        # closest tower is the one we made, so monster goes south
        self.check_move_action(closest_tower_pos)

    def test_ignore_occupied_tower(self, before):
        closest_tower_pos = (0, 3)
        self.create_tower_at(closest_tower_pos)
        self.summon_monster_at(closest_tower_pos)
        # scout should ignore this tower and go for the other one
        other_tower_pos = (7, 4)
        self.create_tower_at(other_tower_pos)
        self.check_move_action(other_tower_pos)

    def test_monster_keeps_moving(self, before):
        self.board.set_monster_pos(self.chim, (0, 12))
        self.create_tower_at((0, 0))
        old_pos = self.chim.pos
        self.end_turn()  # start AI turn
        new_pos = self.chim.pos
        assert new_pos != old_pos
        self.ensure_player_x_turn(1)
        self.tick_event(120)
        self.tick_event()
        self.ensure_player_x_turn(0)
        self.end_turn()
        assert self.chim.pos != new_pos


class TestAttackerBrain(TestCase):
    def before_more(self):
        # set the player to attacker and create brain for it
        self.set_ai_type(AiType.attacker)
        self.enemy_fortress = (8, 3)
        self.board.on_tile(self.enemy_fortress).set_terrain_to(
            Terrain.MAIN_FORTRESS)
        self.board.capture_terrain_at(self.enemy_fortress, 0)

    def test_go_to_enemy_tower(self, before):
        # let's create a tower and set owner to the enemy
        enemy_tower_pos = (0, 0)
        self.create_tower_at(enemy_tower_pos, 0)
        # also create a tower that is self-owned, this should be ignored
        own_tower_pos = (3, 0)
        self.create_tower_at(own_tower_pos, 1)
        self.check_move_action(enemy_tower_pos)

    def test_choose_between_towers(self, before):
        # it should always grab the enemy fortress over the tower

        # x-pos has multiple valid option, y-should always be 12
        self.check_move_action(self.enemy_fortress)

    def test_attack_monster_on_tower(self, before):
        tower_location = (6, 0)
        self.create_tower_at(tower_location, 0)
        self.summon_monster_at(tower_location)
        self.board.set_monster_pos(self.chim, (4, 0))


class TestDefenderBrain(TestCase):
    def before_more(self):
        # set the player to scout and create brain for it
        self.set_ai_type(AiType.defender)

    def test_go_to_owned_tower(self, before):
        # capture tower for self
        tower_location = (0, 0)
        self.create_tower_at(tower_location, 1)
        self.check_move_action(tower_location)

    def test_ignore_enemy_tower(self, before):
        # defend own tower
        enemy_tower_location = (1, 1)
        self.create_tower_at(enemy_tower_location, 0)
        tower_location = (6, 0)
        self.create_tower_at(tower_location, 1)
        self.check_move_action(tower_location)


class TestSummonBrain(TestCase):
    def before_more(self):
        self.wizard = self.board.lords[1]
        self.board.set_monster_pos(self.wizard, (1, 1))
        self.set_ai_type(AiType.summoner)

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


class TestDefaultBrain(TestCase):
    def before_more(self):
        self.set_ai_type(AiType.default)
        self.create_tower_at((19, 19))
        self.create_tower_at((17, 19))

    def test_ai_doesnt_lock_up_the_game(self, before):
        self.end_turn()
        self.tick_event(200)

    def test_move_two_monsters(self, before):
        # make AI move to the tower created
        self.set_mana_of_player_to(1, 0)  # prevents summoning
        self.add_troll()
        self.set_ai_type(AiType.scout)
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


def assert_new_pos(monster, old_monster_pos):
    assert monster.pos != old_monster_pos, f'monster still at {monster.pos}'
