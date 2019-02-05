import pytest

from abstract.controller import PublisherInjector
from components.board.board import Board
from helper.events.events import Publisher
from src.components.board.brain import PlayerDefaultBrain, PlayerIdleBrain
from src.components.board.monster import Monster
from src.components.combat.combat import Combat
from src.controller.board_controller import BoardController
from src.controller.mainmenu_controller import MapOptions
from src.helper.Misc.constants import Terrain, AiType
from src.helper.Misc.options_game import Options

Options.headless = True
Combat.perfect_accuracy = True

Type = Monster.Type
chim_start_pos = (3, 3)


class TestCase:
    # noinspection PyAttributeOutsideInit
    @pytest.fixture
    def before(self):
        mapoptions = MapOptions()
        mapoptions.mapname = 'testempty.map'
        mapoptions.set_number_of_players(2)
        mapoptions.create_players()
        self.controller = BoardController(0, 0, 500, 500, mapoptions)
        self.publisher = Publisher()
        PublisherInjector(self.controller).inject(self.publisher)
        self.model = self.controller.model
        assert self.model.get_player_of_number(1).ai_type != AiType.human
        assert len(self.model.players) == 2
        self.board: Board = self.model.board
        self.player_1 = self.model.get_player_of_number(0)
        self.player_2 = self.model.get_player_of_number(1)

        # put lords in corners
        daimyou = self.board.get_lord_of(self.player_1)
        self.board.set_monster_pos(daimyou, (19, 0))
        wizard = self.board.get_lord_of(self.player_2)
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

    def set_ai_type(self, ai_type, id_=1):
        player = self.model.get_player_of_number(id_)
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
            self.board.capture_terrain_at(pos, self.board.players[owner])

    def add_chim(self):
        """Remove all monsters but lord and chim"""
        # noinspection PyAttributeOutsideInit
        self.chim = self.board.place_new_monster(Monster.Type.CHIMERA,
                                                 chim_start_pos, self.player_2)

    def summon_troll_at(self, pos):
        return self.summon_monster(Monster.Type.TROLL, pos)

    def ensure_player_x_turn(self, number):
        assert self.is_player_x_turn(number), (
            f'It is still player {self.board.get_current_player().id_}\'s '
            f'turn.\n'
            f'Visible controllers: {self.get_visible_controllers()}')

    def get_visible_controllers(self):
        controllers = [self.controller]
        visible = []
        while controllers:
            controller = controllers.pop(-1)
            if controller.visible:
                visible.append(str(controller))
                for child in controller.children:
                    controllers.append(child)
        return ', '.join(visible)

    def is_player_x_turn(self, number):
        return self.board.get_current_player().id_ == number

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
                      {self.board.print()}'

    def summon_monster(self, type_, pos):
        monster = self.board.place_new_monster(type_, pos, self.player_1)
        assert monster is not None
        return monster

    def do_enemy_turn(self):
        self.end_turn()
        for _ in range(120):
            if self.is_player_x_turn(0):
                break
            assert self.publisher.events
            self.tick_event(60)
        self.ensure_player_x_turn(0)

    def surround_with_volcanos(self, pos):
        adj = self.board.get_posses_adjacent_to(pos)
        for adj_pos in adj:
            self.board.set_terrain_to(adj_pos, Terrain.VOLCANO)


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


