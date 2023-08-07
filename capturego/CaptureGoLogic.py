from common import Color, ErrorMessage, get_opponent

class Group:
    # a group of stones
    def __init__(self, color, stones=set(), liberties=set()):
        self.color = color
        self.stones = stones
        self.liberties = liberties

    def num_stones(self):
        return len(self.stones)

    def num_liberties(self):
        return len(self.liberties)


class Board:

    def __init__(self, height, width, init_stones=[]):
        self.height = height
        self.width = width
        self.size = self.height * self.width
        self._pass_location = self.size

        self.groups = [None] * self.size
        self._ko_point = None
        self._capture_count = {
            Color.BLACK: 0,
            Color.WHITE: 0
        }

        self.set_init_stones(init_stones)

    def get_pass_location(self):
        return self._pass_location

    def get_ko_point(self):
        return self._ko_point

    def set_ko_point(self, location):
        self._ko_point = location

    def get_num_captured(self, player):
        return self._capture_count[player]

    def set_num_captured(self, player, num_captured):
        self._capture_count[player] = num_captured

    def is_valid_coordinate(self, x, y):
        return 0 <= x < self.height and 0 <= y < self.width

    def move_to_location(self, x, y):
        return x * self.width + y

    def location_to_move(self, location):
        return location // self.width, location % self.width

    def is_within_bound(self, location):
        return 0 <= location < self.size

    def is_empty(self, location):
        return self.groups[location] is None

    def is_black_stone(self, location):
        return self.groups[location].color == Color.BLACK

    def is_white_stone(self, location):
        return self.groups[location].color == Color.WHITE

    def is_my_stone(self, location, player):
        if self.is_empty(location):
            return False
        return self.groups[location].color == player

    def is_opponent_stone(self, location, player):
        if self.is_empty(location):
            return False
        return self.groups[location].color == get_opponent(player)

    def get_location_color(self, location):
        if self.is_empty(location):
            return Color.EMPTY
        elif self.is_black_stone(location):
            return Color.BLACK
        else:
            return Color.WHITE

    def get_neighbors(self, location):
        neighbors = []
        x, y = self.location_to_move(location)
        for dx, dy in ((0,1), (0,-1), (1,0), (-1,0)):
            neighbor_x, neighbor_y = x+dx, y+dy
            if not self.is_valid_coordinate(neighbor_x, neighbor_y):
                continue
            neighbor = self.move_to_location(neighbor_x, neighbor_y)
            if self.is_within_bound(neighbor):
                neighbors.append(neighbor)
        return neighbors

    def is_protected_by_ko(self, location, player):
        if location != self._ko_point:
            return False
        group_captured = set()
        neighbors = self.get_neighbors(location)
        for neighbor in neighbors:
            if not self.is_opponent_stone(neighbor, player):
                continue
            if self.groups[neighbor].num_liberties() == 1:
                group_captured.add(self.groups[neighbor])
        num_capture = 0
        for group in group_captured:
            num_capture += group.num_stones()
        return num_capture == 1

    def is_suicide(self, location, player):
        neighbors = self.get_neighbors(location)
        for neighbor in neighbors:
            if self.is_empty(neighbor):
                return False
            elif self.is_opponent_stone(neighbor, player):
                if self.groups[neighbor].num_liberties() == 1:
                    return False
            else:  # self.is_my_stone(location, player)
                if self.groups[neighbor].num_liberties() > 1:
                    return False
        return True

    def is_legal_location(self, location, player):
        if player not in (Color.BLACK, Color.WHITE):
            return False, ErrorMessage.UNKNOWN_PLAYER
        if location == self.get_pass_location():
            return True, "legal"
        if not self.is_within_bound(location):
            return False, ErrorMessage.OUT_OF_BOUND
        if not self.is_empty(location):
            return False, ErrorMessage.NOT_EMPTY
        if self.is_protected_by_ko(location, player):
            return False, ErrorMessage.KO_PROTECT
        if self.is_suicide(location, player):
            return False, ErrorMessage.SUICIDE
        return True, "legal"

    def solve_captured_group(self, group):
        color = group.color
        for location in group.stones:
            self.groups[location] = None
            neighbors = self.get_neighbors(location)
            for neighbor in neighbors:
                if self.is_opponent_stone(neighbor, color):
                    self.groups[neighbor].liberties.add(location)
        captured_stones = group.stones
        return captured_stones

    # input: a list of groups
    def merge(self, groups):
        groups.sort(key=lambda g: g.num_liberties(), reverse=True)
        root_group = groups[0]
        for group in groups[1:]:
            for location in group.stones:
                self.groups[location] = root_group
            root_group.stones = root_group.stones.union(group.stones)
            root_group.liberties = root_group.liberties.union(group.liberties)
            group.stones = []
            group.liberties = []
        root_group.liberties -= root_group.stones
        return root_group

    def place_stone(self, location, player):
        if location == self.get_pass_location():
            return set()
        captured_stones = set()
        captured_groups = set()
        merged_groups = set()
        stones = {location}
        liberties = set()
        neighbors = self.get_neighbors(location)
        for neighbor in neighbors:
            if self.is_empty(neighbor):
                liberties.add(neighbor)
            elif self.is_my_stone(neighbor, player):
                merged_groups.add(self.groups[neighbor])
            else:  # self.is_opponent_stone(neighbor, player)
                neighbor_group = self.groups[neighbor]
                if neighbor_group.num_liberties() == 1:
                    captured_groups.add(neighbor_group)
                else:
                    neighbor_group.liberties.remove(location)

        new_group = Group(player, stones, liberties)
        merged_groups.add(new_group)
        root_group = self.merge(list(merged_groups))
        self.groups[location] = root_group

        for captured_group in captured_groups:
            new_capture = self.solve_captured_group(captured_group)
            captured_stones = captured_stones.union(new_capture)

        num_captured = len(captured_stones)
        self._capture_count[player] += num_captured
        if num_captured == 1:
            self._ko_point = list(captured_stones)[0]

        return captured_stones

    def set_init_stones(self, init_stones):
        for color, x, y in init_stones:
            location = self.move_to_location(x, y)
            if not self.is_legal_location(location, color):
                print("ignore illegal init stone ({}, {})".format(x, y))
            self.place_stone(location, color)

    def get_2d_representation(self):
        board_2d = []
        for x in range(self.height):
            board_2d.append([])
            for y in range(self.width):
                location = self.move_to_location(x, y)
                board_2d[x].append(self.get_location_color(location))
        return board_2d