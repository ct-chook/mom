import logging
import pygame
from math import floor

from src.helper.Misc.constants import Color, ROOT
from src.helper.Misc.options_game import Options
from src.helper.textwrap.textwrapper import TextWrap


class Sprite(pygame.sprite.Sprite):
    main_display = None

    def __init__(self, surface, offset):
        super().__init__()
        self.offset = offset
        self.new_pos = None
        self.image = surface
        if surface:
            self.rect = pygame.Rect(
                offset[0], offset[1],
                surface.get_width(), surface.get_height())
        else:
            self.rect = pygame.Rect(offset[0], offset[1], 0, 0)

    def update(self):
        """Switches to next pos, do this after undrawing"""
        if not self.new_pos:
            return
        self.rect.x, self.rect.y = self.new_pos
        self.new_pos = None

    def set_surface(self, new_surface):
        self.image = new_surface


class Text(pygame.sprite.Sprite):
    """
    Options for text:
    size: font size
    font: font type
    color: font color
    """

    def __init__(self, text, offset, max_width=None,
                 color=Color.WHITE, size=16, background_color=None,
                 font='menlo'):

        super().__init__()
        self.image = None
        self.x, self.y = offset
        self.rect = pygame.Rect((self.x, self.y, 0, 0))

        self.text = text
        self.new_text = None
        self.max_width = max_width
        self.offset = offset
        self.color = color
        self.size = size
        self.background_color = background_color
        self.cache = {}

        if Options.headless:
            return
        self.font = pygame.font.Font(f'{ROOT}/{font}.ttc', self.size)
        self.char_width = self.font.size('aa')[0] - self.font.size('a')[0]
        self.update_surface()

    def set_text(self, new_text):
        self.new_text = str(new_text)

    def update(self):
        if self.new_text is None:
            return
        self.set_new_text_to_surface()

    def set_new_text_to_surface(self):
        # logging.info(
        #     f'Old text {self.text}: {self.rect.width}x{self.rect.height}')
        if self.text not in self.cache:
            self.cache[self.text] = self.image
        self.text = self.new_text
        self.new_text = None
        if self.text in self.cache:
            # set surface directly from cache
            # logging.info(f'Using cached text')
            self.image = self.cache[self.text]
        else:
            self.update_surface()
        self._set_rect_to_text_size()
        # logging.info(
        #     f'New text {self.text}: {self.rect.width}x{self.rect.height}')

    def set_color(self, new_color):
        self.color = new_color
        self.update_surface()

    def update_surface(self):
        if Options.headless:
            return
        # cut text into lines bound by max width
        lines = self._get_lines()
        line_surfaces = self._get_line_surfaces(lines)
        self._draw_text_on_surface(line_surfaces)

    def _set_rect_to_text_size(self):
        if Options.headless:
            return
        # make sure to update width and height
        self.rect.width = self.image.get_width()
        self.rect.height = self.image.get_height()

    def _get_lines(self):
        if not self.max_width:
            # if no max width specified (not recommended), return whole string
            return self.text,
        max_chars_per_line = floor(self.max_width / self.char_width)
        textwrapper = TextWrap()
        lines = textwrapper.wrap(self.text, max_chars_per_line)
        return lines

    def _get_line_surfaces(self, lines):
        line_surfaces = []
        for line in lines:
            line_surfaces.append(
                self.font.render(line, True, self.color, self.background_color))
        return line_surfaces

    def _draw_text_on_surface(self, line_surfaces):
        max_width = get_max_surface_width(line_surfaces)
        total_height = get_total_surface_height(line_surfaces)
        self.image = pygame.Surface((max_width, total_height))
        if self.background_color:
            self.image.fill(self.background_color)
        y_offset = 0
        for line_surface in line_surfaces:
            self.image.blit(line_surface, (0, y_offset))
            y_offset += line_surface.get_height()

    def set_background_color(self, color):
        """Performance for text on solid color can be improved

        For solid colored backgrounds, the bg color can be specified. See:
        https://www.pygame.org/docs/ref/font.html#pygame.font.Font.render
        """
        self.background_color = color


