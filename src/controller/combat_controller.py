import logging

from pygame import Surface

from src.abstract.view import View
from src.abstract.window import Window
from src.components.combat import combatlog
from src.components.combat.combatlogbuilder import CombatLogBuilder
from src.components.combat.combatlog import CombatLog
from src.helper.Misc.constants import Color
from src.helper.Misc.options_game import Options
from src.helper.Misc.spritesheet import SpriteSheetFactory
from src.helper.events import EventCallback


class CombatWindow(Window):
    def __init__(self, info):
        super().__init__(100, 100, 300, 200, info)
        self.view: CombatView = self.add_view(CombatView)
        self.combat_log: combatlog.CombatLog = None
        self.hide()
        self.active = False

    def on_combat(self, attacks, attack_range):
        self.show()
        logging.info('Showing combat')
        assert not self.active, 'Combat window is already in use!'
        self.active = True
        combat = CombatLogBuilder()
        self.combat_log = combat.build_from_attacks(attacks, attack_range)

        draw_screen_event = EventCallback(self.view.draw_screen, attacks)
        show_attacks_event = EventCallback(self.view.show_attack,
                                           self.combat_log)
        close_window_event = EventCallback(self.handle_combat_end)
        clear_selection_event = EventCallback(self.parent.view.
                                              clear_highlighted_tiles)
        unfreeze_event = EventCallback(self.parent.unfreeze_events)
        combat_events = (draw_screen_event, show_attacks_event,
                         close_window_event, clear_selection_event,
                         unfreeze_event)
        for event in combat_events:
            self.append_event(event)

    def handle_mouseclick(self):
        self.events.skip()

    def handle_combat_end(self):
        self.active = False
        self.parent.handle_combat_end(self.combat_log)
        self.hide()


class CombatView(View):
    COMBAT_DELAY = 20

    def __init__(self, rectangle):
        super().__init__(rectangle)
        self.bg_color = Color.DARK_GREEN
        self.text = self.add_text('Combat screen', 20, (0, 0))
        self.text.set_background_color(self.bg_color)
        self.text.set_color(Color.BLACK)
        placeholder_sprite = Surface((0, 0))
        self.left_monster = self.add_sprite(placeholder_sprite, (50, 100))
        self.right_monster = self.add_sprite(placeholder_sprite, (150, 100))
        self.round_number = None
        self.monsters = None
        self.hp_left_text = self.add_text('', offset=(50, 150))
        self.hp_right_text = self.add_text('', offset=(150, 150))
        self.hp_left = None
        self.hp_right = None

    def draw_screen(self, attacks):
        self.round_number = -1
        monster_left = attacks.get_attack(0, 0).monster
        monster_right = attacks.get_attack(1, 0).monster
        self.monsters = [monster_left, monster_right]
        self.hp_left = self.monsters[0].hp
        self.hp_right = self.monsters[1].hp
        if Options.headless:
            return

        monster_sprites = SpriteSheetFactory().get_monster_spritesheets()
        self.left_monster.set_surface(monster_sprites.get_sprite(
            monster_left.type, monster_left.owner.id_))
        self.right_monster.set_surface(monster_sprites.get_sprite(
            monster_right.type, monster_right.owner.id_))
        self.queue_for_background_update()

    def show_attack(self, combat_log: CombatLog):
        self.round_number += 1
        assert len(combat_log.rounds) > self.round_number, (
            'reached a round number beyond what is in the log. '
            f'{combat_log}')
        round_ = combat_log.rounds[self.round_number]
        attacker = self.monsters[round_.side]
        damage = round_.damage
        if damage >= 0:
            attacks = f'does {damage} damage to'
        else:
            attacks = 'misses'
        targeted_side = (round_.side + 1) % 2
        target = f'{self.monsters[targeted_side]}'
        self.text.set_text(
            f'{attacker} {attacks} {target} ({self.round_number + 1})')
        if damage > -1:
            if targeted_side == 0:
                self.hp_left -= round_.damage
                if self.hp_left < 0:
                    self.hp_left = 0
            else:
                self.hp_right -= round_.damage
                if self.hp_right < 0:
                    self.hp_right = 0
        self.hp_left_text.set_text(f'{self.hp_left}/'
                                   f'{self.monsters[0].stats.max_hp}')
        self.hp_right_text.set_text(f'{self.hp_right}/'
                                    f'{self.monsters[1].stats.max_hp}')
        self.queue_for_sprite_update()

        logging.info(self.text.text)
        delay = self.COMBAT_DELAY
        if self.round_number == len(combat_log.rounds) - 1:
            delay *= -1
        return delay
