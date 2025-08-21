import copy
import os
import sys
import random
import time

from collections import deque
import heapq

#TODO: Make it use A* search and check turn validity
# Make it avoid creating a loop around itself?
# Make it actually simulate each move instead of just checking if
# there is a path using the current snake positions. Only use a that
# makes the tail reachable.
#
# Actually setting lookahead steps to a low number forces it to do
# a full search instead of A*, making it very slow.
#
# deepcopy is slow
# maybe only copy once when food reached?
# It's particularly slow due to the visited check, since it probably
# isn't caching at all
#
# It doesn't kill the snake for reverse moves when snake is length 1 or 2.

from contextlib import contextmanager
from pynput import keyboard

BORDER_HOR_CHAR = "-"
BORDER_VERT_CHAR = "|"

os.system("stty -echo")

class SnakeGame(object):
    def __init__(self, player, width, height, max_frame_rate=60):
        os.system("clear")
        self.player = player
        self.game_state = GameState(width, height)
        self.game_valid = True
        self.frame_time = 1.0 / max_frame_rate

    def play_game(self):
        rounds = 10000
        i = 0
        while self.game_valid and i < rounds:
            i += 1
            start = time.time()

            move = self.player.next_move(self.game_state)
            self.game_valid = self.game_state.update(move)
            self.render()

            finish = time.time()
            elapsed = finish - start
            remaining_time = self.frame_time - elapsed 
            if remaining_time > 0:
                time.sleep(remaining_time)

    def render(self):
        #os.system('clear') # causes flickering.

        # This resets to home position instead of clearing
        sys.stdout.write("\033[H")

        width, height = self.game_state.dim()
        output = ""
        #print(BORDER_HOR_CHAR * (width+2))
        output += BORDER_HOR_CHAR * (width+2) + "\n"
        for j in range(height):
            row = ""
            row += BORDER_VERT_CHAR
            for i in range(width):
                if (i, j) in self.game_state.filled_squares:
                    char = self.game_state.filled_squares[(i, j)]
                    row += char
                else:
                    row += " "

            row += BORDER_VERT_CHAR + "\n"
            output += row
            #print(row)
        output += BORDER_HOR_CHAR * (width+2) + "\n"
        #print(BORDER_HOR_CHAR * (width+2))
        print(output)

class SnakeNode(object):
    def __init__(self, i, j):
        self.left = None
        self.right = None
        self.pos = (i, j)

    def __str__(self):
        output = ""
        if self.left:
            output += "<-"
        output = "[" + str(self.pos) + "]"
        if self.right:
            output += "->"
        return output

def deepcopy_snake(snake):
    snake_copy = SnakeList()
    snake_copy.size = snake.size
    if snake_copy.size == 0:
        return snake_copy

    prev_copy = None
    curr = snake.head
    while curr:
        i, j = curr.pos
        node = SnakeNode(i, j) 

        if not snake_copy.head:
            snake_copy.head = node

        if prev_copy:
            node.left = prev_copy
            prev_copy.right = node

        prev_copy = node
        curr = curr.right

    snake_copy.tail = prev_copy
    return snake_copy

def deepcopy_gamestate(game_state):
    game_state_copy = GameState(game_state.width, game_state.height)
    game_state_copy.snake = deepcopy_snake(game_state.snake)
    game_state_copy.food_pos = game_state.food_pos

    game_state_copy.filled_squares = copy.deepcopy(game_state.filled_squares)
    game_state_copy.last_move = game_state.last_move
    return game_state_copy

class SnakeList(object):
    def __init__(self):
        self.head = None
        self.tail = None
        self.size = 0

    def __str__(self):
        output = "start"
        curr = self.head
        i = 0
        while i < self.size: # curr:
            i += 1
            output += str(curr)
            curr = curr.right
        return output

    def add(self, node):
        if self.size == 0:
            self.head = node
            self.tail = node
        else:
            old_tail = self.tail
            node.left = old_tail
            self.tail = node
            old_tail.right = self.tail

        self.size += 1

    def apply_move(self, move):
        # applies move and returns the old tail (in case food is eaten)
        old_tail = self.tail
        if self.size >  1:
            # deletes the tail, duplicates head
            old_tail = self.tail
            new_tail = self.tail.left
            new_tail.right = None
            old_tail.left = None
            old_tail.right = None
            self.tail = new_tail

            old_head = self.head
            new_head = SnakeNode(self.head.pos[0], self.head.pos[1])
            new_head.right = old_head
            old_head.left = new_head
            self.head = new_head
        self.head.pos = self.head.pos[0] + move[0], self.head.pos[1] + move[1]
        return old_tail.pos

