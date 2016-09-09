class M:
    def __init__(self, target_rule):
        self.target_rule = target_rule
        self.child = None
        self.sibling_l = []

    @property
    def is_matcher(self):
        return isinstance(self.target_rule, str)

    @property
    def is_wrapper(self):
        return isinstance(self.target_rule, M)

    def __str__(self):
        if self.sibling_l:
            this_s = '({}|{})'.format(self.target, '|'.join(str(i) for i in self.sibling_l))
        else:
            this_s = self.target
        return '{}{}'.format(this_s, self.child or '')

    def __add__(self, other: 'M'):
        assert isinstance(other, M) and self.child is None
        self.cursor.child = other
        self.cursor = other
        return self

    def __or__(self, other: 'M'):
        assert isinstance(other, M)
        self.sibling_l.append(other)
        return self

    def __sub__(self, other):
        pass

    def n(self, n):  # number
        pass


if __name__ == '__main__':
    def test():
        matcher = (M('abc') | M('cfg')) + M('iop')
        print(matcher)


    test()
