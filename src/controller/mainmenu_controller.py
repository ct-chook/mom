import os

from pygame.rect import Rect

from src.abstract.view import View
from src.abstract.window import Window
from src.components.board.board import MapOptions
from src.components.button import TextButton
from src.components.board.monster import Monster
from src.helper.Misc.constants import Color, AiType
from src.helper.Misc.constants import MAP_DIRECTORY
from src.helper.Misc.datatables import DataTables


class MainMenuController(Window):
    def __init__(self, x, y, width, height, info, parent):
        """Should be initialized by MomController"""
        self.rectangle = Rect(x, y, width, height)
        super().__init__(x, y, width, height, info)
        self.add_view(MainMenuView)
        self.parent = parent
        self.mapname = None

        self.start_button = self.attach_controller(
            TextButton(50, 50, 150, 50,
                       info,
                       'Choose map',
                       self.show_map_selection_window))
        self.map_selection_window: MapSelectionWindow = self.attach_controller(
            MapSelectionWindow(50, 50, 200, 600, info, self))
        self.mapoptions_window: MapOptionsWindow = self.attach_controller(
            MapOptionsWindow(50, 50, 650, 350, info, self))

        self.map_selection_window.hide()
        self.mapoptions_window.hide()

    def show_map_selection_window(self):
        self.map_selection_window.show()
        self.map_selection_window.fetch_maps()

    def set_map(self, mapname):
        self.mapname = mapname
        self.mapoptions_window.show()

    def create_board(self, info, mapoptions):
        mapoptions.mapname = self.mapname
        self.hide()
        self.parent.create_board(info, mapoptions)


class MainMenuView(View):
    def __init__(self, rectangle):
        super().__init__(rectangle)
        self.add_text('Main Menu')
        self.bg_color = Color.DARK_GREEN


class MapOptionsWindow(Window):
    def __init__(self, x, y, width, height, info, parent):
        super().__init__(x, y, width, height, info)
        self.add_view(MapOptionsView)
        self.parent: MainMenuController = parent
        self.mapoptions = MapOptions()

        self.player_count_buttons: [FlipButton] = \
            self._add_player_count_buttons(info)
        self.summoner_type_buttons: [FlipButton] = \
            self._add_summoner_type_buttons(info)
        self.player_type_buttons: [FlipButton] = (
            self._add_player_type_buttons(info))
        self.team_buttons: [FlipButton] = self._add_team_buttons(info)
        self._add_finish_button(info)
        self.set_number_of_players(4)

    def _add_player_count_buttons(self, info):
        buttons = []
        for n in range(3):
            buttons.append(self.add_button(
                TextButton(50, 50 * n, 150, 50,
                           info,
                           f'{2 + n} Players',
                           self.set_number_of_players, n + 2)))
        return buttons

    def _add_summoner_type_buttons(self, info):
        buttons = []
        for n in range(4):
            buttons.append(self.add_button(
                SummonerButton(200, 50 * n, 150, 50, info, n)))
        return buttons

    def _add_player_type_buttons(self, info):
        buttons = []
        default_player_type = (0, 1, 1, 1)
        for n in range(4):
            buttons.append(self.add_button(HumanOrComputerButton(
                350, 50 * n, 150, 50, info, default_player_type[n])))
        return buttons

    def _add_team_buttons(self, info):
        buttons = []
        for n in range(4):
            buttons.append(self.add_button(
                TeamButton(500, 50 * n, 150, 50, info, 0)))
        return buttons

    def _add_finish_button(self, info):
        self.finish_button = self.add_button(TextButton(
            50, 250, 150, 50, info, 'Ok', self.finish, info))

    def set_number_of_players(self, number):
        self.mapoptions.set_number_of_players(number)

    def set_lord(self, monster_type):
        self.mapoptions.lord_type = monster_type

    def finish(self, info):
        n = 0
        for button in self.summoner_type_buttons:
            self.mapoptions.lord_types[n] = button.get_value()
            n += 1
        n = 0
        for button in self.player_type_buttons:
            self.mapoptions.ai_types[n] = button.get_value()
            n += 1
        n = 0
        for button in self.team_buttons:
            self.mapoptions.teams[n] = button.get_value()
            n += 1
        self.hide()
        self.parent.create_board(info, self.mapoptions)


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
        return self.value

    def __str__(self):
        return str(self.value)


class FlipButton(TextButton):
    def __init__(self, x, y, width, height, info, base_val):
        """Used to hold and return a value from a list of values

        Provide a list of values that the button should return, and also a list
        of strings representing these values to show on the button"""
        super().__init__(x, y, width, height, info, '', self._next)
        self.val_list = self._get_val_list()
        self.str_list = self._get_str_list()
        assert len(self.val_list) == len(self.str_list), (
            'Both lists should have same length')
        assert base_val < len(self.val_list)
        self.counter = CappedCounter(base_val, len(self.val_list))
        self._update_view()

    def _get_val_list(self):
        """Override this"""
        return []

    def _get_str_list(self):
        """Override this"""
        return []

    def get_value(self):
        return self.val_list[self.counter.value]

    def _next(self):
        self.counter.flip()
        self._update_view()

    def _update_view(self):
        self.view.set_text(self.str_list[self.counter.value])
        self.view.queue_for_sprite_update()


class SummonerButton(FlipButton):
    def _get_val_list(self):
        return (Monster.Type.DAIMYOU, Monster.Type.WIZARD,
                Monster.Type.SORCERER, Monster.Type.DARKLORD,
                Monster.Type.SUMMONER)

    def _get_str_list(self):
        str_list = []
        for val in range(Monster.Type.DAIMYOU, Monster.Type.SUMMONER + 1):
            str_list.append(DataTables.get_monster_stats(val).name)
        return str_list


class HumanOrComputerButton(FlipButton):
    def _get_val_list(self):
        return AiType.human, AiType.default

    def _get_str_list(self):
        return 'Human', 'Computer'


class TeamButton(FlipButton):
    def _get_val_list(self):
        return 0, 1, 2, 3

    def _get_str_list(self):
        return 'No team', 'Team 1', 'Team 2', 'Team 3'


class MapSelectionWindow(Window):
    def __init__(self, x, y, width, height, info, parent):
        super().__init__(x, y, width, height, info)
        self.add_view(MapSelectionView)
        self.parent = parent
        self.info = info

    def fetch_maps(self):
        mapnames = os.listdir(MAP_DIRECTORY)
        mapnames.append('test')  # fake map name that makes test map
        self.list_maps(mapnames)

    def list_maps(self, mapnames):
        # add buttons
        y = 0
        for mapname in mapnames:
            self.add_button(TextButton(
                0, y, 200, 100,
                self.info, mapname, self.pick_map, mapname))
            y += 50

    def pick_map(self, mapname):
        self.hide()
        self.parent.set_map(mapname)


class MapSelectionView(View):
    def __init__(self, rectangle):
        super().__init__(rectangle)
        self.add_text('MapSelectionView')
        self.bg_color = Color.LIGHT_BLUE
