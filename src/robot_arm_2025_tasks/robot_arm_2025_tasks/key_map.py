class KeyMap:

    def __init__(self):

        # Simple example layout (partial)
        # Row 0 = bottom row

        self.map = {
            'a': (2, 0),
            'b': (1, 4),
            'c': (1, 2),
            'd': (2, 2),
            'e': (3, 2),
            'f': (2, 3),
            'g': (2, 4),
            'h': (2, 5),
            'i': (3, 7),
            'j': (2, 6),
            'k': (2, 7),
            'l': (2, 8),
            'm': (1, 6),
            'n': (1, 5),
            'o': (3, 8),
            'p': (3, 9),
            'q': (3, 0),
            'r': (3, 3),
            's': (2, 1),
            't': (3, 4),
            'u': (3, 6),
            'v': (1, 3),
            'w': (3, 1),
            'x': (1, 1),
            'y': (3, 5),
            'z': (1, 0),
            ' ': (0, 5)
        }

    def get_key(self, char):
        return self.map.get(char.lower(), None)
