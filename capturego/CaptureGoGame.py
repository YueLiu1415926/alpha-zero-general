import numpy

from logic.board import Board
from common import Color, get_opponent
import numpy as np


class CaptureGoGame():
    """
    This class specifies the base Game class. To define your own game, subclass
    this class and implement the functions below. This works when the game is
    two-player, adversarial and turn-based.

    Use 1 for player1 and -1 for player2.

    See othello/OthelloGame.py for an example implementation.
    """

    def __init__(self, height, width, num_capture_to_win, num_turn_to_tie, init_stones=[]):
        self.height = height
        self.width = width
        self.init_board = Board(self.height, self.width, init_stones)
        self.num_capture_to_win = num_capture_to_win
        self.num_turn_to_tie = num_turn_to_tie
        self._small_num = 1e-4

    def getInitBoard(self):
        """
        Returns:
            startBoard: a representation of the board (ideally this is the form
                        that will be the input to your neural network)
        """
        init_status = self.get_status(self.init_board, 1)
        return init_status

    def getBoardSize(self):
        """
        Returns:
            (x,y): a tuple of board dimensions
        """
        return self.height, self.width

    def getActionSize(self):
        """
        Returns:
            actionSize: number of all possible actions
        """
        return self.init_board.size + 1  # +1 for pass

    def getNextState(self, board, player, action):
        """
        Input:
            board: current board
            player: current player (1 or -1)
            action: action taken by current player

        Returns:
            nextBoard: board after applying action
            nextPlayer: player who plays in the next turn (should be -player)
        """
        b, turn = self.restore_board_from_status(board)
        b.place_stone(action, player)
        next_status = self.get_status(b, turn + 1)
        return next_status, get_opponent(player)

    def getValidMoves(self, board, player):
        """
        Input:
            board: current board
            player: current player

        Returns:
            validMoves: a binary vector of length self.getActionSize(), 1 for
                        moves that are valid from the current board and player,
                        0 for invalid moves
        """
        valid_moves = [0] * self.getActionSize()
        b, _ = self.restore_board_from_status(board)
        for location in b.size:
            if b.is_legal_location(location, player):
                valid_moves[location] = 1
        valid_moves[-1] = 1
        return np.array(valid_moves)

    def getGameEnded(self, board, player):
        """
        Input:
            board: current board
            player: current player (1 or -1)

        Returns:
            r: 0 if game has not ended. 1 if player won, -1 if player lost,
               small non-zero value for draw.

        """
        b, turn = self.restore_board_from_status(board)
        if b.get_num_captured(player) >= self.num_capture_to_win:
            return 1
        elif b.get_num_captured(get_opponent(player)) >= self.num_capture_to_win:
            return -1
        elif turn >= self.num_turn_to_tie:
            return self._small_num
        else:
            return 0

    def getCanonicalForm(self, board, player):
        """
        Input:
            board: current board
            player: current player (1 or -1)

        Returns:
            canonicalBoard: returns canonical form of board. The canonical form
                            should be independent of player. For e.g. in chess,
                            the canonical form can be chosen to be from the pov
                            of white. When the player is white, we can return
                            board as is. When the player is black, we can invert
                            the colors and return the board.
        """
        assert player in (Color.BLACK, Color.WHITE)
        if player == Color.BLACK:
            return board
        else:
            # reverse color of stones on the board(layer0)
            board[0, :, :] *= -1
            # swap layer1 and layer2
            board[[1, 2], :, :] = board[[2, 1], :, :]

    def getSymmetries(self, board, pi):
        """
        Input:
            board: current board
            pi: policy vector of size self.getActionSize()

        Returns:
            symmForms: a list of [(board,pi)] where each tuple is a symmetrical
                       form of the board and the corresponding pi vector. This
                       is used when training the neural network from examples.
        """
        assert (len(pi) == self.getActionSize())
        pi_board = np.reshape(pi[:-1], self.getBoardSize())
        l = []

        for i in range(1, 5):
            for j in [True, False]:
                newB = np.rot90(board, i, axes=(1, 2))
                newPi = np.rot90(pi_board, i)
                if j:
                    newB = np.fliplr(newB)
                    newPi = np.fliplr(newPi)
                l += [(newB, list(newPi.ravel()) + [pi[-1]])]
        return l

    def stringRepresentation(self, board):
        """
        Input:
            board: current board

        Returns:
            boardString: a quick conversion of board to a string format.
                         Required by MCTS for hashing.
        """
        layer0 = board[0, :, :]
        layer4 = board[4, :, :]
        ko_location = -1
        h, w = self.getBoardSize()
        for x in range(h):
            for y in range(w):
                if layer4[x, y] == 1:
                    ko_location = self.init_board.move_to_location(x, y)
        return np.append(layer0.ravel(), [board[1, 0, 0], board[2, 0, 0], board[3, 0, 0], ko_location])

    def get_status(self, board, turn):
        board_2d = board.get_2d_representation()
        h, w = self.getBoardSize()
        # stones on the board
        layer0 = np.array(board_2d).reshape(1, h, w)
        # num stones black needs to capture to win
        layer1 = np.ones_like(layer0) * (self.num_capture_to_win - board.get_num_captured(Color.BLACK))
        # num stones white needs to capture to win
        layer2 = np.ones_like(layer0) * (self.num_capture_to_win - board.get_num_captured(Color.WHITE))
        # num turn to tie
        layer3 = np.ones_like(layer0) * (self.num_turn_to_tie - turn)
        # ko point
        layer4 = np.zeros_like(layer0)
        ko_point = board.get_ko_point()
        if ko_point is not None:
            ko_x, ko_y = board.location_to_move(ko_point)
            layer4[0, ko_x, ko_y] = 1
        layers = [
            layer0,
            layer1,
            layer2,
            layer3,
            layer4,
        ]
        # shape = 5 * height * width
        _status = np.vstack(layers)
        return _status

    def restore_board_from_status(self, status):
        layer0 = status[0, :, :]
        black_stone_list = []
        white_stone_list = []
        for x in range(self.height):
            for y in range(self.width):
                if layer0[x, y] == Color.BLACK:
                    black_stone_list.append([Color.BLACK, x, y])
                elif layer0[x, y] == Color.WHITE:
                    white_stone_list.append([Color.WHITE, x, y])
        init_stones = black_stone_list + white_stone_list
        board = Board(self.height, self.width, init_stones)

        board.set_num_captured(Color.BLACK, self.num_capture_to_win - status[1, 0, 0])
        board.set_num_captured(Color.WHITE, self.num_capture_to_win - status[2, 0, 0])

        turn = self.num_turn_to_tie - status[3, 0, 0]

        layer4 = status[4, :, :]
        for x in range(self.height):
            for y in range(self.width):
                if layer4[x, y] == 1:
                    ko_point = self.init_board.move_to_location(x, y)
                    board.set_ko_point(ko_point)

        return board, turn

if __name__ == "__main__":
    b = Board(3, 3, [(Color.BLACK, 1, 1)])
    g = CaptureGoGame(3, 3, 2, 10, [])
    s = g.get_status(b, 2)
    # print(s)
    print(g.stringRepresentation(s))
    # print(s.shape)
    # print(s[1,:,:])
    # print(s[2,:,:])
    # print(s[3,:,:])
    # print(s[4,:,:])
    #
    # b2, t = g.restore_board_from_status(s)
    # print(b2.groups)
    # print(t)

    # A = np.arange(27).reshape(3,3,3)
    # print(A)
    # print('*'*20)
    # print(np.rot90(A, axes=(1,2)))
    # print('*' * 20)
    # print(np.fliplr(A))

    pass

