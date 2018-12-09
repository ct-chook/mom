import logging
from math import floor

import pygame
from pygame.rect import Rect

from src.abstract.view import View
from src.abstract.window import Window, YesNoWindow
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
from src.helper.Misc.tileblitter import TileBlitter
from src.helper.events.events import Event, EventQueue
from src.helper.events.factory import PathEventFactory
from src.model.board_model import BoardModel
from src.helper import selectionhandler


class BoardController(Window):
    """Contains controller, and the model containing the board"""
    directions = {pygame.K_LEFT: (-1, 0), pygame.K_RIGHT: (1, 0),
                  pygame.K_DOWN: (0, 1), pygame.K_UP: (0, -1)}

    def __init__(self, x, y, width, height, mapname='test'):
        super().__init__(x, y, width, height)
        self.mapname = mapname
        self.path_event_factory = None

        self.model = BoardModel(mapname)
        self.camera = Rect(
            (0, 0), (Options.camera_width, Options.camera_height))
        self.view: BoardView = self.add_view(BoardView,
                                             (self.camera, self.model))

        # todo camera should be part of controller instead?
        self.pos_converter = PosConverter(
            self.camera, self.model.board.x_max, self.model.board.y_max)
        self.actionlog_handler = ActionLogHandler(self)
        if self.view:
            self.path_event_factory = PathEventFactory(
                self.view.on_path_animation)

        # Windows
        self.combat_window: CombatWindow = self.attach_controller(
            CombatWindow())
        self.precombat_window: PreCombatWindow = self.attach_controller(
            PreCombatWindow(self.model, self.combat_window))
        self.summon_window: SummonWindow = self.attach_controller(
            SummonWindow(self.model))
        self.sidebar: Sidebar = self.attach_controller(Sidebar())
        self.tower_capture_window: TowerCaptureWindow = self.attach_controller(
            TowerCaptureWindow())
        self.tile_editor_window: TileEditorWindow = self.attach_controller(
            TileEditorWindow())
        self.minimap_window: MinimapController = self.attach_controller(
            MinimapController(self.model.board))
        self.end_of_turn_window: YesNoWindow = self.attach_controller(
            YesNoWindow('Do you want to end your turn?',
                        self.handle_end_of_turn, None))

        self.end_of_turn_window.hide()

    def handle_mouseclick(self):
        assert self.mouse_pos[0] >= 0 and self.mouse_pos[1] >= 0, \
            'Position was calculated as outside the controller'
        tile_pos = self.get_tile_pos_at_mouse()
        self.handle_tile_selection(tile_pos)

    def handle_right_mouseclick(self):
        tile_pos = self.get_tile_pos_at_mouse()
        if tile_pos[0] == -1:
            return
        self.view.center_camera_on(tile_pos)

    def handle_mouseover(self):
        tile_pos = self.get_tile_pos_at_mouse()
        tile = self.model.board.tile_at(tile_pos)
        self.sidebar.display_tile_info(tile)

    def get_tile_pos_at_mouse(self):
        return self.pos_converter.mouse_to_board(self.mouse_pos)

    def handle_tile_selection(self, tile_pos):
        if self._tile_edit_mode_is_active():
            terrain = self.tile_editor_window.selected_terrain
            self.model.board.on_tile(tile_pos).set_terrain_to(terrain)
            self.view.queue_for_background_update()
        else:
            self.model.select_tile(tile_pos)
            action_log = self.model.selection_handler.actionlog
            self.actionlog_handler.process(action_log)

    def _tile_edit_mode_is_active(self):
        return self.tile_editor_window.selected_terrain is not None

    def handle_keypress(self, key):
        if key in self.directions:
            self.handle_arrow_key(key)
        elif key == pygame.K_s:
            self.handle_key_k()
        elif key == pygame.K_SPACE:
            self.handle_key_space()

    def handle_key_space(self):
        self.end_of_turn_window.show()
        self.view.queue_for_background_update()

    def handle_key_k(self):
        terrain = [self.model.board.x_max, self.model.board.y_max]
        for col in self.model.board.tiles:
            for tile in col:
                terrain.append(tile.terrain)
        print(terrain)

    def handle_arrow_key(self, key):
        self.view.move_camera(self.directions[key])

    def handle_end_of_turn(self):
        self.model.on_end_turn()
        current_player = self.model.players.get_current_player()
        self.sidebar.display_turn_info(current_player, self.model.sun_stance)
        if not current_player.ai_type == AiType.human:
            self.handle_ai_start_turn(current_player)

    def handle_ai_start_turn(self, current_player):
        """The ai must take over the controller until they end their turn
        do this by disabling the controller, and have the ai send events
        to control itself
        every event should fetch an ai action from the brain, display this
        action to the controller/view, and then send it to the model
        this happens until the brain decides to end its turn
        """
        action = current_player.get_next_ai_action()
        assert action, 'AI action requested but no action received'
        if action.end_turn:
            end_turn_event = Event(
                self.handle_end_of_turn,
                name=f'AI {current_player.number} end turn')
            EventQueue(end_turn_event).subscribe()
        else:
            raise AttributeError(
                f'I don\'t know how to deal with this AI action. {action}')


