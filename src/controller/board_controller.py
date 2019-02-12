import logging
import pygame

from math import floor
from pygame.rect import Rect

from src.components.board.board import Board
from src.controller.statusbar_controller import StatusbarController
from src.handlers.selectionhandler import SelectionHandler
from src.abstract.view import View
from src.abstract.window import Window
from src.controller.yesno_controller import YesNoWindow
from src.components.board.brain import PlayerIdleBrain, PlayerDefaultBrain
from src.controller.combat_controller import CombatWindow
from src.controller.minimap_controller import MinimapController
from src.controller.precombat_controller import PreCombatWindow
from src.controller.sidebar_controller import Sidebar
from src.controller.summon_controller import SummonWindow
from src.controller.tile_editor_controller import TileEditorWindow
from src.controller.towercapture_controller import TowerCaptureWindow
from src.helper.Misc.constants import Color, AiType
from src.helper.Misc.options_game import Options
from src.helper.Misc.posconverter import PosConverter
from src.helper.Misc.spritesheet import SpriteSheetFactory
from src.helper.Misc.tileblitter import BoardBlitter
from src.helper.events import EventCallback
from src.model.board_model import BoardModel


class BoardController(Window):
    """Contains controller, and the model containing the board"""
    directions = {pygame.K_LEFT: (-1, 0), pygame.K_RIGHT: (1, 0),
                  pygame.K_DOWN: (0, 1), pygame.K_UP: (0, -1)}

    def __init__(self, x, y, width, height, info, mapoptions):
        super().__init__(x, y, width, height, info)
        self.path_event_factory = None
        self.is_ai_controlled = False
        self.camera = Rect(
            (0, 0),
            (self.config.camera_width, self.config.camera_height))
        self.brains = {}

        self.model = BoardModel(mapoptions)
        self.view: BoardView = self.add_view(
            BoardView,
            self.camera,
            self.model,
            info.config)
        self.pos_converter = PosConverter(
            self.camera,
            self.model.board.x_max,
            self.model.board.y_max,
            info.config.tile_width,
            info.config.tile_height)
        self.selection_handler = SelectionHandler(
            self.model.board,
            self.model, self)

        # Windows
        self.combat_window: CombatWindow = self.attach_controller(
            CombatWindow(info))
        self.precombat_window: PreCombatWindow = self.attach_controller(
            PreCombatWindow(
                info,
                self.model,
                self.combat_window))
        self.summon_window: SummonWindow = self.attach_controller(
            SummonWindow(
                info,
                self.model))
        self.sidebar: Sidebar = self.attach_controller(Sidebar(info))
        self.tower_capture_window: TowerCaptureWindow = self.attach_controller(
            TowerCaptureWindow(info))
        self.tile_editor_window: TileEditorWindow = self.attach_controller(
            TileEditorWindow(info))
        self.minimap_window: MinimapController = self.attach_controller(
            MinimapController(
                info,
                self.model.board))
        self.end_of_turn_window: YesNoWindow = self.attach_controller(
            YesNoWindow(
                info,
                'Do you want to end your turn?',
                self.handle_end_of_turn,
                None))
        self.status_bar: StatusbarController = self.attach_controller(
            StatusbarController(
                0, 500,
                info,
                self.model))
        self.end_of_turn_window.hide()

        # AI stuff
        self.create_brains()

    def append_ai_callback(self):
        self.append_event(self.get_ai_action_event())

    def create_brains(self):
        for player in self.model.players:
            self._create_brain(player)

    def _create_brain(self, player):
        ai_type = player.ai_type
        if ai_type == AiType.human:
            return
        if ai_type == AiType.default:
            brain_class = PlayerDefaultBrain
        elif ai_type == AiType.idle:
            brain_class = PlayerIdleBrain
        else:
            brain_class = PlayerIdleBrain
        self.add_brain_for_player(brain_class, player)

    def add_brain_for_player(self, brain_class, player):
        self.brains[player] = brain_class(self, player)

    def handle_mouseclick(self):
        if self.is_ai_controlled:
            return
        assert self.mouse_pos[0] >= 0 and self.mouse_pos[1] >= 0, (
            'Position was calculated as outside the controller')
        tile_pos = self.get_tile_pos_at_mouse()
        self.handle_tile_selection(tile_pos)

    def handle_right_mouseclick(self):
        if self.is_ai_controlled:
            return
        tile_pos = self.get_tile_pos_at_mouse()
        if not tile_pos:
            return
        self.view.center_camera_on(tile_pos)

    def handle_mouseover(self):
        tile_pos = self.get_tile_pos_at_mouse()
        if not tile_pos:
            return
        tile = self.model.board.tile_at(tile_pos)
        self.sidebar.display_tile_info(tile)

    def get_tile_pos_at_mouse(self):
        return self.pos_converter.mouse_to_board(self.mouse_pos)

    def handle_tile_selection(self, tile_pos):
        if self._tile_edit_mode_is_active():
            if not self.model.board.is_valid_board_pos(tile_pos):
                return
            terrain = self.tile_editor_window.selected_terrain
            self.model.board.set_terrain_to(tile_pos, terrain)
            self.view.queue_for_background_update()
        else:
            self.selection_handler.click_tile(tile_pos)

    def _tile_edit_mode_is_active(self):
        return self.tile_editor_window.selected_terrain is not None

    def handle_keypress(self, key):
        if self.is_ai_controlled:
            return
        if key in self.directions:
            self._handle_arrow_key(key)
        elif key == pygame.K_s:
            self._handle_key_k()
        elif key == pygame.K_SPACE:
            self._handle_key_space()

    def _handle_key_k(self):
        """For now use this to print terrain to stdout"""
        terrain = [self.model.board.x_max, self.model.board.y_max]
        for col in self.model.board.tiles:
            for tile in col:
                terrain.append(tile.terrain)
        print(terrain)

    def _handle_arrow_key(self, key):
        self.view.move_camera(self.directions[key])

    def _handle_key_space(self):
        self.end_of_turn_window.show()
        self.view.queue_for_background_update()

    def highlight_tiles(self, posses):
        self.view.highlight_tiles(posses)

    def get_ai_action_event(self):
        return EventCallback(self._handle_ai_action, name='ai action')

    def _handle_ai_action(self):
        """The ai must take over the controller until they end their turn

        Every event should fetch an ai action from the brain, and send this
        action to the controller/view.
        The event should also include another call to this method if the AI's
        turn is not over yet.
        """
        brain = self._get_current_player_brain()
        assert brain, 'Tried to handle ai action for human'
        brain.do_action()

    def _get_current_player_brain(self):
        player = self.model.get_current_player()
        if player not in self.brains:
            return None
        return self.brains[player]

    def handle_move_monster(self, monster, path):
        """Accessed by either the selection handler or the brain

        Sends movement to model, and sends movement event to view. After that
        it checks if it is the computer's turn, in that case it adds an event
        to make the computer do another move.

        Moving a monster may result in a tower capture. We can check if
        destination is unoccupied tower and add a capture event directly
        after movement. The model should auto-capture tower upon moving
        """
        logging.info(f'Moving monster {monster}')
        pos = path[-1]
        if monster.pos != pos:
            assert self.model.board.monster_at(pos) is None, (
                f'Destination {pos} is occupied by '
                f'{self.model.board.monster_at(pos)}')
        self.model.move_monster_to(monster, pos)
        self.set_movement_events(monster, path)
        if self.model.has_capturable_tower_at(pos):
            self._handle_tower_capture(pos)

    def set_movement_events(self, monster, path):
        """Movement can work in two ways, either by player or by computer

        In the case of the player, something sends a signal to move x to y,
        which triggers an event for the view, as well as a change in the model
        The ai should have the same. But after the ai's event there should be
        a callback.

        So any asynchronous event, such as the movement in the view
        should have an option for a callback so the ai can chain it with
        another function.
        """
        assert monster
        assert path
        events = self.view.get_movement_events(monster, path)
        for event in events:
            self.append_event(event)
        self.minimap_window.update_view()

    def _handle_tower_capture(self, pos):
        self.model.capture_tower_at(pos)
        capture_event = self.tower_capture_window.show_capture
        freeze_callback = self.freeze_events
        self.append_callback(capture_event)
        self.append_callback(freeze_callback)
        self.status_bar.update_stats()

    def show_precombat_window_for(self, attacker, defender):
        assert attacker
        assert defender
        assert attacker is not defender
        self.precombat_window.show()
        self.precombat_window.set_attackers((attacker, defender))

    def handle_attack_order(self, monsters, attack_range):
        attacks = self.model.get_short_and_long_attacks(monsters)
        self.combat_window.on_combat(attacks, attack_range)
        attacker = attacks.get_attack(0, attack_range).monster
        defender = attacks.get_attack(1, attack_range).monster
        logging.info(f'{attacker} is attacking monster {defender}')
        self.freeze_events()

    def handle_combat_end(self, combat_log):
        self.model.process_combat_log(combat_log)
        self.status_bar.update_stats()
        if self.model.game_over:
            if self.parent:
                self.parent.running = False

    def handle_summon_order_at(self, pos):
        logging.info(f'Picked {pos} for summon location')
        self.summon_window.show()
        self.summon_window.set_summon_pos(pos)

    def handle_summon_monster(self, monster_type, pos):
        summoned_monster = self.model.summon_monster_at(monster_type, pos)
        if self.is_ai_controlled:
            self.view.center_camera_on(pos)
        if summoned_monster:
            self.view.create_sprite_for_monster(summoned_monster)
            self.view.queue_for_sprite_update()
            self.status_bar.update_stats()
        return summoned_monster

    def handle_end_of_turn(self):
        self.selection_handler.unselect_current_monster()
        self.selection_handler.unselect_enemy()
        self.model.on_end_turn()
        current_player = self.model.players.get_current_player()
        self.sidebar.display_turn_info(
            current_player,
            self.model.sun_stance.value)
        lord = self.model.board.get_lord_of(current_player)
        self.view.center_camera_on(lord.pos)
        self.is_ai_controlled = current_player.ai_type != AiType.human
        if self.is_ai_controlled:
            self.append_ai_callback()
        self.status_bar.update_stats()


