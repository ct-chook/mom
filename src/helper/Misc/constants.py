import math
import os

DIR_OF_THIS_FILE = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR_END = DIR_OF_THIS_FILE.find('src')
ROOT = DIR_OF_THIS_FILE[0:ROOT_DIR_END]
MAP_DIRECTORY = f'{ROOT}src/data/maps/'

print(f'Root dir: {ROOT}')

TERRAIN_COUNT = 13
MONSTER_COUNT = 90
SUMMONER_COUNT = 6

UNEXPLORED = 9999
IMPASSIBLE = 99999

grid_height_factor = math.sqrt(2) / 2  # 0.7083, height / width of tiles


# enumeration
class Range:
    CLOSE, LONG = range(2)


class DayTime:
    DAWN, NOON, DUSK, NIGHT = range(4)


class Terrain:
    (MAIN_FORTRESS, FORTRESS, TOWER, DUNE, FOREST, GRASS, MOUNTAIN, OCEAN,
     RIVER, ROCKY, SWAMP, TUNDRA, VOLCANO, TOWER_CLAIMED, FOG) = range(15)


class Movetype:
    (master, highSky, sky, lowSky, fireSky, bigOcean, smallOcean, bigLand,
     smallLand, fireLand, bigTundra, smallTundra, dune) = range(13)


class AttackType:
    PHYSICAL, MAGICAL, HEAT, COLD = range(4)


class MouseButton:
    LEFT = 1
    RIGHT = 3


class AiType:
    (human, idle, default, scout, attacker, defender) = range(6)


class MonsterBehavior:
    (SCOUT, ATTACKER, DEFENDER) = range(3)


class Color:
    # EGA
    RED = (0xAA, 0, 0)
    BLUE = (0, 0, 0xAA)
    GREEN = (0, 0xAA, 0)
    WHITE = (0xFF, 0xFF, 0xFF)
    BLACK = (0, 0, 0)
    MAGENTA = (0xAA, 0, 0xAA)
    BROWN = (0xAA, 0x55, 0)
    LIGHT_GRAY = (0xAA, 0xAA, 0xAA)
    DARK_GRAY = (0x55, 0x55, 0x55)
    CYAN = (0, 0xAA, 0xAA)
    LIGHT_CYAN = (0x55, 0xFF, 0xFF)
    LIGHT_MAGENTA = (0xff, 0x55, 0xFF)
    LIGHT_GREEN = (0x55, 0xFF, 0x55)
    LIGHT_BLUE = (0x55, 0x55, 0xff)
    LIGHT_RED = (0xff, 0x55, 0x55)
    LIGHT_YELLOW = (0xFF, 0xFF, 0x55)
    # custom
    GRAY = (50, 50, 50)
    YELLOW = (255, 255, 0)
    DARK_GREEN = (50, 175, 50)
    # spritesheet
    MAGENTA_BACKGROUND = (252, 0, 252)
    PLAYER_BLUE = (0, 144, 252)
    PLAYER_RED = (0xFF, 0, 0)
    PLAYER_GREEN = (0, 0xFF, 0)
    PLAYER_YELLOW = (0xFF, 0xFF, 0)


class MonsterType:
    (GLITCH, DAIMYOU, WIZARD, SORCERER, DARKLORD, SUMMONER, SIXTHLORD, FIRE,
     WATER, AIR, EARTH, ANGEL, ARCH_A, GREAT_A, DEMON, ARCH_D, GREAT_D,
     DRAGON_DY, DRAGON_SO, DRAGON_DL, DRAGON_W, DRAGON_SU, FLAME_D, FIRE_D,
     FROST_D, ICE_D, SKY_D, AIR_D, DARK_D, DEATH_D, SILVER_D, GOLD_D, ROMAN,
     CARTHAGO, CAESER, WARRIOR, ATTACKER, CRASHER, SOLDIER, FIGHTER, CRUSADER,
     UNICORN, TRICORN, PEGASUS, MONO_P, WRAITH, DARK_W, BLACK_W, TROLL, GIANT,
     COLOSSUS, CYCLOPS, ICEGIANT, FIRBOLG, GOLEM, STONE_G, IRON_G, MINOTAUR,
     GORGON, SKY_G, LOC, PHOENIX, GRIFFIN, HIPPO_G, CHIMERA, SPHINX, LIZARD,
     TWINHEAD, HYDRA, MARMAID, SIRENE, OCTOPUS, KRAKEN, SERPENT, BIG_S, COCOON,
     GUARDIAN, KING_D, AMAZON, MUSHA, MAGE, VALKYRIE, TAITAN) = range(83)


def is_odd(_input):
    return _input & 1


def is_even(_input):
    return not _input & 1