class ActionLogHandler:
    def __init__(self, controller):
        self.controller = controller

    def process(self, action_log):
        """Performs necessary actions using log retrieved from selector.

        From a mouseclick, the following can happen:
        - A monster moves, has event queue that needs to be added
        - A monster moves and attacks, has event queue that needs
        appending, controller has to open combat window and have event queue
        link to that and also display movement event. Movement event callback
        can be received from the view with repeats for length of path. The
        combat event can be retrieved from the combat log with callbacks to the
        combat window so the move event has to be made by the model first and
        then the combat event can be added to it by the controller so it needs
        to receive the combat log and the event queue so it can add to the
        event queue using its own function to open the combat window, and pass
        the combat log to the combat window.
        """
        if not action_log:
            raise AttributeError('Action log was "None"')
        flag = action_log.next_action
        if flag == selectionhandler.ActionFlag.SHOW_COMBAT_SCREEN:
            self._show_combat_screen(action_log)
        elif flag == selectionhandler.ActionFlag.SHOW_PRE_COMBAT_SCREEN:
            self._show_precombat_window(action_log)
        elif flag == selectionhandler.ActionFlag.SELECT_ENEMY:
            self._handle_monster_movement(action_log)
        elif flag == selectionhandler.ActionFlag.SUMMON_MONSTER:
            self._handle_choose_summon(action_log)
        elif flag == selectionhandler.ActionFlag.MOVE_MONSTER:
            self._handle_monster_movement(action_log)
        elif flag == selectionhandler.ActionFlag.SELECT_MONSTER:
            self._handle_monster_selection(action_log)
        elif flag == selectionhandler.ActionFlag.CAPTURE_TOWER:
            self._handle_tower_capture(action_log)

    def _show_combat_screen(self, action_log):
        """ todo:
        there are two functions that handle combat
        merge them into one
        """
        combat_log = action_log.combat_log
        event_queue = action_log.get_event_queue()
        if event_queue:
            # todo enabling of controller should be part of event log
            open_combat_window_event = Event(
                self.controller.combat_window.show)
            event_queue.append(open_combat_window_event)
        else:
            self.controller.combat_window.show_combat(combat_log)

    def _show_precombat_window(self, action_log):
        self.controller.precombat_window.show()
        self.controller.precombat_window.set_attackers(
            action_log.combat_monsters)

    def _handle_monster_selection(self, actionlog):
        tiles_to_highlight = actionlog.tiles_to_highlight
        # todo view reference
        self.controller.view.highlight_tiles(tiles_to_highlight)

    def _handle_monster_movement(self, action_log):
        monster = action_log.monster
        path = action_log.path
        self._add_movement_event(monster, path)
        self.controller.minimap_window.view.queue_for_background_update()

    def _add_movement_event(self, monster, path):
        assert monster
        assert path
        self.controller.view.init_path_animation(monster, path)
        # todo view references
        movement_event = Event(self.controller.view.on_path_animation)
        clear_highlight_event = Event(
            self.controller.view.clear_highlighted_tiles)
        return EventQueue((movement_event, clear_highlight_event))

    def _handle_tower_capture(self, action_log):
        monster = action_log.monster
        path = action_log.path
        eventqueue = self._add_movement_event(monster, path)
        tower_capture_event = (
            Event(self.controller.tower_capture_window.show),
            Event(self.controller.tower_capture_window.view.show_capture),
            Event(self.controller.tower_capture_window.hide))
        eventqueue.append(tower_capture_event)

    def _handle_choose_summon(self, actionlog):
        x, y = actionlog.pos
        logging.info(f'Picked {(x, y)} for summon location')
        self._show_summon_window(actionlog)

    def _show_summon_window(self, actionlog):
        logging.info('Showing summon window')
        self.controller.summon_window.show()
        self.controller.summon_window.set_summon_pos(actionlog.pos)


