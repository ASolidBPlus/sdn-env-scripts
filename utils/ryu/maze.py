import os
import time
import threading
import queue

MAZE = [
    "███████████████████████████████████████████",
    "█     █                                   █",
    "█     █                                   █",
    "█  @  █                                   █",
    "█     █                                   █",
    "█     █                                   █",
    "█     ███████     ███████████████████     █",
    "█           █           █           █     █",
    "█           █           █           █     █",
    "█           █           █           █     █",
    "█           █           █           █     █",
    "█           █           █           █     █",
    "███████     ███████     █     ███████     █",
    "█     █     █           █     █           █",
    "█     █     █           █     █           █",
    "█     █     █           █     █           █",
    "█     █     █           █     █           █",
    "█     █     █           █     █           █",
    "█     █     █     ███████     █     ███████",
    "█                 █                       █",
    "█                 █                       █",
    "█                 █                       █",
    "█                 █                       █",
    "█                 █                       █",
    "███████████████████████████████████████████",
]

CAT_FACE = "(=^･ω･^=)"
FACE_WIDTH = len(CAT_FACE)

# Internal ping→direction mapping
PING_MAP = {
    "1.1.1.1": "←",
    "2.2.2.2": "→",
    "3.3.3.3": "↑",
    "4.4.4.4": "↓",
}

class Maze:
    def __init__(self):
        self.maze = [list(row) for row in MAZE]
        self.height = len(self.maze)
        self.width = len(self.maze[0])
        for y, row in enumerate(self.maze):
            for x, ch in enumerate(row):
                if ch == '@':
                    self.start_x, self.start_y = x, y
                    self.maze[y][x] = ' '
        self.mouse_x, self.mouse_y = self.start_x, self.start_y

        open_cells = [
            (x, y)
            for y in range(self.height)
            for x in range(self.width)
            if self.maze[y][x] == ' '
        ]
        raw_x, raw_y = max(
            open_cells,
            key=lambda p: abs(p[0] - self.start_x) + abs(p[1] - self.start_y)
        )
        self.cat_x = min(raw_x, self.width - FACE_WIDTH)
        self.cat_y = raw_y

        self.pings = 0
        self.bumps = 0
        self.log = []
        self.game_over = False
        self._queue = queue.Queue()
        self.ping_map = PING_MAP

    def start(self):
        self.draw()  # initial render
        t = threading.Thread(target=self._run, daemon=True)
        t.start()

    def _run(self):
        while not self.game_over:
            dx, dy = self._queue.get()
            self._do_move(dx, dy)
            if self.game_over:
                break

    def _print_maze(self, highlight=None):
        for y in range(self.height):
            x = 0
            line = ''
            while x < self.width:
                if highlight and (x, y) in highlight:
                    line += highlight[(x, y)]
                    x += 1
                elif x == self.mouse_x and y == self.mouse_y:
                    line += 'o'
                    x += 1
                elif (y == self.cat_y and
                      self.cat_x <= x < self.cat_x + FACE_WIDTH):
                    offset = x - self.cat_x
                    line += CAT_FACE[offset]
                    x += 1
                else:
                    line += self.maze[y][x]
                    x += 1
            print(line)

    def draw(self):
        os.system('clear')
        self._print_maze()
        print(f"Pings: {self.pings}  Bumps: {self.bumps}")
        print("Recent Moves (last 5):")
        for entry in self.log[-5:]:
            print(f"  {entry}")
        # persistent ping→direction menu
        print("\nPing → Direction")
        for ip, arrow in self.ping_map.items():
            print(f"  {ip:<15} : {arrow}")

    def _do_move(self, dx, dy):
        dir_map = {
            (0, -1): 'up',
            (0, 1): 'down',
            (-1, 0): 'left',
            (1, 0): 'right'
        }
        dir_str = dir_map.get((dx, dy), 'move')
        self.pings += 1
        nx, ny = self.mouse_x + dx, self.mouse_y + dy
        is_cat = (
            ny == self.cat_y and 
            self.cat_x <= nx < self.cat_x + FACE_WIDTH
        )
        if (0 <= nx < self.width and 
            0 <= ny < self.height and
            (self.maze[ny][nx] == ' ' or is_cat)):
            self.mouse_x, self.mouse_y = nx, ny
            self.log.append(f"Moved {dir_str} ✔")
            self.draw()
            if is_cat:
                self.finish()
        else:
            self.bumps += 1
            self.log.append(f"Bumped into wall moving {dir_str} ✖")
            self.animate_bump(nx, ny)

    def animate_bump(self, bx, by):
        for _ in range(2):
            self.draw()
            time.sleep(0.1)
            os.system('clear')
            self._print_maze(highlight={(bx, by): 'X'})
            time.sleep(0.1)
        self.draw()

    def animate_cat_blink(self):
        for f in ('x', ' '):
            os.system('clear')
            highlights = {
                (self.cat_x + i, self.cat_y): f
                for i in range(FACE_WIDTH)
            }
            self._print_maze(highlight=highlights)
            time.sleep(0.3)

    def finish(self):
        self.game_over = True
        self.animate_cat_blink()
        time.sleep(0.2)
        os.system('clear')
        alive = [" /\\_/\\ ", "( ^.^ )", " > ^ < "]
        dead  = [" /\\_/\\ ", "( x.x )", " >   < "]
        for frame in (alive, dead):
            for line in frame:
                print(line)
            time.sleep(0.5)
            os.system('clear')
        for line in dead:
            print(line)
        cp, cb = self.pings, self.bumps
        print(f"\nYou killed the cat! It took you {cp} pings, and you bumped {cb} times!")

    def up(self):
        self._queue.put((0, -1))

    def down(self):
        self._queue.put((0, 1))

    def left(self):
        self._queue.put((-1, 0))

    def right(self):
        self._queue.put((1, 0))

