import logging

from src.helper.Misc.constants import ROOT, SUMMONER_COUNT

stats_csv_location = f'{ROOT}/src/data/monsters/stats.csv'
terrain_cost_csv_location = f'{ROOT}/src/data/terrain/cost.csv'
terrain_defense_csv_location = f'{ROOT}/src/data/terrain/defense.csv'


class TableLoader:
    def __init__(self, tableholder):
        self.tableholder = tableholder
        assert self.tableholder.terrain_name is not None
        assert self.tableholder.terrain_cost is not None
        assert self.tableholder.terrain_defense is not None
        assert self.tableholder.monster_stats is not None
        assert self.tableholder.summon_options is not None

    def load_tables(self):
        self._load_terrain_stats()
        self._load_monster_stats()

    def _load_terrain_stats(self):
        self._load_terrain_cost_and_name()
        self._load_terrain_defense()

    def _load_terrain_cost_and_name(self):
        lines = self._get_lines(terrain_cost_csv_location)
        for line in lines:
            self._parse_terrain_cost_and_name(line)

    def _parse_terrain_cost_and_name(self, line):
        elements = line.split(',')
        self.tableholder.terrain_name.append(elements[0])
        int_elements = []
        for element in elements[1:]:
            if element == 'N':
                int_elements.append(99)
            else:
                int_elements.append(int(element))
        self.tableholder.terrain_cost.append(int_elements)

    def _load_terrain_defense(self):
        lines = self._get_lines(terrain_defense_csv_location)
        for line in lines:
            self._parse_terrain_defense(line)

    def _parse_terrain_defense(self, line):
        s = line.split(',')
        int_elements = []
        for element in s[1:]:
            if element == 'N':
                int_elements.append(element)
            else:
                int_elements.append(int(element))
        self.tableholder.terrain_defense.append(int_elements)

    def _load_monster_stats(self):
        lines = self._get_lines(stats_csv_location)
        possible_summoners = []
        for line in lines:
            self._parse_monster_stats(line, possible_summoners)
        for _ in range(SUMMONER_COUNT):
            self.tableholder.summon_options.append([])
        for i in range(len(possible_summoners)):
            self._set_summonable_monsters(i, possible_summoners)

    def _parse_monster_stats(self, line, possible_summoners):
        s = line.split(',')
        self.tableholder.monster_stats.append(MonsterStats(
            s[0], s[1], s[2], s[3],
            s[4], s[5], s[6], s[7],
            s[8], s[9], s[10], s[11],
            s[12], s[13],
            s[14], s[15], s[16], s[17]))
        possible_summoners.append(s[18])  # also fetch summoner data

    def _set_summonable_monsters(self, monster_index, possible_summoners):
        summoners = possible_summoners[monster_index]
        summoners = summoners.split('-')
        for summoner in summoners:
            if summoner:
                summoner_index = int(summoner) - 1
                self.tableholder.summon_options[summoner_index].append(
                    monster_index)

    @staticmethod
    def _get_lines(filename):
        with open(filename, 'r') as fd:
            fd.readline()  # flush
            lines = fd.read().splitlines()
        return lines


class MonsterStats:
    move_types = ["M", "SH", "S", "SL", "SF", "OB", "OS", "LB", "LS", "LF",
                  "I2", "I1", "LD", "-"]
    alignments = ["L", "N", "C"]

    def __init__(self,
                 _id, name, alignment, level,
                 move_type, move_points, hp, exp,
                 promotion, mp, short_range, long_range,
                 short_el, long_el,
                 physical, magical, heat, cold):
        # From:
        # 0-3   id,        Name,        Alignment,   Level,
        # 4-7   Move Type, Move Points, HP,          XP,
        # 8-11  Promotion, MP,          Short Range, Long Range,
        # 12-16 Element,   longEl,
        # 14-17 Physical,  Magical,     Heat,        Cold
        # To:
        # 0-3   id,        Name,        Alignment, Level,
        # 4-7   Move Type, Move Points, HP,        XP,
        # 8-11  Promotion, MP,          S-damage,  S-hits,
        # 12-16 L-damage,  L-hits,      S-element, L-element,
        # 16-20 Physical,  Magical,     Heat,      Cold
        self.id = int(_id)
        self.name = name
        self.alignment = self.alignments.index(alignment)
        self.level = int(level)
        self.terrain_type = self.move_types.index(move_type)  # convert to index
        if self.terrain_type == 13:  # if moveType was read as "-"
            self.terrain_type = 0  # set to default
        self.move_points = int(move_points)
        self.max_hp = int(hp)
        self.max_exp = int(exp)
        if promotion == "-":
            self.promotion = None
        else:
            self.promotion = int(promotion)
        self.summon_cost = int(mp)
        self.damage = [None, None]
        self.hits = [None, None]
        if short_range == "-":
            self.damage[0] = 0
            self.hits[0] = 0
        else:
            short_attack = short_range.split("-")
            self.damage[0] = int(short_attack[0])
            self.hits[0] = int(short_attack[1])
        if long_range == "-":
            self.damage[1] = 0
            self.hits[1] = 0
        else:
            long_attack = long_range.split("-")
            self.damage[1] = int(long_attack[0])
            self.hits[1] = int(long_attack[1])
        self.element = [None, None]
        element_str = (short_el, long_el)
        elements = ("P", "M", "H", "C", "-")
        for i in range(2):
            self.element[i] = elements.index(element_str[i])
            if self.element[i] == 4:
                self.element[i] = 0  # converts "-" into "P"
        self.resistance = (
            int(physical), int(magical), int(heat), int(cold))


class DataTables:
    terrain_cost = []
    terrain_name = []
    terrain_defense = []
    summon_options = []
    monster_stats = []
    loaded = False

    @staticmethod
    def load():
        table_loader = TableLoader(DataTables)
        table_loader.load_tables()
        logging.info('data tables loaded')
        DataTables.loaded = True

    @staticmethod
    def get_terrain_cost(terrain, movement_type):
        if not DataTables.loaded:
            DataTables.load()
        return DataTables.terrain_cost[terrain][movement_type]

    @staticmethod
    def get_terrain_defense(terrain, terrain_type):
        if not DataTables.loaded:
            DataTables.load()
        return DataTables.terrain_defense[terrain][terrain_type]

    @staticmethod
    def get_monster_stats(monster_id) -> MonsterStats:
        if not DataTables.loaded:
            DataTables.load()
        return DataTables.monster_stats[monster_id]

    @staticmethod
    def get_terrain_name(terrain_id):
        if not DataTables.loaded:
            DataTables.load()
        return DataTables.terrain_name[terrain_id]

    @staticmethod
    def get_summon_options(summoner_id):
        if not DataTables.loaded:
            DataTables.load()
        return DataTables.summon_options[summoner_id]