class TestHandleNearbyEnemies(TestCase):
    def test_attack_lone_monster(self, before):
        self.ensure_monster_is_attacked(Type.LIZARD)

    def test_attack_enemy_while_cannot_move_to_other_tiles(self, before):
        lizard_pos = (3, 5)
        chim_pos = (2, 5)
        self.board.set_monster_pos(self.chim, chim_pos)
        self.surround_with_volcanos(lizard_pos)
        self.surround_with_volcanos(chim_pos)
        self.board.set_terrain_to(lizard_pos, Terrain.GRASS)
        self.board.set_terrain_to(chim_pos, Terrain.GRASS)
        self.ensure_monster_is_attacked(Type.LIZARD)
        self.ensure_attack_monster_at(lizard_pos)

    def test_attack_weakened_monster(self, before):
        """Finish off monster with 1 hp"""
        wraith_pos = (3, 5)
        other_chim_pos = (5, 3)
        self.summon_weakened_monster_at(Type.WRAITH, wraith_pos)
        self.summon_monster(Type.CHIMERA, other_chim_pos)
        self.ensure_monster_gets_killed(wraith_pos)

    def test_ignore_phys_resistant_monster(self, before):
        """ignore this monster because chim's attacks are ineffective"""
        self.ensure_first_monster_is_attacked(Type.LIZARD, Type.DARK_W)

    def test_attack_other_chim(self, before):
        """Mirror match"""
        self.ensure_first_monster_is_attacked(Type.CHIMERA, Type.KING_D)

    def test_attack_ranged_monster(self, before):
        """Sneak in a close attack on a ranged monster"""
        self.ensure_first_monster_is_attacked(Type.ARCH_A, Type.ICEGIANT)

    def test_attack_melee_monster(self, before):
        """Use a ranged attack on a monster bad in range combat"""
        self.chim.set_monster_type_to(Type.VALKYRIE)
        self.ensure_first_monster_is_attacked(Type.ATTACKER, Type.VALKYRIE)

    def test_ignore_immune_monster(self, before):
        """Ignore monster you can't deal damage to"""
        self.chim.set_monster_type_to(Type.VALKYRIE)
        self.ensure_first_monster_is_attacked(Type.FIRBOLG, Type.IRON_G)

    def ensure_monster_is_attacked(self, type_):
        pos = (3, 5)
        self.summon_monster(type_, pos)
        self.ensure_attack_monster_at(pos)

    def ensure_first_monster_is_attacked(self, type1, type2):
        pos1 = (3, 5)
        pos2 = (5, 3)
        self.summon_monster(type1, pos1)
        self.summon_monster(type2, pos2)
        self.ensure_attack_monster_at(pos1)

    def ensure_monster_gets_killed(self, pos):
        self.ensure_attack_monster_at(pos)
        self.ensure_monster_is_dead(pos)

    def ensure_attack_monster_at(self, pos):
        enemy = self.board.monster_at(pos)
        old_hp = enemy.hp
        self.do_enemy_turn()
        adjacent_tiles = self.board.get_posses_adjacent_to(pos)
        assert self.chim.pos in adjacent_tiles, f'Chim was not next to {pos}'
        assert enemy.hp < old_hp, 'Enemy hp did not change'

    def ensure_monster_is_dead(self, pos):
        assert self.board.monster_at(pos) is None, 'Monster is still alive'

    def summon_weakened_monster_at(self, type_, pos):
        monster = self.summon_monster(type_, pos)
        monster.hp = 1
        return monster


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


class TestCannotMove(TestCase):
    def test_surrounded_by_volcanos(self, before):
        inside_volcano = (1, 6)
        self.surround_with_volcanos(inside_volcano)
        self.board.set_monster_pos(self.chim, inside_volcano)
        self.do_enemy_turn()

    def test_surrounded_by_friendly_monsters(self, before):
        self.board.set_monster_pos(self.chim, (0, 0))
        blocked_posses = ((1, 0), (2, 0), (3, 0), (4, 0), (5, 0),
                          (0, 1), (1, 1), (2, 1), (3, 1), (4, 1), (5, 1),
                          (0, 2), (1, 2), (2, 2), (3, 2), (4, 2), (5, 2),
                          (0, 3), (1, 3), (2, 3), (3, 3), (4, 3), (5, 3),
                          (0, 4), (1, 4), (2, 4), (3, 4), (4, 4), (5, 4),
                          (0, 5), (1, 5), (2, 5), (3, 5), (4, 5), (5, 5))
        for pos in blocked_posses:
            self.model.summon_monster(Type.COCOON, pos, self.player_1)
        self.check_chim_pos((0, 0))

    def test_ignore_monster_surrounded_by_friendlies(self, before):
        """Monster is considered reachable on matrix, but cannot move to it"""
        enemy_pos = (3, 5)
        self.board.place_new_monster(Monster.Type.LIZARD, enemy_pos,
                                     self.player_2)
        posses = self.board.get_posses_adjacent_to(enemy_pos)
        for pos in posses:
            if not self.board.monster_at(pos):
                monster = self.board.place_new_monster(Type.COCOON, pos,
                                                       self.player_1)
                monster.moved = True
        self.do_enemy_turn()
        assert self.chim.pos != chim_start_pos


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
        # tower is owned so now the only target is player 1's lord
        old_chim_pos = self.chim.pos
        self.board.capture_terrain_at(self.tower, self.player_2)
        self.check_move_action((old_chim_pos[0] + 4, old_chim_pos[1] - 3))


