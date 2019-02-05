from math import ceil

from src.abstract.view import View
from components.button import ButtonMatrixView
from src.abstract.window import Window
from src.components.button import ButtonMatrix
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
        self.player = self.board_model.get_current_player()
        self.summonable_monsters = []
        self.summon_pos = None

        self.summonable_monsters = (DataTables
                                    .get_summon_options(self.player.lord_type))
        number_of_buttons = len(self.summonable_monsters)
        height = ceil(button_y_offset + button_height * number_of_buttons) / 2
        rows = ceil(number_of_buttons / 2)
        cols = 2
        # super is called after the number of buttons, that is, the number
        # of monsters has been computed
        super().__init__(100, 100, width, height)
        self.view = self.add_view(SummonView)
        self.summon_buttons: SummonButtons = self.add_button(
            SummonButtons(button_x_offset, button_y_offset,
                          button_width, button_height,
                          rows, cols, self.handle_summon_choice))
        self.display_summonable_monsters()
        self.hide()

    def handle_summon_choice(self, index):
        monster_type = self.summonable_monsters[index]
        monster = self.parent.handle_summon_monster(
            monster_type, self.summon_pos)
        # todo better alert
        if not monster:
            print('could not summon monster, not enough towers/mp')
        else:
            self.hide()

    def display_summonable_monsters(self):
        if not self.view:
            return
        self.summon_buttons.display_monsters(self.summonable_monsters)

    def set_summon_pos(self, pos):
        self.summon_pos = pos

    def handle_mouseclick(self):
        self.hide()


class SummonView(View):
    def __init__(self, rectangle):
        super().__init__(rectangle)
        self.set_bg_color(Color.CYAN)
        self.title = self.add_text('SummonView', 48, (0, 0))


class SummonButtons(ButtonMatrix):
    def __init__(self, x, y, button_width, button_height, rows, cols,
                 callback):
        super().__init__(
            x, y, button_width, button_height, rows, cols, callback)
        self.add_view(SummonChoiceButtonsView)

    def display_monsters(self, summonable_monsters):
        for monster_index, index in zip(summonable_monsters,
                                        range(len(summonable_monsters))):
            player_id = 0
            sprite = (SpriteSheetFactory().get_monster_spritesheets()
                      .get_sprite(monster_index, player_id))
            self.add_button_sprite(sprite, index)
        self.view.queue_for_sprite_update()


class SummonChoiceButtonsView(ButtonMatrixView):
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
