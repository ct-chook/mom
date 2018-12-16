import pytest

from src.components.board.brain import PlayerDefaultBrain, PlayerIdleBrain
from src.components.board.monster import Monster
from src.controller.board_controller import BoardController
from src.helper.Misc.constants import Terrain, MonsterBehavior
from src.helper.events.events import EventList, EventQueue
from test.controllers.test_board_controller import chim_start_pos


class PlayerScoutBrain(PlayerDefaultBrain):
    """Only makes scouts"""

    def _create_brain_for_monster(self, monster):
        super()._create_brain_for_monster(monster)
        monster.brain.type = MonsterBehavior.SCOUT


class PlayerAttackerBrain(PlayerDefaultBrain):
    """Only makes attackers"""

    def _create_brain_for_monster(self, monster):
        super()._create_brain_for_monster(monster)
        monster.brain.type = MonsterBehavior.ATTACKER


class PlayerDefenderBrain(PlayerDefaultBrain):
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
        self.controller = BoardController(0, 0, 500, 500, 'testempty.map')
        self.model = self.controller.model
        self.board = self.model.board
        self.before_more()
        self.publisher = EventQueue()
        EventList.set_publisher(self.publisher)
        self.add_chim()

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
        brain_class = None
        if ai_type == AiType.idle:
            brain_class = PlayerIdleBrain
        if ai_type == AiType.scout:
            brain_class = PlayerScoutBrain
        elif ai_type == AiType.attacker:
            brain_class = PlayerAttackerBrain
        elif ai_type == AiType.defender:
            brain_class = PlayerDefenderBrain
        elif ai_type == AiType.summoner:
            brain_class = PlayerSummonBrain
        self.controller.add_brain_for_player(brain_class, player)

    def summon_monster_at(self, pos):
        return self.board.summon_monster(Monster.Type.TROLL, pos, 0)

    def create_tower_at(self, pos, owner=None):
        self.board.on_tile(pos).set_terrain_to(Terrain.TOWER)
        if owner is not None:
            self.board.capture_terrain_at(pos, owner)

    def add_chim(self):
        # remove all monsters but lord and chim
        self.chim = self.board.summon_monster(Monster.Type.CHIMERA, (3, 3), 1)
        self.chim.moved = False

    def ensure_player_0s_turn(self):
        assert self.board.get_current_player_id() == 0

    def end_turn(self):
        self.controller.end_of_turn_window.yes.handle_mouseclick()

    def check_move_action(self, pos):
        self.end_turn()
        assert self.board.monster_at(pos) == self.chim, \
            f'Monster was at {self.chim.pos} instead of {pos} \
              {self.board.debug_print()}'


class TestIdleBrain(TestCase):
    def test_idle_ai_turns(self, before):
        self.set_ai_type(AiType.idle)
        self.end_turn()
        self.ensure_player_0s_turn()


class TestScoutBrain(TestCase):
    def before_more(self):
        # set the player to scout and create brain for it
        self.set_ai_type(AiType.scout)

    def test_monster_keeps_moving(self, before):
        self.board.set_monster_pos(self.chim, (0, 12))
        self.create_tower_at((0, 0))
        old_pos = self.chim.pos
        self.board.debug_print()
        self.end_turn()  # start AI turn
        self.board.debug_print()
        new_pos = self.chim.pos
        assert new_pos != old_pos
        self.ensure_player_0s_turn()
        self.end_turn()
        self.board.debug_print()
        assert self.chim.pos != new_pos

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
        self.board.debug_print()
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
        self.set_ai_type(AiType.summoner)

    def test_summon_monster(self, before):
        self.model.get_current_player().mana = 200

    def test_no_mana_to_summon(self, before):
        self.model.get_current_player().mana = 0
