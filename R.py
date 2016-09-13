from collections import namedtuple

Result = namedtuple('Result', 'epoche op ed')


def make_gen(target: str):
    def gen(epoche: int, op: int):
        ed = op
        for expect_char in target:
            in_char = yield 'GO'
            if in_char == expect_char:
                ed += 1
            else:
                yield 'NO'
        yield Result(epoche, op, ed)

    return gen


class R:
    def __init__(self, target_rule, num=None, name: str = None):
        self.target_rule = target_rule
        self.num = num
        self.name = name

        self.sibling_l = []
        self.next_rule = None
        if self.is_matcher:
            self.gen = make_gen(target_rule)

    @property
    def is_matcher(self) -> bool:
        return isinstance(self.target_rule, str)

    def __and__(self, other) -> 'R':
        assert isinstance(other, R)

    def __or__(self, other) -> 'R':
        assert isinstance(other, R)
        self.sibling_l.append(other)
        return self

    def __xor__(self, other) -> 'R':
        assert isinstance(other, R)

    def __invert__(self) -> 'R':
        pass

    def __call__(self, *other_l) -> 'R':
        if not other_l:
            return
        cursor = self
        for other in other_l:
            assert cursor.next_rule is None and isinstance(other, R)
            cursor.next_rule = other
            cursor = other
        return R(self)

    def __str__(self):
        s = str(self.target_rule)

        def group() -> str:
            return '[' + s + ']'

        def did_group() -> bool:
            return s.startswith('[') and s.endswith(']')

        if self.sibling_l:
            s += '|' + '|'.join(str(i) for i in self.sibling_l)
            s = group()

        if self.num is not None:
            if not did_group():
                s = group()
            s += self.num
        if self.next_rule is not None:
            s += str(self.next_rule)
        return s


if __name__ == '__main__':
    def test():
        _ = R
        matcher = _(_(_('abc') | _('cfg'), '{1}')(_('iop'), _('iop')), '{1}')
        print(matcher)


    test()
