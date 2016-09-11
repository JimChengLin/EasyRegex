class R:
    def __init__(self, target_rule, num=None, name=None):
        self.target_rule = target_rule
        self.num = num
        self.name = name

        self.next_rule = None
        self.sibling_l = []

    @property
    def is_matcher(self) -> bool:
        return isinstance(self.target_rule, str)

    def __and__(self, other: 'R') -> 'R':
        pass

    def __or__(self, other: 'R') -> 'R':
        assert isinstance(other, R)
        self.sibling_l.append(other)
        return self

    def __xor__(self, other: 'R') -> 'R':
        pass

    def __invert__(self) -> 'R':
        pass

    def __call__(self, *other_l) -> 'R':
        cursor = self
        for other in other_l:
            assert cursor.next_rule is None and isinstance(other, R)
            cursor.next_rule = other
            cursor = R(cursor)
        return cursor

    def __str__(self):
        def group(s: str) -> str:
            return '[' + s + ']'

        def did_group(s: str) -> bool:
            return s.startswith('[') and s.endswith(']')

        s = str(self.target_rule)
        if self.sibling_l:
            s += '|' + '|'.join(str(i) for i in self.sibling_l)
            s = group(s)

        if self.num is not None:
            if not did_group(s):
                s = group(s)
            s += self.num

        if self.next_rule is not None:
            s += str(self.next_rule)
        return s


if __name__ == '__main__':
    def test():
        _ = R
        matcher = _(_('abc') | _('cfg'), '*')(_('iop'), _('iop'))
        print(matcher)


    test()