class GameState(object):
    def __init__(self, width, height):
        self.width = width
        self.height = height
        # contain snake or food positions.
        self.filled_squares = {}
        self.last_move = (0, 0)

        # initialize the snake and food randomly.
        # doubly linked list of snake.
        # i, j = (63, 4) #self.random_pos()
        i, j = self.random_pos()
        node = SnakeNode(i, j)
        self.snake = SnakeList()
        self.snake.add(node)
        self.filled_squares[(i,j)] = "O"

        # self.food_pos = (i+1, j+1)#self.random_pos()
        self.food_pos = (4, 4)# self.random_pos()
        self.filled_squares[self.food_pos] = "X"

    def random_pos(self):
        options = []
        for i in range(self.width):
            for j in range(self.height):
                if (i, j) in self.filled_squares:
                    continue

                options.append((i, j))
        return random.choice(options)

    def dim(self):
        return self.width, self.height

    def update(self, move):
        # checks if snake moves backward.
        if self.last_move:
            if self.last_move[0] * move[0] == -1 or self.last_move[1] * move[1] == -1:
                return False
        # returns False if the move causes the snake to die
        # (indicating that the game is over).
        old_tail_pos = self.snake.apply_move(move)

        new_squares = {}
        curr = self.snake.head
        while curr:
            i, j = curr.pos
            if i >= self.width or i < 0 or j >= self.height or j < 0:
                return False

            if (i, j) in new_squares:
                return False

            new_squares[(i, j)] = "O"
            curr = curr.right

        self.filled_squares = new_squares
        # (maybe) eat food
        if self.food_pos in new_squares:
            self.snake.add(SnakeNode(old_tail_pos[0], old_tail_pos[1]))
            new_squares[old_tail_pos] = "O"

            # self.food_pos = self.snake.head.pos[0]+1, self.snake.head.pos[1]+1 #self.random_pos()
            self.food_pos = self.random_pos()
        self.last_move = move
        self.filled_squares[self.food_pos] = "X"
        return True

    def is_valid_position(self, pos):
        return pos[0] < self.width and pos[1] < self.height and pos[0] >= 0 and pos[1] >= 0

    def dist_estimate(self, food):
        curr = self.snake.head.pos
        dist = abs(curr[0] - food[0]) + abs(curr[1] - food[1])
        if dist == 0:
            return dist

        # Add penalty for blocked direct path.
        start_i, end_i = min(curr[0], food[0]), max(curr[0], food[0])
        start_j, end_j = min(curr[1], food[1]), max(curr[1], food[1])
        blocked = 0
        path1 = [(i, start_j) for i in range(start_i, end_i+1)] + [(end_i, j) for j in range(start_j, end_j+1)]
        #print(path1)
        #time.sleep(.1)
        for i, j in path1:
            if (i, j) == curr:
                continue
            if (i, j) in self.filled_squares and self.filled_squares[(i, j)] == "O":
                blocked += 1
                break
        path2 = [(start_i, j) for j in range(start_j, end_j+1)] + [(i, end_j) for i in range(start_i, end_i+1)]
        for i, j in path2:
            if (i, j) == curr:
                continue
            if (i, j) in self.filled_squares and self.filled_squares[(i, j)] == "O":
                blocked += 1
                break
        if blocked > 1:
            dist += blocked * (self.snake.size)

        return dist


class Player(object):
    def next_move(self, game_state):
        pass

