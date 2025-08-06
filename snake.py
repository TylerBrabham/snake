import os
import random
import time

#TODO: Make it use A* search and check turn validity
# Make it avoid creating a loop around itself?


class SnakeGame(object):
    def __init__(self, player, width, height):
        self.player = player
        self.game_state = GameState(width, height)
        self.game_valid = True

    def play_game(self):
        rounds = 1000
        i = 0
        while self.game_valid and i < rounds:
            i += 1
            time.sleep(0.01)
            move = self.player.next_move(self.game_state)
            self.game_valid = self.game_state.update(move)
            self.render()

    def render(self):
        os.system('clear')
        time.sleep(0.001)
        width, height = self.game_state.dim()
        for j in range(height):
            row = ""
            for i in range(width):
                if (i, j) in self.game_state.filled_squares:
                    char = self.game_state.filled_squares[(i, j)]
                    row += char
                else:
                    row += " "

            print(row)

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

        # initialize the snake and food randomly.
        # doubly linked list of snake.
        i, j = self.random_pos()
        node = SnakeNode(i, j)
        self.snake = SnakeList()
        self.snake.add(node)
        self.filled_squares[(i,j)] = "O"

        # self.food_pos = (i+1, j+1)#self.random_pos()
        self.food_pos = self.random_pos()
        self.filled_squares[self.food_pos] = "X"

    def random_pos(self):
        while True:
            i = random.choice(range(self.width))
            j = random.choice(range(self.height))
            if (i, j) not in self.filled_squares:
                return (i, j)
        #unreachable
        return None

    def dim(self):
        return self.width, self.height

    def update(self, move):
        # returns False if the move causes the snake to die
        # (indicating that the game is over).
        old_tail_pos = self.snake.apply_move(move)

        new_squares = {}
        curr = self.snake.head
        while curr:
            i, j = curr.pos
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
        self.filled_squares[self.food_pos] = "X"
        return True

class Player(object):
    def next_move(self, game_state):
        pass

class RandomPlayer(Player):
    def next_move(self, game_state):
        moves = [
            (0, 1),
            (0, -1),
            (1, 0),
            (-1, 0),
        ]
        return random.choice(moves)

class OneStepCloserPlayer(Player):
    def next_move(self, game_state):
        moves = [
            (0, 1),
            (0, -1),
            (1, 0),
            (-1, 0),
        ]
        front = game_state.snake.head.pos
        food = game_state.food_pos

        poss = [(front[0] + m[0], front[1] + m[1]) for m in moves]
        poss = list(zip(poss, moves))
        poss = list(filter(lambda p: p[0] not in game_state.filled_squares or game_state.filled_squares[p[0]] != "O", poss))
        moves = [x[1] for x in poss]
        poss = [x[0] for x in poss]
        dist = [abs(p[0] - food[0]) + abs(p[1] - food[1]) for p in poss]
        arg_moves = list(zip(dist, moves))
        arg_moves.sort(key=lambda x: x[0])
        return arg_moves[0][1]

width = 64
height = 16
snake_game = SnakeGame(OneStepCloserPlayer(), width, height)
snake_game.play_game()
