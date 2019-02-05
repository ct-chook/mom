import random

from src.components.board.players import Player
from src.helper.Misc.datatables import MonsterStats, DataTables
from src.helper.Misc.constants import MonsterType


class Monster:
    class Type:
        (GLITCH, DAIMYOU, WIZARD, SORCERER, DARKLORD, SUMMONER, SIXTHLORD, FIRE,
         WATER, AIR, EARTH, ANGEL, ARCH_A, GREAT_A, DEMON, ARCH_D, GREAT_D,
         DRAGON_DY, DRAGON_SO, DRAGON_DL, DRAGON_W, DRAGON_SU, FLAME_D, FIRE_D,
         FROST_D, ICE_D, SKY_D, AIR_D, DARK_D, DEATH_D, SILVER_D, GOLD_D, ROMAN,
         CARTHAGO, CAESER, WARRIOR, ATTACKER, CRASHER, SOLDIER, FIGHTER,
         CRUSADER, UNICORN, TRICORN, PEGASUS, MONO_P, WRAITH, DARK_W, BLACK_W,
         TROLL, GIANT, COLOSSUS, CYCLOPS, ICEGIANT, FIRBOLG, GOLEM, STONE_G,
         IRON_G, MINOTAUR, GORGON, SKY_G, LOC, PHOENIX, GRIFFIN, HIPPO_G,
         CHIMERA, SPHINX, LIZARD, TWINHEAD, HYDRA, MARMAID, SIRENE, OCTOPUS,
         KRAKEN, SERPENT, BIG_S, COCOON, GUARDIAN, KING_D, AMAZON, MUSHA, MAGE,
         VALKYRIE, TAITAN) = range(83)

    def __init__(self, monster_type, pos, owner, terrain):
        assert type(owner) is not int
        self.pos = pos
        self.owner: Player = owner
        self.terrain = terrain

        self.type = None
        self.stats: MonsterStats = None
        self.hp = None
        self.name = None
        self.exp = None
        self.terrain_type = None
        self.moved = False
        self.brain = None

        self.set_monster_type_to(monster_type)

    def set_monster_type_to(self, monster_type):
        self.type = monster_type
        self.stats = DataTables.get_monster_stats(monster_type)
        self._update_stats()
        self.exp = 0
        self.terrain_type = self.stats.terrain_type

    def _update_stats(self):
        self.hp = self.stats.max_hp
        self.name = self.stats.name

    def award_exp(self, exp):
        self.exp += exp

    def will_promote_with_exp(self, exp):
        return self.exp + exp >= self.stats.max_exp

    def promote(self):
        assert self.stats.promotion, (
                f'Tried to promote {self.name}, but it has no promotion!')
        self.set_monster_type_to(self.stats.promotion)
        self.exp = 0

    def is_lord(self):
        if self.type <= MonsterType.SIXTHLORD:
            return True

    def tower_heal(self):
        """Should be triggered when monster ends turn on tower

        todo check how much health is restored (flat amount?)
        seems to be 10±4, independent of max hp
        """
        self.heal(random.randint(6, 14))

    def heal(self, amount):
        self.hp += amount
        if self.hp > self.stats.max_hp:
            self.hp = self.stats.max_hp

    def is_friendly_with(self, player):
        return self.owner.is_friendly_with(player)

    def is_enemy_of(self, player):
        return self.owner.is_enemy_of(player)

    def __str__(self):
        return f'{self.name}'