PATH_ANIMATION_DELAY = 6


class BoardView(View):
    def __init__(self, rectangle, camera, board_model, config):
        super().__init__(rectangle)
        self.set_bg_color(Color.GRAY)
        self.camera = camera
        self.pos_converter = None
        self.path_animation = None
        self.path_index = None
        self.monster_sprites = {}
        self.tiles_to_highlight = None
        self.board_model: BoardModel = None
        self.board: Board = None
        self.board_blitter: BoardBlitter = None

        self.link_to_board_model(board_model, config)
        self.monster_spritesheet = (
            SpriteSheetFactory().get_monster_spritesheets())
        self.create_sprites_for_viewport()
        self.add_text('Board view')

    def link_to_board_model(self, board_model, config):
        self.board_model = board_model
        self.board = board_model.board
        tile_width = config.tile_width
        tile_height = config.tile_height
        self.board_blitter = BoardBlitter(
            self,
            self.board,
            self.camera,
            tile_width, tile_height)
        self.pos_converter = PosConverter(
            self.camera,
            self.board.x_max, self.board.y_max,
            tile_width, tile_height)

    def highlight_tiles(self, tiles):
        self.tiles_to_highlight = tiles
        self.queue_for_background_update()

    def clear_highlighted_tiles(self):
        self.highlight_tiles(None)

    def move_camera(self, dxy):
        dx, dy = dxy
        center_x, center_y = self._get_center_tile()
        new_center = (center_x + dx, center_y + dy)
        if not self.board.is_valid_board_pos(new_center):
            return
        self.center_camera_on(new_center)

    def _get_center_tile(self):
        return (self.camera.x + floor(self.camera.width / 2),
                self.camera.y + floor(self.camera.height / 2))

    def center_camera_on(self, pos):
        # todo pos should be centered on board
        x, y = pos
        self.camera.x = x - floor(self.camera.width / 2)
        self.camera.y = y - floor(self.camera.height / 2)
        self.create_sprites_for_viewport()
        self.queue_for_background_update()

    def update_background(self):
        if Options.headless:
            return
        self.board_blitter.blit_all_tiles()
        super().update_background()
        logging.info('updated surface of board')

    def get_movement_events(self, monster, path):
        """Returns all the callbacks needed to animate a moving monster"""
        self.path_animation = (path, monster)
        self.path_index = 0
        movement_event = EventCallback(
            self.on_path_animation,
            name='path anim')
        clear_highlight_event = EventCallback(
            self.clear_highlighted_tiles,
            name='clear highlight')
        return movement_event, clear_highlight_event

    def on_path_animation(self):
        """A callback used to animate a moving monster"""
        path, monster = self.path_animation
        if self.path_index >= len(path):
            return
        logging.info(f'doing movement animation')
        pos_on_path = path[self.path_index]
        if self.path_index % 4 == 0:
            self.center_camera_on(pos_on_path)
        self.path_index += 1
        if monster not in self.monster_sprites:
            logging.info(
                f'Tried to animate monster {monster.name} but not in dict. '
                'This means that the sprite is outside camera view, or '
                'simply was never created')
            return
        sprite = self.monster_sprites[monster]
        surface_pos = self.pos_converter.board_to_surface_pos(pos_on_path)
        sprite.rect.x, sprite.rect.y = surface_pos
        self.queue_for_sprite_update()
        return PATH_ANIMATION_DELAY

    def create_sprites_for_viewport(self):
        self.sprites.empty()
        self.monster_sprites = {}
        monsterlist = self._get_monsters_within_view()
        self.create_sprites_from_monsterlist(monsterlist)

    def _get_monsters_within_view(self):
        monsterlist = []
        x_min, x_max, y_min, y_max = self.get_dimensions_of_viewport()
        for y in range(y_min, y_max):
            for x in range(x_min, x_max):
                monster = self.board.monster_at((x, y))
                if monster:
                    monsterlist.append(monster)
        return monsterlist

    def get_dimensions_of_viewport(self):
        """Returns the coordinates of the piece of board visible"""
        x_min = max(self.camera.x, 0)
        y_min = max(self.camera.y, 0)
        x_max = min(self.camera.x + self.camera.height, self.board.x_max)
        y_max = min(self.camera.y + self.camera.height, self.board.y_max)
        return x_min, x_max, y_min, y_max

    def create_sprites_from_monsterlist(self, monsterlist):
        for monster in monsterlist:
            self.create_sprite_for_monster(monster)

    def create_sprite_for_monster(self, monster):
        try:
            sprite_surface = (
                self.monster_spritesheet
                .get_sprite(monster.stats.id, monster.owner.id_))
        except IndexError:
            print(f'trying to fetch a sprite for {monster.stats.id}, but '
                  'sprite was not found')
            return
        offset = self.pos_converter.board_to_surface_pos(monster.pos)
        self.monster_sprites[monster] = self.add_sprite(
            sprite_surface,
            offset)
        # logging.info(f'sprite added for {monster.name} ({monster.owner})')

    def highlight_monsters(self, enemies):
        tiles = []
        for enemy in enemies:
            tiles.append(enemy.pos)
        self.highlight_tiles(tiles)
