from R import r, Mode

# 通配符
dot = r(lambda char: True)


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
    数量条件的匹配
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

    # --- 通配符
    m = r('a') @ dot.clone('*') @ r('a')
    assert str(m.match('123a123a123')) == '[Result(3, 8, {})]'
    # ---

    # --- 嵌套
    for m in (r(r('b'), '*') @ r('cd'), r(r('b'), '*', mode=Mode.lazy) @ r('cd')):
        assert str(m.match('cd')) == '[Result(0, 2, {})]'

    m = r(r('a'), 5)
    assert str(m.match('qaaaaaq')) == '[Result(1, 6, {})]'

    m = r(r('a'), 0) @ r('q')
    assert str(m.match('qaaaaaq')) == '[Result(0, 1, {}), Result(6, 7, {})]'

    m = r('q') @ r(r('a'), '+', mode=Mode.lazy)
    assert str(m.match('qaaaaaa')) == '[Result(0, 2, {})]'
    # ---


def t_and():
    '''
    and 条件的匹配
    '''
    m = (r('abc') & r('abc')) @ r('d')
    assert str(m.match('abcd')) == '[Result(0, 4, {})]'
    assert str((m @ m).match('abcd' * 2)) == '[Result(0, 8, {})]'

    m = (r('a') & r('b')) @ r('d')
    assert str(m.match('ad')) == '[]'

    startswith_abc = r('abc') @ dot.clone('*')
    endswith_abc = dot.clone('*') @ r('abc')
    m = startswith_abc & endswith_abc
    assert str(m.match('1abchhabc1')) == '[Result(1, 9, {})]'


def t_or():
    '''
    or 条件的匹配
    '''
    m = (r('a') | r('b')) @ r('bc')
    assert str(m.match('abcbbc')) == '[Result(0, 3, {}), Result(3, 6, {})]'

    m = (r('abc') | r('cfg')) @ r('iop') @ r('iop')
    assert str(m.match('pppcfgiopiop')) == '[Result(3, 12, {})]'


def t_not():
    '''
    not 条件的匹配
    '''
    digit = r(str.isdigit)
    no_digit = ~digit
    m = no_digit.clone('+')
    assert str(m.match('123yyyyy123')) == '[Result(3, 8, {})]'


def t_xor():
    '''
    xor 条件的匹配
    '''
    m = (r('a') ^ r('b')) @ r('c')
    assert str(m.match('ac')) == '[Result(0, 2, {})]'
    assert str(m.match('bc')) == '[Result(0, 2, {})]'
    assert str(m.match('cc')) == '[]'

    m = (r('a') ^ r('ab')) @ r('c')
    assert str(m.match('ac')) == '[]'
    assert str(m.match('abc')) == '[]'

    m = (r('ab') ^ r('ab')) @ r('c')
    assert str(m.match('abc')) == '[]'


def t_exception():
    '''
    异常是否正常触发
    '''
    counter = 0
    for func in (lambda: r(1), lambda: r('foo', '1')):
        try:
            func()
        except TypeError:
            counter += 1
    assert counter == 2


def t_name():
    '''
    带捕获组的匹配
    '''
    m = r('b', '{1,2}', ':b') @ r('cd')
    assert str(m.match('bbcda')) == "[Result(0, 4, {':b': [(0, 1), (1, 2)]})]"

    # --- 捕获组影响数量条件
    for m in (r(r('b', 1, ':b'), 2) @ r('cd', ':b'), r('b', '+', ':b') @ r('cd', ':b'),
              r('b', '+', ':a').clone(name=':b') @ r('cd', ':b')):
        assert str(m.match('bbcdcd')) == "[Result(0, 6, {':b': [(0, 1), (1, 2)]})]"

    # ------ 函数数量条件
    m = r('a', name=':a') @ r('b', lambda capture: len(capture.get(':a', ())) + 1)
    assert str(m.match('aabbbbb')) == "[Result(1, 4, {':a': [(1, 2)]})]"
    # ------
    # ---


def t_div():
    '''
    匹配嵌套 DIV
    '''
    code = '0<div>1<div>2</div>3</div>4'
    div_head = r('<div', name=':head')
    div_tail = r('</div>', name=':tail')
    no_head_tail = ~(div_head | div_tail)

    def stop_head_tail_equal(capture: dict):
        head_group = capture.get(':head', ())
        tail_group = capture.get(':tail', ())
        return 1 if not head_group or not tail_group or len(head_group) != len(tail_group) else 0

    sentinel = r('\00', stop_head_tail_equal)

    div = r(div_head | div_tail | no_head_tail, '+') @ sentinel
    assert str(div.match(code)) == "[Result(0, 27, {':head': [(1, 5), (5, 11)], ':tail': [(13, 19), (19, 26)]})]"

    div = div_head @ r(div_head | div_tail | dot, '+') @ div_tail @ sentinel
    assert str(div.match(code)) == "[Result(1, 26, {':head': [(1, 5), (5, 11)], ':tail': [(13, 19), (19, 26)]})]"


for func in (
        t_str,
        t_simple,
        t_num,
        t_and,
        t_or,
        t_not,
        t_xor,
        t_exception,
        t_name,
        t_div,
):
    func()
print('all pass')
