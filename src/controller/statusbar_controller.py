from src.abstract.view import View
from src.abstract.window import Window
from src.components.board.players import Player


class StatusbarController(Window):
    """Displayed at the bottom of the screen"""

    def __init__(self, x, y, model):
        super().__init__(x, y, 500, 200)
        self.add_view(StatusbarView)
        self.stats: [PlayerstatsController] = []

        players = model.players
        x = 0
        y = 0
        for player in players:
            self.stats.append(
                self.attach_controller(PlayerstatsController(x, y, player)))
            x += 70

    def update_stats(self):
        for stat in self.stats:
            stat.update_stats()


class StatusbarView(View):
    pass


class PlayerstatsController(Window):
    def __init__(self, x, y, player):
        super().__init__(x, y, 100, 100)
        self.player = player
        self.add_view(PlayerstatsView)
        self.update_stats()

    def update_stats(self):
        self.view.update_stats(self.player)


class PlayerstatsView(View):
    id_to_color = ('BLUE', 'RED', 'YELLOW', 'GREEN')

    def __init__(self, rectangle):
        super().__init__(rectangle)
        height = 20
        self.color = self.add_text(offset=(0, 0))
        self.monsters = self.add_text(offset=(0, height))
        self.mp = self.add_text(offset=(0, height * 2))

    def update_stats(self, player: Player):
        color_text = f'{self.id_to_color[player.id_]}'
        monster_text = f'{player.monster_count}/{player.tower_count + 1}'
        mp_text = f'{player.mana} MP'
        self.color.set_text(color_text)
        self.monsters.set_text(monster_text)
        self.mp.set_text(mp_text)
        self.color.update()
        self.monsters.update()
        self.mp.update()
        self.queue_for_sprite_update()
