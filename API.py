class M:
    def __init__(self, target: str):
        self.target = target
        self.head = self
        self.tail = self
        self.child = None
        self.sibling_l = []

    def __str__(self):
        self_s = self.target
        if self.sibling_l:
            self_s = '({}|{})'.format(self.target, '|'.join(str(i) for i in self.sibling_l))
        return '{}{}'.format(self_s, self.child if self.child else '')

    def __add__(self, other: 'M'):
        assert isinstance(other, M) and self.child is None
        self.tail.child = other
        self.tail = other
        other.head = self.head
        return self

    def __or__(self, other: 'M'):
        assert isinstance(other, M)
        self.sibling_l.append(other)
        return self


if __name__ == '__main__':
    def test():
        matcher = (M('abc') | M('cfg')) + M('iop')
        print(matcher.head)


    test()
