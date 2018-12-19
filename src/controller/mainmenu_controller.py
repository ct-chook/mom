import os

from pygame.rect import Rect

from src.abstract.view import View
from src.abstract.window import Window, TextButton
from src.components.board.monster import Monster
from src.components.board.players import PlayerList, AiType
from src.helper.Misc.constants import Color
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
            MapOptionsWindow(50, 50, 200, 500, self))

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
        # (eventually must become options for each player
        for n in range(3):
            self.add_button(TextButton(
                50, 50 * n, 150, 50, f'{n} Players',
                self.set_number_of_players, n + 1))
        for n in range(1, 6):
            self.add_button(TextButton(
                100, 50 * n, 150, 50,
                f'{DataTables.get_monster_stats(n).name}',
                self.set_lord, n))
        self.add_button(TextButton(50, 250, 150, 50, 'Ok', self.finish))
        self.set_number_of_players(4)

    def set_number_of_players(self, number):
        self.mapoptions.set_number_of_players(number)

    def set_lord(self, monster_type):
        self.mapoptions.lord_type = monster_type

    def finish(self):
        self.mapoptions.set_players()
        self.hide()
        self.parent.create_board(self.mapoptions)


class MapOptionsView(View):
    def __init__(self, rectangle):
        super().__init__(rectangle)
        self.add_text('MapOptionsView')
        self.bg_color = Color.LIGHT_RED


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
        self.lord_type = Monster.Type.DAIMYOU
        self.mapname = None

    def set_number_of_players(self, number):
        self.number_of_players = number

    def set_players(self):
        # lord type should be configurable, players shouldn't be made until
        # all settings are confirmed
        self.players.add_player(self.lord_type, AiType.human, 50)
        for n in range(self.number_of_players - 1):
            self.players.add_player(2 + n, AiType.default, 50)


class MapSelectionView(View):
    def __init__(self, rectangle):
        super().__init__(rectangle)
        self.add_text('MapSelectionView')
        self.bg_color = Color.LIGHT_BLUE
