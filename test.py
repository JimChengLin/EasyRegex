from R import r


def t_str():
    m = (r('abc') | r('cfg')) @ r('iop') @ r('iop')
    assert str(m) == '(abc|cfg)iopiop'
    print(m.match('cfgiopiop'))


def t_abc():
    m = r('abc')
    print(m.match('abcdabdabccc'))


def t_abcda():
    m = r('abc') @ r('d') @ r('a')
    print(m.match('abcdabdabccc'))


for func in (
        t_str,
        t_abc,
        t_abcda,
):
    func()
