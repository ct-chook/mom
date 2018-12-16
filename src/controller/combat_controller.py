import logging

from src.components.combat import combatlog
from src.components.combat.combat import Combat
from src.helper.Misc.options_game import Options
from src.helper.events import events
from src.helper.events.events import EventCallback, EventList
from src.abstract.window import Window
from src.components.combat.combatlog import CombatLog
from src.helper.Misc.constants import Color
from src.helper.Misc.spritesheet import SpriteSheetFactory
from src.abstract.view import View


class CombatWindow(Window):
    def __init__(self):
        super().__init__(100, 100, 300, 200)
        self.view: CombatView = self.add_view(CombatView)
        self.event_list: events.EventList = None
        self.combat_log: combatlog.CombatLog = None
        self.hide()
        self.active = False

    def on_combat(self, attacks, attack_range):
        logging.info('Showing combat')
        combat = Combat()
        self.combat_log = combat.monster_combat2(attacks, attack_range)
        print('adding draw screen event')
        draw_screen_event = EventCallback(self.view.draw_screen, attacks)
        show_attacks_event = EventCallback(self.view.show_attack, self.combat_log)
        close_window_event = EventCallback(self.handle_combat_end)
        clear_selection_event = EventCallback(self.parent.view.clear_highlighted_tiles)
        combat_events = (
            draw_screen_event, show_attacks_event, close_window_event,
            clear_selection_event)
        self.event_list = EventList(combat_events)

    def handle_mouseclick(self):
        self.event_list.skip()

    def handle_combat_end(self):
        self.parent.model.process_combat_log(self.combat_log)
        self.hide()
        logging.info('closing')


class CombatView(View):
    COMBAT_DELAY = 120

    def __init__(self, rectangle):
        super().__init__(rectangle)
        self.bg_color = Color.DARK_GREEN
        self.monster_sprites = SpriteSheetFactory().get_monster_spritesheets()
        placeholder_sprite = self.monster_sprites.get_sprite(0, 0)
        self.text = self.add_text('Combat screen', 20, (0, 0))
        self.text.set_background_color(self.bg_color)
        self.text.set_color(Color.BLACK)
        self.left_monster = self.add_sprite(placeholder_sprite, (50, 100))
        self.right_monster = self.add_sprite(placeholder_sprite, (150, 100))
        self.round_number = None
        self.monsters = None

    def draw_screen(self, attacks):
        self.round_number = -1
        monster_left = attacks.get_attack(0, 0).monster
        monster_right = attacks.get_attack(1, 0).monster
        self.monsters = [monster_left, monster_right]
        if Options.headless:
            return
        self.left_monster.set_surface(self.monster_sprites.get_sprite(
            monster_left.type, monster_left.owner))
        self.right_monster.set_surface(self.monster_sprites.get_sprite(
            monster_right.type, monster_right.owner))
        self.queue_for_background_update()

    def show_attack(self, combat_log: CombatLog):
        self.round_number += 1
        round_ = combat_log.rounds[self.round_number]
        attacker = self.monsters[round_.side]
        if round_.damage >= 0:
            attacks = f'does {round_.damage} damage to'
        else:
            attacks = 'misses'
        targeted_side = (round_.side + 1) % 2
        target = f'{self.monsters[targeted_side]}'
        self.text.set_text(
            f'{attacker} {attacks} {target} ({self.round_number + 1})')
        self.queue_for_background_update()
        logging.info(self.text.text)
        delay = self.COMBAT_DELAY
        if self.round_number == len(combat_log.rounds) - 1:
            delay = delay * -1
        return delay
