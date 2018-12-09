import pytest

from src.components.board import board
from src.components.board.brain import PlayerDefaultBrain, PlayerIdleBrain
from src.components.board.monster import Monster
from src.helper.Misc.constants import Terrain, Range, MonsterBehavior
from src.model.board_model import BoardModel


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
    """Only summons monsters"""

    def _handle_monsters(self):
        pass


class AiType:
    (human, idle, default, scout, attacker, defender, summoner) = range(7)


class TestCase:
    @pytest.fixture
    def before(self):
        self.model = BoardModel()
        self.board: board.Board = self.model.board
        self.action = None
        self.monster = None
        self.before_more()

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
        player.create_brain_from_class(brain_class, self.model)

    def summon_monster_at(self, pos):
        return self.board.summon_monster(Monster.Type.TROLL, pos, 0)

    def create_tower_at(self, pos, owner=None):
        self.board.on_tile(pos).set_terrain_to(Terrain.TOWER)
        if owner is not None:
            self.board.capture_terrain_at(pos, owner)

    def check_move_action(self, monster, pos):
        self.get_action()
        assert self.action.monster_to_move == monster, \
            f'{self.board.debug_print()}'
        assert self.action.pos_to_move == pos, f'{self.board.debug_print()}'
        assert self.action.monster_to_attack is None

    def check_attack_action(self, attacker, defender, attack_range):
        self.get_action()
        assert self.action.monster_to_move is attacker, \
            f'{self.board.debug_print()}'
        # assert self.action.pos_to_move == pos, f'{self.board.debug_print()}'
        assert self.action.monster_to_attack == defender
        assert self.action.range_to_use == attack_range

    def get_action(self):
        self.action = self.model.get_brain_action()

    def test_class(self):
        pass


class TestIdleBrain(TestCase):
    def test_idle_brain(self, before):
        self.set_ai_type(AiType.idle)
        self.skip_x_turns(1)  # go to 2nd player, idle AI
        action = self.model.get_brain_action()
        assert action.end_turn

    def test_error_on_human_action(self, before):
        with pytest.raises(AttributeError):
            self.model.get_brain_action()


class TestScoutBrain(TestCase):
    def before_more(self):
        # set the player to scout and create brain for it
        self.set_ai_type(AiType.scout)
        self.skip_x_turns(1)  # go to 2nd player, idle AI
        self.monster = self.model.get_current_player_monsters()[0]

    def test_action_gives_move_event(self, before):
        action = self.model.get_brain_action()
        assert action.monster_to_move, f'{self.board.debug_print()}'
        assert action.pos_to_move, f'{self.board.debug_print()}'

    def test_move_to_nearby_tower(self, before):
        # Set tower next to monster
        assert self.monster
        closest_tower_pos = (self.monster.pos[0], self.monster.pos[1] - 2)
        self.create_tower_at(closest_tower_pos)
        self.check_move_action(self.monster, closest_tower_pos)

    def test_move_to_far_tower(self, before):
        # Set tower next to monster
        assert self.monster.stats.move_points == 5
        # with 5 move points, the chim can move to the following pos:
        closest_tower_pos = (2, 12)
        self.check_move_action(self.monster, closest_tower_pos)

    def test_move_to_closest_tower(self, before):
        # Set tower next to monster
        closest_tower_pos = (self.monster.pos[0] + 8, self.monster.pos[1])
        # move monster closer to both
        old_pos = self.monster.pos
        self.board.set_monster_pos(self.monster, (old_pos[0], old_pos[1] - 4))
        self.create_tower_at(closest_tower_pos)
        # closest tower is the one we made, so monster goes south
        closest_tile_pos = (4, 17)
        self.check_move_action(self.monster, closest_tile_pos)

    def test_ignore_occupied_tower(self, before):
        closest_tower_pos = (2, self.monster.pos[1] - 2)
        self.create_tower_at(closest_tower_pos)
        self.summon_monster_at(closest_tower_pos)
        # scout should ignore this tower and go for further one
        self.action = self.model.get_brain_action()
        further_tower_pos = (0, 0)
        self.create_tower_at(further_tower_pos)
        assert self.action.pos_to_move[1] == 12


