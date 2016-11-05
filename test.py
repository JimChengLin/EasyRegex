from R import r, Mode


def t_str():
    '''
    test stringify
    '''
    m = (r('abc') | r('cfg')) @ r('iop') @ r('iop')
    assert str(m) == '(abc|cfg)iopiop'

    m = (r('abc') | r('cfg', '{1}')) @ r('iop') @ r('iop', '{1}')
    assert str(m) == '(abc|cfg)iopiop'

    m = (r('abc') & r('abc') & r('abc')) @ r('d')
    assert str(m) == '((abc&abc)&abc)d'

    m = (r('abc') & r('abc') & r('abc')).clone(num='{1,2}', mode=Mode.Lazy) @ r('d')
    print(m)


def t_abc():
    m = r('abc')
    print(m.match('abcdabdabccc'))


def t_abcda():
    m = r('abc') @ r('d') @ r('a')
    print(m.match('abcdabdabccc'))


for func in (
        t_str,
        # t_abc,
        # t_abcda,
):
    func()
