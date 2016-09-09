class M:
    def __init__(self, target: str):
        self.target = target
        self.cursor = self
        self.child = None
        self.sibling_l = []

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


if __name__ == '__main__':
    def test():
        matcher = (M('abc') | M('cfg')) + M('iop')
        print(matcher)


    test()