class HumanPlayer(object):
    def __init__(self):
        self.key_pressed = deque([])
        self.last_move = (0, 0)
        self.listener = keyboard.Listener(on_press=self.on_press, on_release=self.on_release)
        self.listener.start()

    def on_press(self, key):
        self.key_pressed.append(key)
        #os.system('clear')
        #print(self.key_pressed)

    def on_release(self, key):
        if key == keyboard.Key.esc:
            return False  # stop listener if you want

    def next_move(self, game_state):
        if not self.key_pressed:
            return self.last_move

        key = self.key_pressed.popleft()
        move = self.last_move 
        if key == keyboard.Key.up:
            move = (0, -1)
        if key == keyboard.Key.down:
            move = (0, 1)
        if key == keyboard.Key.left:
            move = (-1, 0)
        if key == keyboard.Key.right:
            move = (1, 0)
        self.last_move = move
        return move

class RandomPlayer(Player):
    def next_move(self, game_state):
        moves = [
            (0, 1),
            (0, -1),
            (1, 0),
            (-1, 0),
        ]
        return random.choice(moves)

class TempState(object):
    def __init__(self, level, original_move, gamestate_hypo):
        self.level = level
        self.original_move = original_move
        self.gamestate_hypo = gamestate_hypo

    def __lt__(self, _):
        return True

class NStepLookaheadPlayer(Player):
    def __init__(self, lookahead_steps=1):
        self.lookahead_steps = lookahead_steps

    def tail_reachable(self, game_state):
        moves = [
            (0, 1),
            (0, -1),
            (1, 0),
            (-1, 0),
        ]
        start_pos = game_state.snake.head.pos
        food = game_state.food_pos

        queue = deque([start_pos])
        visited = set([])

        while queue:
            i, j = queue.popleft()
            if not game_state.is_valid_position((i, j)):
                continue

            if (i, j) in visited:
                continue

            visited.add((i,j))
            if (i, j) == food:
                return True

            for m in moves:
                queue.append((i + m[0], j + m[1]))
        return False

    def next_move(self, game_state):
        moves = [
            (0, 1),
            (0, -1),
            (1, 0),
            (-1, 0),
        ]
        food = game_state.food_pos

        game_state_hypo = deepcopy_gamestate(game_state)
        #path = deque([(front, 0, None, snake_hypo)])
        path = []
        heapq.heappush(path, (float('inf'), TempState(0, None, game_state_hypo)))
        arg_moves = []
        visited = set([])
        best_dist = float('inf')
        #print("starting search")
        while path:
            #print([s for (s,_) in heapq.nsmallest(len(path), path)])
            #time.sleep(0.1)
            #curr, level, original_move, snake_hypo = path.popleft()
            (score, temp_state) = heapq.heappop(path)
            #print(score)
            level = temp_state.level
            original_move = temp_state.original_move
            gamestate_hypo = temp_state.gamestate_hypo

            key = str(gamestate_hypo.snake)
            if key in visited:
                continue
            visited.add(key)

            dist = gamestate_hypo.dist_estimate(food)
            if dist == 0 or level >= self.lookahead_steps:
                reachable = self.tail_reachable(gamestate_hypo)
                if not reachable:
                    continue
                if reachable and dist < best_dist:
                    best_dist = dist
                    arg_moves.append((dist, original_move))
                if dist == 0:
                    break
            else:
                for m in moves:
                    gamestate_hypo2 = deepcopy_gamestate(gamestate_hypo)
                    valid = gamestate_hypo2.update(m)
                    if not valid:
                        continue
                    
                    # We want to compare the head to the previous food position.
                    new_dist = gamestate_hypo2.dist_estimate(food)
                    #print(new_pos, food, new_dist)
                    start_move = original_move if original_move else m
                    heapq.heappush(path, (new_dist, TempState(level+1, start_move, gamestate_hypo2)))
                    #path.append((new_pos, level+1, start_move, snake_hypo2))

        #print("ending search")
        arg_moves.sort(key=lambda x: x[0])
        #print(food)
        #print(arg_moves)
        return arg_moves[0][1]

width = 64
height = 32
#snake_game = SnakeGame(NStepLookaheadPlayer(lookahead_steps=1000), width, height, max_frame_rate=75)
snake_game = SnakeGame(HumanPlayer(), width, height, max_frame_rate=30)
snake_game.play_game()
