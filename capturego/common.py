class Color:
    BLACK = 1
    WHITE = -1
    EMPTY = 0


class ErrorMessage:
    UNKNOWN_PLAYER = "player should be either black or white"
    OUT_OF_BOUND = "location out of bound"
    NOT_EMPTY = "location is not empty"
    KO_PROTECT = "location is protected by ko rule"
    SUICIDE = "location causes suicide, and suicide is illegal"
    SUCCESSIVE_PASS = "successive pass is not allowed"
    INVALID_INPUT = "invalid input, input should be in the form 'c,2'"


def get_opponent(color):
    return Color.BLACK + Color.WHITE - color

