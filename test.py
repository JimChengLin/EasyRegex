from R import r


def t_str():
    m = (r('abc') | r('cfg')) @ r('iop') @ r('iop')
    assert str(m) == '(abc|cfg)iopiop'


def t_abc():
    m = r('abc')
    print(m.match('abcdabdabccc'))


for func in (
        t_str,
        t_abc,
):
    func()
