from src.components.combat.attack import AttackCollection
from src.abstract.view import View
from src.abstract.window import Window
from src.components.button import Button
from src.controller import board_controller
from src.controller.combat_controller import CombatWindow
from src.helper.Misc.constants import Color
from src.helper.Misc.constants import Range


class PreCombatWindow(Window):
    def __init__(self, board_model, combat_window):
        super().__init__(100, 100, 400, 300)
        self.board_model: board_controller.BoardModel = board_model
        self.combat_window: CombatWindow = combat_window

        self.attacks: AttackCollection = None
        self.view: PreCombatView = self.add_view(PreCombatView)
        self.short_range_button: AttackButton = self.attach_controller(
            AttackButton(
                0, 75, 200, 50,
                self.handle_attack_choice, Range.CLOSE))
        self.long_range_button: AttackButton = self.attach_controller(
            AttackButton(
                0, 175, 200, 50,
                self.handle_attack_choice, Range.LONG))
        self.short_range_button.show()
        self.long_range_button.show()
        self.hide()

    def handle_attack_choice(self, attack_range):
        monsters = (self.attacks.get_attack(0, attack_range).monster,
                    self.attacks.get_attack(1, attack_range).monster)
        self.parent.handle_attack_order(monsters, attack_range)
        self.hide()

    def handle_mouseclick(self):
        self.hide()

    def set_attackers(self, combat_monsters):
        assert len(combat_monsters) == 2
        attacks = self.board_model.get_short_and_long_attacks(combat_monsters)
        self._set_and_display_attacks(attacks)

    def _set_and_display_attacks(self, attacks):
        if not self.view:
            return
        self.attacks = attacks
        side_left_attacks = attacks.get_all_ranges(0)
        side_right_attacks = attacks.get_all_ranges(1)
        self.short_range_button.set_stats(side_left_attacks)
        self.long_range_button.set_stats(side_right_attacks)
        self.view.display_attacks(attacks)
        self.view.queue_for_background_update()


class AttackButton(Button):
    def __init__(self, x, y, width, height, callback, arguments):
        super().__init__(x, y, width, height, callback, arguments)
        self.view = self.add_view(AttackButtonView)

    def set_stats(self, attacks):
        self.view.set_stats(attacks)


class PreCombatView(View):
    def __init__(self, rectangle):
        super().__init__(rectangle)
        self.bg_color = Color.LIGHT_RED
        self.add_text('PrecombatView', 24, (0, 0))
        close_range_y = 50
        long_range_y = 150
        self.close_range_text = self.add_text(
            'Close Range', 24, (0, close_range_y), 100)
        self.long_range_text = self.add_text(
            'Long Range', 24, (0, long_range_y), 100)
        self.monsters = [None, None]
        self.close_range_damage = [None, None]
        self.close_range_accuracy = [None, None]
        self.long_range_damage = [None, None]
        self.long_range_accuracy = [None, None]
        for n in range(2):
            x_base = 100 * n
            self.monsters[n] = self.add_text(
                f'monster_{n}', size=20, offset=(x_base, close_range_y - 25),
                max_width=100)

    def display_attacks(self, attacks):
        for n in range(2):
            close_attack = attacks.get_attack(n, 0)
            monster_ = close_attack.monster
            self.monsters[n].set_text(f'{monster_.name}')


class AttackButtonView(View):
    def __init__(self, rectangle):
        super().__init__(rectangle)
        self.bg_color = (50, 50, 200)
        self.damage = [None, None]
        self.accuracy = [None, None]
        for n in range(2):
            x_base = n * 100
            self.damage[n] = self.add_text(
                f'damage_{n}', size=24, offset=(x_base, 0))
            self.accuracy[n] = self.add_text(
                f'accuracy_{n}', size=24, offset=(x_base, 25))
        self.queue_for_background_update()

    def set_stats(self, attacks):
        for n in attacks:
            attack = attacks[n]
            self.damage[n].set_text(f'{attack.damage} - {attack.hits}')
            self.accuracy[n].set_text(f'{attack.accuracy}')
        self.queue_for_background_update()
