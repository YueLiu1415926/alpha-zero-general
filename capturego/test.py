import unittest

from .common import Color, ErrorMessage
from .CaptureGoLogic import Board


class TestBoard(unittest.TestCase):

    def setUp(self):
        self.board55 = Board(5, 5)

    def test_stone_black(self):
        location = self.board55.move_to_location(3,3)
        self.board55.place_stone(location, Color.BLACK)
        assert self.board55.is_black_stone(location)
        assert self.board55.get_location_color(location) == Color.BLACK
        group = self.board55.groups[location]
        assert group.num_stones() == 1
        assert group.num_liberties() == 4

    def test_stone_white(self):
        location = self.board55.move_to_location(3,3)
        self.board55.place_stone(location, Color.WHITE)
        assert self.board55.is_white_stone(location)
        assert self.board55.get_location_color(location) == Color.WHITE
        group = self.board55.groups[location]
        assert group.color == Color.WHITE
        assert group.num_stones() == 1
        assert group.num_liberties() == 4

    def test_illegal_move_basic(self):
        location = self.board55.move_to_location(3, 3)

        legal, message = self.board55.is_legal_location(location, 12345)
        assert not legal
        assert message == ErrorMessage.UNKNOWN_PLAYER

        legal, message = self.board55.is_legal_location(12345, Color.BLACK)
        assert not legal
        assert message == ErrorMessage.OUT_OF_BOUND

        self.board55.place_stone(location, Color.WHITE)

        legal, message = self.board55.is_legal_location(location, Color.BLACK)
        assert not legal
        assert message == ErrorMessage.NOT_EMPTY

        legal, message = self.board55.is_legal_location(location, Color.WHITE)
        assert not legal
        assert message == ErrorMessage.NOT_EMPTY

    def test_liberties_center(self):
        location = self.board55.move_to_location(3, 3)
        self.board55.place_stone(location, Color.BLACK)
        group = self.board55.groups[location]
        assert group.num_liberties() == 4

    def test_liberties_border(self):
        location = self.board55.move_to_location(3, 4)
        self.board55.place_stone(location, Color.BLACK)
        group = self.board55.groups[location]
        assert group.num_liberties() == 3

    def test_liberties_corner(self):
        location = self.board55.move_to_location(0, 4)
        self.board55.place_stone(location, Color.BLACK)
        group = self.board55.groups[location]
        assert group.num_liberties() == 2

    def test_reduce_liberty(self):
        location0 = self.board55.move_to_location(3, 3)
        location1 = self.board55.move_to_location(3, 2)
        location2 = self.board55.move_to_location(2, 3)

        self.board55.place_stone(location0, Color.BLACK)
        group0 = self.board55.groups[location0]
        assert group0.num_liberties() == 4
        self.board55.place_stone(location1, Color.WHITE)
        group1 = self.board55.groups[location1]
        assert group0.num_liberties() == 3
        assert group1.num_liberties() == 3
        self.board55.place_stone(location2, Color.WHITE)
        group2 = self.board55.groups[location2]
        assert group0.num_liberties() == 2
        assert group1.num_liberties() == 3
        assert group2.num_liberties() == 3

    def test_merge(self):
        location0 = self.board55.move_to_location(3, 3)
        location1 = self.board55.move_to_location(3, 2)
        location2 = self.board55.move_to_location(2, 3)
        location3 = self.board55.move_to_location(4, 3)
        location4 = self.board55.move_to_location(1, 1)

        self.board55.place_stone(location0, Color.BLACK)
        group0 = self.board55.groups[location0]
        assert group0.num_liberties() == 4

        self.board55.place_stone(location1, Color.BLACK)
        group1 = self.board55.groups[location1]
        assert group0 == group1
        assert group0.num_liberties() == 6

        self.board55.place_stone(location2, Color.BLACK)
        group2 = self.board55.groups[location2]
        assert group0 == group2
        assert group0.num_liberties() == 7

        self.board55.place_stone(location3, Color.BLACK)
        group3 = self.board55.groups[location3]
        assert group0 == group3
        assert group0.num_liberties() == 7

        self.board55.place_stone(location4, Color.BLACK)
        group4 = self.board55.groups[location4]
        assert group0 != group4
        assert group0.num_liberties() == 7
        assert group4.num_liberties() == 4

    def test_capture_1stone_center(self):
        moves = [
            (1, Color.BLACK, 3, 3),
            (2, Color.WHITE, 2, 3),
            (3, Color.WHITE, 4, 3),
            (4, Color.WHITE, 3, 4),
            (5, Color.WHITE, 3, 2),
        ]
        capture_location = self.board55.move_to_location(3, 3)
        for turn, player, x, y in moves:
            location = self.board55.move_to_location(x, y)
            captured_stones = self.board55.place_stone(location, player)
            if turn < 5:
                assert len(captured_stones) == 0
                assert not self.board55.is_empty(capture_location)
                assert self.board55._ko_point is None
            elif turn == 5:
                assert len(captured_stones) == 1
                assert capture_location in captured_stones
                assert self.board55.is_empty(capture_location)
                assert self.board55._ko_point == capture_location
                group = self.board55.groups[location]
                assert group.num_liberties() == 4
                assert group.num_stones() == 1

    def test_capture_1stone_corner(self):
        moves = [
            (1, Color.BLACK, 4, 4),
            (2, Color.WHITE, 4, 3),
            (3, Color.WHITE, 3, 4),
        ]
        capture_location = self.board55.move_to_location(4, 4)
        for turn, player, x, y in moves:
            location = self.board55.move_to_location(x, y)
            captured_stones = self.board55.place_stone(location, player)
            if turn < 3:
                assert len(captured_stones) == 0
                assert not self.board55.is_empty(capture_location)
                assert self.board55._ko_point is None
            elif turn == 3:
                assert len(captured_stones) == 1
                assert capture_location in captured_stones
                assert self.board55.is_empty(capture_location)
                assert self.board55._ko_point == capture_location
                group = self.board55.groups[location]
                assert group.num_liberties() == 3
                assert group.num_stones() == 1

    def test_capture_2stone_center(self):
        moves = [
            (1, Color.BLACK, 2, 3),
            (2, Color.BLACK, 3, 3),
            (3, Color.WHITE, 1, 3),
            (4, Color.WHITE, 4, 3),
            (5, Color.WHITE, 2, 4),
            (6, Color.WHITE, 3, 4),
            (7, Color.WHITE, 2, 2),
            (8, Color.WHITE, 3, 2),
        ]
        capture_location1 = self.board55.move_to_location(2, 3)
        capture_location2 = self.board55.move_to_location(3, 3)
        for turn, player, x, y in moves:
            location = self.board55.move_to_location(x, y)
            captured_stones = self.board55.place_stone(location, player)
            if 1 < turn < 8:
                assert len(captured_stones) == 0
                assert not self.board55.is_empty(capture_location1)
                assert not self.board55.is_empty(capture_location2)
                assert self.board55._ko_point is None
            elif turn == 8:
                assert len(captured_stones) == 2
                assert capture_location1 in captured_stones
                assert capture_location2 in captured_stones
                assert self.board55.is_empty(capture_location1)
                assert self.board55.is_empty(capture_location2)
                assert self.board55._ko_point is None
                group = self.board55.groups[location]
                assert group.num_liberties() == 6
                assert group.num_stones() == 2

    def test_ko_1(self):
        moves = [
            (1, Color.BLACK, 0, 0),
            (2, Color.BLACK, 1, 1),
            (3, Color.BLACK, 0, 2),
            (4, Color.WHITE, 1, 2),
            (5, Color.WHITE, 0, 3),
            (6, Color.WHITE, 0, 1),
            (7, Color.BLACK, 0, 2),
        ]
        for turn, player, x, y in moves:
            location = self.board55.move_to_location(x, y)
            if turn == 7:
                legal, message = self.board55.is_legal_location(location, player)
                assert not legal
                assert message == ErrorMessage.KO_PROTECT
                return
            self.board55.place_stone(location, player)

    def test_ko_2(self):
        moves = [
            (1, Color.BLACK, 0, 0),
            (2, Color.BLACK, 1, 1),
            (3, Color.BLACK, 0, 2),
            (4, Color.BLACK, 0, 3),
            (5, Color.WHITE, 0, 4),
            (6, Color.WHITE, 1, 3),
            (7, Color.WHITE, 1, 2),
            (8, Color.WHITE, 0, 1),
            (9, Color.BLACK, 0, 2),
        ]
        for turn, player, x, y in moves:
            location = self.board55.move_to_location(x, y)
            if turn == 9:
                legal, message = self.board55.is_legal_location(location, player)
                assert legal
                return
            self.board55.place_stone(location, player)

    def test_ko_3(self):
        moves = [
            (1, Color.BLACK, 0, 0),
            (2, Color.BLACK, 1, 1),
            (3, Color.BLACK, 1, 2),
            (4, Color.BLACK, 0, 3),
            (5, Color.WHITE, 0, 4),
            (6, Color.WHITE, 1, 3),
            (8, Color.WHITE, 0, 1),
            (7, Color.WHITE, 0, 2),
            (9, Color.BLACK, 0, 3),
        ]
        for turn, player, x, y in moves:
            location = self.board55.move_to_location(x, y)
            if turn == 9:
                legal, message = self.board55.is_legal_location(location, player)
                assert legal
                return
            self.board55.place_stone(location, player)

    def test_suicide_1stone(self):
        moves = [
            (1, Color.BLACK, 1, 1),
            (2, Color.BLACK, 1, 3),
            (3, Color.BLACK, 0, 2),
            (4, Color.BLACK, 2, 2),
            (5, Color.WHITE, 1, 2),
        ]
        for turn, player, x, y in moves:
            location = self.board55.move_to_location(x, y)
            if turn == 5:
                legal, message = self.board55.is_legal_location(location, player)
                assert not legal
                assert message == ErrorMessage.SUICIDE
                return
            self.board55.place_stone(location, player)

    def test_suicide_2stone(self):
        moves = [
            (1, Color.BLACK, 0, 0),
            (2, Color.BLACK, 1, 1),
            (3, Color.BLACK, 1, 2),
            (4, Color.BLACK, 0, 3),
            (5, Color.WHITE, 0, 1),
            (6, Color.WHITE, 0, 2),
        ]
        for turn, player, x, y in moves:
            location = self.board55.move_to_location(x, y)
            if turn < 6:
                legal, message = self.board55.is_legal_location(location, player)
                assert legal
            elif turn == 6:
                legal, message = self.board55.is_legal_location(location, player)
                assert not legal
                assert message == ErrorMessage.SUICIDE
                return
            self.board55.place_stone(location, player)

    def test_init_stone(self):
        init_stones = [
            (Color.BLACK, 1, 1),
            (Color.BLACK, 1, 2),
            (Color.WHITE, 2, 2)
        ]
        board = Board(5, 5, init_stones)
        assert board.is_black_stone(board.move_to_location(1, 1))
        assert board.is_black_stone(board.move_to_location(1, 2))
        assert board.is_white_stone(board.move_to_location(2, 2))
