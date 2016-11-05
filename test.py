from R import r, Mode


def t_str():
    '''
    R 的 stringify 是否符合预期
    '''
    m = (r('abc') | r('cfg')) @ r('iop') @ r('iop')
    assert str(m) == '(abc|cfg)iopiop'

    m = (r('abc') | r('cfg', '{1}')) @ r('iop') @ r('iop', '{1}')
    assert str(m) == '(abc|cfg)iopiop'

    m = (r('abc') & r('abc') & r('abc')) @ r('d')
    assert str(m) == '((abc&abc)&abc)d'

    m = (r('abc') & r('abc') & r('abc')).clone(num='{1,2}', mode=Mode.lazy) @ r('d')
    assert str(m) == '(((abc&abc)&abc){1,2}?)d'

    m = r('a', '+', ':a') @ r('b', lambda capture: len(capture.get(':a', ())))
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


def t_simple():
    '''
    没有条件的简单匹配
    '''
    m = r('abc')
    assert str(m.match('abcdabdabccc')) == '[Result(0, 3, {}), Result(7, 10, {})]'

    for m in (r('abc') @ r('d') @ r('a'), r('abc') @ r(r('d') @ r('a'))):
        assert str(m.match('abcdabdabccc')) == '[Result(0, 5, {})]'
        assert str(m.match('aabcdabdabccc')) == '[Result(1, 6, {})]'

    # --- 函数匹配
    m = r('1') @ r(str.isalpha) @ r('1')
    assert str(m.match('a1a1')) == '[Result(1, 4, {})]'
    # ---


def t_num():
    '''
    有数量条件的匹配
    '''
    for m in (r('b', '{1,2}') @ r('cd'), r('b', '{2}') @ r('cd')):
        assert str(m.match('bbcda')) == '[Result(0, 4, {})]'

    m = r('b', '{0,1}') @ r('cd')
    assert str(m.match('cdabcd')) == '[Result(0, 2, {}), Result(3, 6, {})]'

    m = r('a') @ r('b') @ r('c', 0) @ r('d')
    assert str(m.match('abd')) == '[Result(0, 3, {})]'

    for m in (r('ab') @ r('c', '*'), r('ab') @ r('c', '+')):
        assert str(m.match('abcccc')) == '[Result(0, 6, {})]'

    # --- 懒惰模式
    m = (r('ab') @ r('c', '*', mode=Mode.lazy))
    assert str(m.match('abcccc')) == '[Result(0, 2, {})]'

    m = (r('ab') @ r('c', (1, 2), mode=Mode.lazy))
    assert str(m.match('abcccc')) == '[Result(0, 3, {})]'
    # ---


for func in (
        t_str,
        t_simple,
        t_num,
):
    func()
