class R:
    def __init__(self, target_rule, num=None, at=None):
        self.target_rule = target_rule
        self.num = num
        self.next_r = None
        self.sibling_l = []

    @property
    def is_matcher(self):
        return isinstance(self.target_rule, str)

    def __and__(self, other: 'R'):
        self.next_r = other
        return R(self)

    def __or__(self, other: 'R'):
        self.sibling_l.append(other)
        return self

    def __str__(self):
        did_group = False
        s = str(self.target_rule)
        if s.startswith('(') and s.endswith(')'):
            did_group = True
        if self.sibling_l:
            s += '|'
            s += '|'.join(str(i) for i in self.sibling_l)
            s = '(' + s + ')'
            did_group = True
        if self.num is not None:
            if not did_group:
                s = '(' + s + ')'
            s += str(self.num)
        if self.next_r is not None:
            s += str(self.next_r)
        return s


if __name__ == '__main__':
    def test():
        _ = R
        matcher = _(_('abc') | _('cfg'), '*', '@game') & _('iop')
        print(matcher)


    test()
