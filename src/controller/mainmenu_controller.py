import os

from pygame.rect import Rect

from src.abstract.view import View
from src.abstract.window import Window, TextButton
from src.components.board.monster import Monster
from src.components.board.players import PlayerList
from src.helper.Misc.constants import Color, AiType
from src.helper.Misc.constants import MAP_DIRECTORY
from src.helper.Misc.datatables import DataTables


class MainMenuController(Window):
    def __init__(self, x, y, width, height, parent):
        """Should be initialized by MomController"""
        self.rectangle = Rect(x, y, width, height)
        super().__init__(x, y, width, height)
        self.add_view(MainMenuView)
        self.parent = parent
        self.mapname = None

        self.start_button = self.attach_controller(
            TextButton(50, 50, 150, 50, 'Choose map',
                       self.show_map_selection_window))
        self.map_selection_window: MapSelectionWindow = self.attach_controller(
            MapSelectionWindow(50, 50, 200, 600, self))
        self.mapoptions_window: MapOptionsWindow = self.attach_controller(
            MapOptionsWindow(50, 50, 500, 350, self))

        self.map_selection_window.hide()
        self.mapoptions_window.hide()

    def show_map_selection_window(self):
        self.map_selection_window.show()
        self.map_selection_window.fetch_maps()

    def set_map(self, mapname):
        self.mapname = mapname
        self.mapoptions_window.show()

    def create_board(self, mapoptions):
        mapoptions.mapname = self.mapname
        self.hide()
        self.parent.create_board(mapoptions)


class MainMenuView(View):
    def __init__(self, rectangle):
        super().__init__(rectangle)
        self.add_text('Main Menu')
        self.bg_color = Color.DARK_GREEN


class MapOptionsWindow(Window):
    def __init__(self, x, y, width, height, parent):
        super().__init__(x, y, width, height)
        self.add_view(MapOptionsView)
        self.parent: MainMenuController = parent
        self.mapoptions = MapOptions()
        # add buttons for player options
        # (eventually must become options for each player)
        # from player counts 2 - 4
        self.player_count_buttons = []
        for n in range(3):
            self.player_count_buttons.append(self.add_button(TextButton(
                50, 50 * n, 150, 50, f'{2 + n} Players',
                self.set_number_of_players, n + 2)))
        # for players 1 - 4
        self.summoner_type_buttons: [FlipButton] = []
        for n in range(4):
            button = self.add_button(SummonerButton(200, 50 * n, 150, 50, n))
            self.summoner_type_buttons.append(button)

        self.player_type_buttons: [FlipButton] = []
        default_player_type = (0, 1, 1, 1)
        for n in range(4):
            button = self.add_button(HumanOrComputerButton(
                350, 50 * n, 150, 50, default_player_type[n]))
            self.player_type_buttons.append(button)

        self.finish_button = self.add_button(TextButton(
            50, 250, 150, 50, 'Ok', self.finish))
        self.set_number_of_players(4)

    def set_number_of_players(self, number):
        self.mapoptions.set_number_of_players(number)

    def set_lord(self, monster_type):
        self.mapoptions.lord_type = monster_type

    def finish(self):
        n = 0
        for button in self.summoner_type_buttons:
            self.mapoptions.lord_types[n] = button.get_value()
            n += 1
        n = 0
        for button in self.player_type_buttons:
            self.mapoptions.ai_types[n] = button.get_value()
            n += 1
        self.mapoptions.set_players()
        self.hide()
        self.parent.create_board(self.mapoptions)


class MapOptionsView(View):
    def __init__(self, rectangle):
        super().__init__(rectangle)
        self.add_text('MapOptionsView')
        self.bg_color = Color.LIGHT_RED


class CappedCounter:
    """A variable that can be incremented and loop to zero at a certain cap

    The cap is exclusive. CappedCounter(0, 10) will loop between 0-9
    """
    def __init__(self, value, cap):
        self.value = value
        self.cap = cap

    def flip(self):
        """Increase counter, reverts back to zero if value hits cap"""
        self.value += 1
        if self.value >= self.cap:
            self.value = 0

    def __repr__(self):
        return str(self.value)

    def __str__(self):
        return str(self.value)


class FlipButton(TextButton):
    def __init__(self, x, y, width, height, base_val, val_list, str_list):
        """Used to hold and return a value from a list of values

        Provide a list of values that the button should return, and also a list
        of strings representing these values to show on the button"""
        super().__init__(x, y, width, height, '', self._next)
        self.val_list = val_list
        self.str_list = str_list
        assert len(self.val_list) == len(self.str_list), (
            'Both lists should have same length')
        assert base_val < len(self.val_list)
        self.counter = CappedCounter(base_val, len(self.val_list))
        self._update_view()

    def _next(self):
        self.counter.flip()
        self._update_view()

    def _update_view(self):
        self.view.set_text(self.str_list[self.counter.value])
        self.view.queue_for_sprite_update()

    def get_value(self):
        return self.val_list[self.counter.value]


class SummonerButton(FlipButton):
    def __init__(self, x, y, width, height, summoner_type):
        vals = (Monster.Type.DAIMYOU, Monster.Type.WIZARD,
                Monster.Type.SORCERER, Monster.Type.DARKLORD,
                Monster.Type.SUMMONER)
        str_list = []
        for val in vals:
            str_list.append(DataTables.get_monster_stats(val).name)
        super().__init__(x, y, width, height, summoner_type, vals, str_list)


class HumanOrComputerButton(FlipButton):
    def __init__(self, x, y, width, height, player_type):
        vals = (AiType.human, AiType.default)
        str_list = ('Human', 'Computer')
        super().__init__(x, y, width, height, player_type, vals, str_list)


class MapSelectionWindow(Window):
    def __init__(self, x, y, width, height, parent):
        super().__init__(x, y, width, height)
        self.add_view(MapSelectionView)
        self.parent = parent

    def fetch_maps(self):
        mapnames = os.listdir(MAP_DIRECTORY)
        mapnames.append('test')  # fake map name that makes test map
        self.list_maps(mapnames)

    def list_maps(self, mapnames):
        # add buttons
        y = 0
        for mapname in mapnames:
            self.add_button(TextButton(
                0, y, 200, 100, mapname, self.pick_map, mapname))
            y += 50

    def pick_map(self, mapname):
        self.hide()
        self.parent.set_map(mapname)


class MapOptions:
    def __init__(self):
        self.players: PlayerList = PlayerList()
        self.number_of_players = None
        self.lord_types = {}
        self.ai_types = {}
        self.mapname = None

    def set_number_of_players(self, number):
        self.number_of_players = number

    def set_players(self):
        # lord type should be configurable, players shouldn't be made until
        # all settings are confirmed
        # quick fix for lack of lord types configured
        if not self.lord_types:
            for n in range(4):
                self.lord_types[n] = n + Monster.Type.DAIMYOU
        if not self.ai_types:
            for n in range(4):
                if n == 0:
                    self.ai_types[n] = AiType.human
                else:
                    self.ai_types[n] = AiType.default
        for n in range(self.number_of_players):
            self.players.add_player(self.lord_types[n], self.ai_types[n], 50)


class MapSelectionView(View):
    def __init__(self, rectangle):
        super().__init__(rectangle)
        self.add_text('MapSelectionView')
        self.bg_color = Color.LIGHT_BLUE
