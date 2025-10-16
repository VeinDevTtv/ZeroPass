class Node:
    __slots__ = ("children", "terminal")
    def __init__(self):
        self.children = {}
        self.terminal = False


def build_trie(words):
    root = Node()
    for w in words:
        cur = root
        for ch in w:
            cur = cur.children.setdefault(ch, Node())
        cur.terminal = True
    return root