class BoardView(View):
    verbose = 1

    def __init__(self, rectangle, arguments):
        camera, board_model = arguments
        super().__init__(rectangle)
        self.set_bg_color(Color.WHITE)
        self.camera = camera
        self.monster_width = Options.tile_width
        self.monster_height = Options.tile_height
        self.tile_width = Options.tile_width
        self.tile_height = Options.tile_height
        self.pos_converter = None
        self.path_animation = None
        self.path_index = None
        self.monster_to_sprite = None

        self.board_model = None
        self.board = None
        self.tile_blitter: TileBlitter = None
        self.link_to_board_model(board_model)
        self.add_text('Board view')
        self.monster_sprites = \
            SpriteSheetFactory().get_monster_spritesheets()
        self.create_sprites_for_board_in_view()

        self.tiles_to_highlight = None

    def link_to_board_model(self, board_model):
        self.board_model = board_model
        self.board = board_model.board
        self.tile_blitter = TileBlitter(self, self.board, self.camera)
        x_max = self.board.x_max
        y_max = self.board.y_max
        self.pos_converter = PosConverter(self.camera, x_max, y_max)

    def highlight_tiles(self, tiles):
        self.tiles_to_highlight = tiles
        self.queue_for_background_update()

    def clear_highlighted_tiles(self):
        self.tiles_to_highlight = None
        self.queue_for_background_update()

    def move_camera(self, dxy):
        center_x, center_y = self.get_center_tile(dxy)
        print(f'center: {(center_x, center_y)}')
        if (center_x < 0 or center_y < 0 or center_x >= self.board.x_max or
                center_y >= self.board.y_max):
            return
        old_camera_x = self.camera.x
        old_camera_y = self.camera.y
        dx, dy = dxy
        new_camera_x = old_camera_x + dx
        new_camera_y = old_camera_y + dy
        self.camera.x = new_camera_x
        self.camera.y = new_camera_y
        self.create_sprites_for_board_in_view()
        self.queue_for_background_update()
        print(f'new pos: {self.camera.x},{self.camera.y}')

    def get_center_tile(self, dxy):
        dx, dy = dxy
        return (self.camera.x + dx + floor(self.camera.width / 2),
                self.camera.y + dy + floor(self.camera.height / 2))

    def center_camera_on(self, pos):
        # todo pos should be centered on board
        x, y = pos
        self.camera.x = x - self.camera.width / 2
        self.camera.y = y - self.camera.height / 2
        self.create_sprites_for_board_in_view()
        self.queue_for_background_update()
        print(f'new pos: {self.camera.x},{self.camera.y}')

    def update_background(self):
        self.background.fill(self.bg_color)
        self.tile_blitter.blit_all_tiles()
        super().update_background()
        logging.info('updated surface of board')

    def init_path_animation(self, monster, path):
        self.path_animation = (path, monster)
        self.path_index = 0

    def on_path_animation(self):
        path, monster = self.path_animation
        if self.path_index >= len(path):
            return 0
        logging.info(f'doing movement animation')
        pos_on_path = path[self.path_index]
        self.path_index += 1
        if monster not in self.monster_to_sprite:
            logging.info(
                f'Tried to animate monster {monster.name} but not in dict. '
                'This means that the sprite is outside camera view, or '
                'simply was never created')
            return 6
        sprite = self.monster_to_sprite[monster]
        surface_pos = self.pos_converter.board_to_surface_pos(pos_on_path)
        sprite.rect.x = surface_pos[0]
        sprite.rect.y = surface_pos[1]
        self.queue_for_background_update()
        return 6

    def create_sprites_for_board_in_view(self):
        self.sprites.empty()
        self.monster_to_sprite = {}
        for key in self.board.monsters:
            monsterlist = self.board.monsters[key]
            self.create_sprites_from_monsterlist(monsterlist)

    def create_sprites_from_monsterlist(self, monsterlist):
        for monster in monsterlist:
            if self.monster_is_within_camera_view(monster):
                self.create_sprite_for_monster(monster)
        pass

    def monster_is_within_camera_view(self, monster):
        adjusted_pos_not_negative = (
                monster.pos[0] >= self.camera.x and
                monster.pos[1] >= self.camera.y)
        adjusted_pos_not_too_high = (
                monster.pos[0] < self.camera.x + self.camera.width and
                monster.pos[1] < self.camera.y + self.camera.height)
        return adjusted_pos_not_negative and adjusted_pos_not_too_high

    def create_sprite_for_monster(self, monster):
        try:
            sprite_surface = self.monster_sprites.get_sprite(
                monster.stats.id, monster.owner)
        except IndexError:
            print(f'trying to fetch a sprite for {monster.stats.id}, but '
                  'sprite was not found')
            return
        offset = self.pos_converter.board_to_surface_pos(monster.pos)
        self.monster_to_sprite[monster] = self.add_sprite(
            sprite_surface, offset)
        logging.info(f'sprite added for {monster.name} ({monster.owner})')
