from src.abstract.view import View
from src.abstract.window import Window, ButtonMatrix
from src.helper.Misc.constants import Color
from src.helper.Misc.datatables import DataTables
from src.helper.Misc.spritesheet import SpriteSheetFactory


class SummonWindow(Window):
    def __init__(self, board_model):
        # todo: clean up, set and cache window every time it opens
        width = 300
        button_height = 50
        button_width = 100
        button_y_offset = 100
        button_x_offset = 0
        self.board_model = board_model
        self.player = 0
        self.summonable_monsters = []
        self.summon_pos = None

        self._get_summonable_monsters_for_player(self.player)
        number_of_buttons = len(self.summonable_monsters)
        height = button_y_offset + button_height * number_of_buttons
        rows = number_of_buttons
        cols = 1
        # super is called after the number of buttons, that is, the number
        # of monsters has been computed
        super().__init__(100, 100, width, height)
        self.view = self.add_view(SummonView)
        self.summon_options = self.add_button(
            SummonChoiceButtons(
                button_x_offset, button_y_offset,
                button_width, button_height,
                rows, cols, self.handle_summon_choice))
        self.display_summonable_monsters()
        self.hide()

    def _get_summonable_monsters_for_player(self, summoner_id):
        self.summonable_monsters = DataTables.summon_options[summoner_id]

    def handle_summon_choice(self, index):
        monster_type = self.summonable_monsters[index]
        summoned_monster = self.board_model.summon_monster_at(
            monster_type, self.summon_pos)
        if summoned_monster is None:
            print('Not enough mana')
            return
        self.hide()

    def display_summonable_monsters(self):
        if not self.view:
            return
        self.summon_options.view.display_summonable_monsters(
            self.summonable_monsters)

    def set_summon_pos(self, pos):
        self.summon_pos = pos

    def handle_mouseclick(self):
        self.hide()


class SummonView(View):
    def __init__(self, rectangle):
        super().__init__(rectangle)

        self.set_bg_color(Color.CYAN)
        self.title = self.add_text('SummonView', 48, (0, 0))


class SummonChoiceButtons(ButtonMatrix):
    def __init__(self, x, y, button_width, button_height, rows, cols,
                 callbacks):
        super().__init__(
            x, y, button_width, button_height, rows, cols, callbacks)
        self.add_view(SummonChoiceButtonsView)


class SummonChoiceButtonsView(View):
    def __init__(self, rectangle):
        super().__init__(rectangle)
        self.set_bg_color(Color.BLUE)
        self.monster_sprites = SpriteSheetFactory().get_monster_spritesheets()

    def display_summonable_monsters(self, monster_ids):
        row_y = 0
        for monster_id in monster_ids:
            monster_sprite = self.monster_sprites.get_sprite(monster_id, 0)
            self.add_sprite(monster_sprite, (0, row_y))
            row_y += 50
