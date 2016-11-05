from R import r, Mode


def t_str():
    '''
    测试 stringify
    '''
    m = (r('abc') | r('cfg')) @ r('iop') @ r('iop')
    assert str(m) == '(abc|cfg)iopiop'

    m = (r('abc') | r('cfg', '{1}')) @ r('iop') @ r('iop', '{1}')
    assert str(m) == '(abc|cfg)iopiop'

    m = (r('abc') & r('abc') & r('abc')) @ r('d')
    assert str(m) == '((abc&abc)&abc)d'

    m = (r('abc') & r('abc') & r('abc')).clone(num='{1,2}', mode=Mode.Lazy) @ r('d')
    assert str(m) == '(((abc&abc)&abc){1,2}?)d'

    m = r('a', '+', '@a') @ r('b', lambda capture: len(capture.get('@a', ())))
    assert str(m) == '(a{1,inf})(b{%<lambda>%})'

    m = (r('abc') | r('abb')) @ r('abc')
    assert str(m) == '(abc|abb)abc'

    alpha = r(str.isalpha, '+')
    m = (alpha & r('abc')) & (r('abc') & alpha)
    assert str(m) == '(((%isalpha%{1,inf})&abc)&(abc&(%isalpha%{1,inf})))'

    no_alpha = ~alpha
    assert str(no_alpha) == '(~(%isalpha%{1,inf}))'

    m = (r('a') ^ r('b')) @ r('c')
    assert str(m) == '(a^b)c'


for func in (
        t_str,
):
    func()
