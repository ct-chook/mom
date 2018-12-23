import logging
from math import floor

import pygame
from pygame.rect import Rect

from src.abstract.view import View
from src.abstract.window import Window, YesNoWindow
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
from src.helper.Misc.tileblitter import TileBlitter
from src.helper.events.events import EventCallback, EventList
from src.helper.events.factory import PathEventFactory
from src.helper.selectionhandler import SelectionHandler
from src.model.board_model import BoardModel


class BoardController(Window):
    """Contains controller, and the model containing the board"""
    directions = {pygame.K_LEFT: (-1, 0), pygame.K_RIGHT: (1, 0),
                  pygame.K_DOWN: (0, 1), pygame.K_UP: (0, -1)}

    def __init__(self, x, y, width, height, mapoptions=None):
        super().__init__(x, y, width, height)
        self.path_event_factory = None
        self.is_ai_controlled = False
        self.camera = Rect(
            (0, 0), (Options.camera_width, Options.camera_height))
        self.brains = {}

        self.model = BoardModel(mapoptions)
        self.view: BoardView = self.add_view(BoardView,
                                             (self.camera, self.model))

        self.pos_converter = PosConverter(
            self.camera, self.model.board.x_max, self.model.board.y_max)
        self.selection_handler = SelectionHandler(
            self.model.board, self.model, self)
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
        self.create_brains()

    def create_brains(self):
        for player in self.model.get_players():
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
        assert self.mouse_pos[0] >= 0 and self.mouse_pos[1] >= 0, \
            'Position was calculated as outside the controller'
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
            terrain = self.tile_editor_window.selected_terrain
            self.model.board.on_tile(tile_pos).set_terrain_to(terrain)
            self.view.queue_for_background_update()
        else:
            self.selection_handler.click_tile(tile_pos)
            # self.actionlog_handler.process(action_log)

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

    def _handle_key_space(self):
        self.end_of_turn_window.show()
        self.view.queue_for_background_update()

    def _handle_key_k(self):
        terrain = [self.model.board.x_max, self.model.board.y_max]
        for col in self.model.board.tiles:
            for tile in col:
                terrain.append(tile.terrain)
        print(terrain)

    def _handle_arrow_key(self, key):
        self.view.move_camera(self.directions[key])

    def handle_end_of_turn(self):
        self.selection_handler.unselect_current_monster()
        self.selection_handler.unselect_enemy()
        self.model.on_end_turn()
        current_player = self.model.players.get_current_player()
        self.sidebar.display_turn_info(current_player, self.model.sun_stance)
        if current_player.ai_type == AiType.human:
            self.is_ai_controlled = False
        else:
            self.is_ai_controlled = True
            EventList(EventCallback(self._handle_ai_action))

    def handle_move_monster(self, monster, path):
        """Accessed by either the selection handler or the brain

        Sends movement to model, and sends movement event to view. After that
        it checks if it is the computer's turn, in that case it adds an event
        to make the computer do another move.

        Moving a monster may result in a tower capture. We can check if
        destination is unoccupied tower and add a capture event directly
        after movement. The model should auto-capture tower upon moving
        """
        logging.info('Moving monster')
        pos = path[-1]
        if self.model.has_capturable_tower_at(pos):
            tower_capture = True
        else:
            tower_capture = False
        self.model.move_monster_to(monster, pos)
        # todo get actual path
        eventlist = self.add_movement_event_to_view(monster, path)
        if tower_capture:
            self._handle_tower_capture(pos, eventlist)
        if self.is_ai_controlled:
            eventlist.append(self.get_ai_action_event())

    def get_ai_action_event(self):
        return EventCallback(
                self._handle_ai_action, name='ai action')

    def add_movement_event_to_view(self, monster, path):
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
        queue = self.view.add_movement_event(monster, path)
        self.minimap_window.update_view()
        return queue

    def _handle_tower_capture(self, pos, eventqueue):
        self.model.capture_tower_at(pos)
        tower_capture_events = self.tower_capture_window.get_capture_events()
        return eventqueue.append(tower_capture_events)

    def _handle_ai_action(self):
        """The ai must take over the controller until they end their turn

        Every event should fetch an ai action from the brain, display this
        action to the controller/view, and then send it to the model.
        this happens until the brain decides to end its turn.
        Each event
        """
        brain = self._get_current_player_brain()
        brain.do_action()

    def _get_current_player_brain(self):
        player = self.model.get_current_player()
        if player not in self.brains:
            raise AttributeError(f'Brain not found for player {player.id_}')
        return self.brains[player]

    def show_combat_window_for(self, attacker, defender):
        assert attacker
        assert defender
        assert attacker is not defender
        self.precombat_window.show()
        self.precombat_window.set_attackers((attacker, defender))

    def handle_attack_order(self, monsters, range_):
        attacker, defender = monsters
        attacker.moved = True
        logging.info(f'{attacker} is attacking monster {defender}')
        combat_log = self.model.get_combat_result(attacker, defender, range_)
        if combat_log.loser:
            logging.info(f'{combat_log.loser} was defeated!')

    def handle_summon_window_at(self, pos):
        x, y = pos
        logging.info(f'Picked {(x, y)} for summon location')
        self.summon_window.show()
        self.summon_window.set_summon_pos(pos)

    def handle_summon_monster(self, monster_type, pos):
        summoned_monster = self.model.summon_monster_at(
            monster_type, pos)
        if self.is_ai_controlled:
            EventList(EventCallback(self._handle_ai_action, name='ai action'))
        return summoned_monster

    def highlight_tiles(self, posses):
        self.view.highlight_tiles(posses)


PATH_ANIMATION_DELAY = 6


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

    def update_background(self):
        self.background.fill(self.bg_color)
        self.tile_blitter.blit_all_tiles()
        super().update_background()
        logging.info('updated surface of board')

    def add_movement_event(self, monster, path):
        self.path_animation = (path, monster)
        self.path_index = 0
        movement_event = EventCallback(self.on_path_animation, name='path anim')
        clear_highlight_event = EventCallback(
            self.clear_highlighted_tiles, name='clear highlight')
        return EventList((movement_event, clear_highlight_event))

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
            return PATH_ANIMATION_DELAY
        sprite = self.monster_to_sprite[monster]
        surface_pos = self.pos_converter.board_to_surface_pos(pos_on_path)
        sprite.rect.x = surface_pos[0]
        sprite.rect.y = surface_pos[1]
        self.queue_for_background_update()
        return PATH_ANIMATION_DELAY

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

    def highlight_monsters(self, enemies):
        tiles = []
        for enemy in enemies:
            tiles.append(enemy.pos)
        self.highlight_tiles(tiles)