class TestAttackerBrain(TestCase):
    def before_more(self):
        # set the player to scout and create brain for it
        self.set_ai_type(AiType.attacker)
        self.skip_x_turns(1)  # go to 2nd player, idle AI
        self.monster = self.model.get_current_player_monsters()[0]
        # create enemy fortress
        self.enemy_fortress = (0, 0)
        self.board.on_tile(self.enemy_fortress). \
            set_terrain_to(Terrain.MAIN_FORTRESS)
        self.board.capture_terrain_at(self.enemy_fortress, 0)
        # remove enemies near chimera
        roman_pos = (1, 19)
        phoenix_pos = (1, 18)
        self.board.remove_monster_at(roman_pos)
        self.board.remove_monster_at(phoenix_pos)

    def test_go_to_enemy_tower(self, before):
        # let's create a tower and set owner to the enemy
        enemy_tower_pos = (self.monster.pos[0], self.monster.pos[1] - 4)
        self.create_tower_at(enemy_tower_pos, 0)
        # also create a tower that is self-owned, this should be ignored
        own_tower_pos = (self.monster.pos[0], self.monster.pos[1] - 3)
        self.create_tower_at(own_tower_pos, 1)
        self.check_move_action(self.monster, enemy_tower_pos)

    def test_no_enemy_towers(self, before):
        # now it should always grab the enemy fortress
        self.get_action()
        # x-pos has multiple valid option, y-should always be 12
        assert self.action.pos_to_move[1] == 12, \
            f'{self.board.debug_print()}'
        assert self.action.monster_to_move == self.monster, \
            f'{self.board.debug_print()}'

    def test_choose_between_towers(self, before):
        # remove fighter near tower
        fighter_pos = (5, 5)
        self.board.remove_monster_at(fighter_pos)
        # now it should always grab the enemy fortress over the tower
        self.board.set_monster_pos(self.monster, (5, 0))
        self.get_action()
        # x-pos has multiple valid option, y-should always be 12
        self.check_move_action(self.monster, self.enemy_fortress)

    def test_attack_monster_on_tower(self, before):
        tower_location = (6, 0)
        self.create_tower_at(tower_location, 0)
        defender = self.summon_monster_at(tower_location)
        self.board.set_monster_pos(self.monster, (4, 0))
        self.check_attack_action(self.monster, defender, Range.CLOSE)


class TestDefenderBrain(TestCase):
    def before_more(self):
        # set the player to scout and create brain for it
        self.set_ai_type(AiType.defender)
        self.skip_x_turns(1)  # go to 2nd player, idle AI
        self.monster = self.model.get_current_player_monsters()[0]
        # create own fortress
        self.enemy_fortress = (0, 0)
        self.board.on_tile(self.enemy_fortress). \
            set_terrain_to(Terrain.MAIN_FORTRESS)
        self.board.capture_terrain_at(self.enemy_fortress, 1)

    def test_go_to_owned_tower(self, before):
        # capture tower for self
        tower_location = (2, 13)
        self.create_tower_at(tower_location, 1)
        self.check_move_action(self.monster, tower_location)

    def test_ignore_enemy_tower(self, before):
        # capture tower for self
        tower_location = (6, 0)
        self.create_tower_at(tower_location, 0)
        self.board.move_monster(self.monster, (3, 3))
        self.check_move_action(self.monster, (0, 0))


class TestSummonBrain(TestCase):
    def before_more(self):
        self.set_ai_type(AiType.summoner)
        self.skip_x_turns(1)  # go to 2nd player, idle AI

    def test_summon_monster(self, before):
        self.model.get_current_player().mana = 200
        self.get_action()
        assert self.action.end_turn is False
        assert self.action.monster_to_summon is not None

    def test_no_mana_to_summon(self, before):
        self.model.get_current_player().mana = 0
        self.get_action()
        assert self.action.end_turn is True
        assert self.action.monster_to_summon is None