class TestSummoning(TestCase):
    def before_more(self):
        self.wizard = self.board.lords.get_for(self.player_2)
        assert self.wizard.type
        self.board.set_monster_pos(self.wizard, (1, 1))
        self.chim.moved = True

    def test_summon_monsters(self, before):
        self.set_mana_of_player_to(1, 220)
        self.add_towers_to_summon_on()
        monsters = self.get_monsters_after_turn()
        assert len(monsters) > 2

    def test_no_mana_to_summon(self, before):
        self.set_mana_of_player_to(1, 0)
        self.add_towers_to_summon_on()
        monsters = self.get_monsters_after_turn()
        assert len(monsters) == 2

    def test_summon_6_monsters_on_single_turn(self, before):
        self.set_mana_of_player_to(1, 1000)
        self.add_towers_to_summon_on()
        monsters = self.get_monsters_after_turn()
        assert len(monsters) == 8

    def test_summon_monsters_on_map_edge(self, before):
        self.set_mana_of_player_to(1, 1000)
        self.board.set_monster_pos(self.wizard, (0, 1))
        self.add_towers_to_summon_on()
        monsters = self.get_monsters_after_turn()
        # should be 5 + chim and wizard
        assert len(monsters) == 7

    def test_cannot_summon_on_grass(self, before):
        """Make towers but then move wizard away, surrounded by grass"""
        self.set_mana_of_player_to(1, 1000)
        self.add_towers_to_summon_on()
        self.board.set_monster_pos(self.wizard, (6, 6))
        monsters = self.get_monsters_after_turn()
        # should be 2: chim and wizard
        assert len(monsters) == 2

    def test_cannot_summon_without_towers(self, before):
        """Don't make towers so wizard cannot summon more"""
        self.set_mana_of_player_to(1, 1000)
        self.board.set_monster_pos(self.wizard, (0, 1))
        monsters = self.get_monsters_after_turn()
        # should be 2: chim and wizard
        assert len(monsters) == 2

    def add_towers_to_summon_on(self):
        posses = self.board.get_posses_adjacent_to(self.wizard.pos)
        for pos in posses:
            self.board.on_tile(pos).set_terrain_to(Terrain.TOWER)
            self.board.capture_terrain_at(pos, self.player_2)

    def get_monsters_after_turn(self):
        monsters = self.model.get_monsters_of_player(self.player_1)
        assert len(monsters) == 1, f'Player 1 has {len(monsters)} monsters'
        self.end_turn()
        self.tick_event(10)  # give time to summon
        self.ensure_player_x_turn(0)
        return self.model.get_monsters_of_player(self.player_2)


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
        self.troll = self.board.place_new_monster(Monster.Type.TROLL, (2, 2),
                                                  self.player_2)
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
        self.set_ai_type(AiType.default)

        lord_1 = self.board.lords[0]
        lord_2 = self.board.lords[1]
        self.board.set_monster_pos(lord_1, (1, 1))
        self.surround_pos_with_towers_for(lord_1.pos, 0)
        self.surround_pos_with_towers_for(lord_2.pos, 1)
        self.create_tower_at((9, 9))
        self.create_tower_at((11, 11))
        self.create_tower_at((13, 13))
        self.create_tower_at((15, 15))

    def skip_test_ai_doesnt_lock_up_the_game(self, before):
        for _ in range(5):
            self.do_enemy_turn()

    def surround_pos_with_towers_for(self, pos, owner):
        posses = self.board.get_posses_adjacent_to(pos)
        for pos in posses:
            self.board.set_terrain_to(pos, Terrain.TOWER)
            self.board.capture_terrain_at(pos, owner)


def assert_new_pos(monster, old_monster_pos):
    assert monster.pos != old_monster_pos, f'monster still at {monster.pos}'