class View:
    main_display = None

    def __init__(self, rectangle):
        self.rectangle: pygame.rect.Rect = rectangle
        self.parent: View = None
        self.children: [View] = []
        self.visible = True

        self.background: pygame.Surface = None
        self.sprites = pygame.sprite.RenderUpdates()
        self.texts = pygame.sprite.RenderUpdates()
        self.surface: pygame.Surface = None
        self.bg_color = Color.LIGHT_BLUE

        if Options.headless:
            return
        # noinspection PyArgumentList
        self.background = pygame.Surface(
            (rectangle.width, rectangle.height)).convert()
        # noinspection PyArgumentList
        self.surface = pygame.Surface(
            (rectangle.width, rectangle.height)).convert()

    def initialize_background(self):
        if Options.headless:
            return
        logging.info(f'Initializing background for {self}')
        self.background = pygame.Surface(
            (self.rectangle.width, self.rectangle.height))
        self.background.fill(self.bg_color)
        self.surface = pygame.Surface(
            (self.rectangle.width, self.rectangle.height))
        self.queue_for_background_update()

    def queue_for_background_update(self):
        if self.main_display:
            self.main_display.add_view_to_update_queue(self)
        self.queue_for_sprite_update()

    def queue_for_sprite_update(self):
        if self.main_display:
            self.main_display.add_sprites_to_update_queue(self)

    def update_background(self):
        """Gives order to redraw background on screen"""
        if Options.headless:
            return
        if not self.surface:
            raise AttributeError(
                f'{self} tried to update background but had no surface')
        logging.info(f'Redrawing background of {self}')
        self.surface.blit(self.background, self.background.get_rect())

    def add_sprite(self, surface: pygame.Surface, offset: tuple) -> Sprite:
        new_sprite: Sprite = Sprite(surface, offset)
        self.sprites.add(new_sprite)
        self.queue_for_sprite_update()
        return new_sprite

    def add_text(
            self, input_text: str, size: int = 16, offset: tuple = (0, 0),
            max_width: int = None):

        if not max_width:
            max_width = self._get_horizonal_space_till_end_of_view(offset[0])
        text = Text(
            input_text, offset,
            max_width=max_width, size=size)
        self.texts.add(text)
        self.queue_for_sprite_update()
        return text

    def _get_horizonal_space_till_end_of_view(self, x):
        return self.rectangle.width - x

    def update_sprites(self):
        """Gives order to redraw sprites and text on screen"""
        if not self.sprites and not self.texts:
            return []
        logging.info(
            f'redrawing {len(self.sprites)} sprites and {len(self.texts)} '
            f'text sprites for {self}')
        updated_rects = self.redraw_sprites(self.sprites)
        updated_rects.extend(self.redraw_sprites(self.texts))
        return updated_rects

    def redraw_sprites(self, sprite_group):
        """Redraws a provided group of sprites on the view

        The renderUpdates class keeps track of areas of the screen that were
        changed, including cleared areas.
        """
        if Options.headless:
            sprite_group.update()
            return []
        sprite_group.clear(self.surface, self.background)
        sprite_group.update()
        return sprite_group.draw(self.surface)

    def get_global_offset(self):
        """Returns the xy pos of a view on the main display

        Each rectangle has its position on its parent stored. To get the
        position on the main display instead, use this method.
        """
        rect = self.get_absolute_rectangle()
        return rect.x, rect.y

    def get_absolute_rectangle(self):
        """Returns a rectangle with absolute, i.e. main display-oriented pos

        Use this for blitting to the main display
        """
        if not self.parent:
            return self.rectangle
        parent_rectangle = self.parent.get_absolute_rectangle()
        return pygame.Rect((
            parent_rectangle.x + self.rectangle.x,
            parent_rectangle.y + self.rectangle.y,
            self.rectangle.width,
            self.rectangle.height))

    def blit_to_display(self, x_offset, y_offset):
        """Blit this view and underlaying views on the display"""
        if self.rectangle:
            x = x_offset + self.rectangle.x
            y = y_offset + self.rectangle.y
            self._blit_surface_to_display((x, y))
        else:
            # if no rectangle, do blit children, but not self
            x = 0
            y = 0
        self._blit_children(x, y)

    def _blit_surface_to_display(self, pos):
        """Blit this view on the display"""
        assert self.visible
        logging.info(f'Blitting {self} to display')
        self.main_display.blit(self.surface, pos)

    def _blit_children(self, parent_x, parent_y):
        """Gives orders to the children of this view to blit themselves"""
        for view in self.children:
            if view.visible:
                view.blit_to_display(parent_x, parent_y)

    def _set_position(self, x, y):
        self.rectangle.x = x
        self.rectangle.y = y

    def _set_dimensions(self, width, height):
        self.rectangle.width = width
        self.rectangle.height = height

    def add_child_view(self, view):
        self.children.append(view)

    def set_bg_color(self, bg_color):
        self.bg_color = bg_color

    def __str__(self):
        return self.__class__.__name__


def get_max_surface_width(surfaces):
    max_width = 0
    for surface in surfaces:
        if surface.get_width() > max_width:
            max_width = surface.get_width()
    return max_width


def get_total_surface_height(surfaces):
    total_height = 0
    for surface in surfaces:
        total_height += surface.get_height()
    return total_height


class ButtonMatrixView(View):
    # todo move this to a button module
    def __init__(self, rectangle):
        super().__init__(rectangle)

    def set_sprite_for_button(self, index):
        pass
