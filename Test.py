from R import R, Res, Mode

_ = R


def t_str():
    m = _(_(_('abc') | _('cfg'), '{1}')(_('iop'), _('iop')), '{1}')
    assert str(m) == '[abc|cfg]iopiop'


def t_abc():
    m = _('abc')
    assert m.match('abcdabdabccc') == [Res(0, 0, 3), Res(7, 7, 10)]


def t_abcda():
    m = _('abc')(_('d'), _('a'))
    assert m.match('abcdabdabccc') == [Res(0, 4, 5)]
    m = _('abc')(_('d'), _('a'))
    assert m.match('aabcdabdabccc') == [Res(1, 5, 6)]


def t_abc_bbc():
    m = (_('a') | _('b'))(_('bc'))
    assert m.match('abcbbc') == [Res(0, 1, 3), Res(3, 4, 6)]


def t_b_2_cd():
    m = _('b', '{1,2}')(_('cd'))
    assert m.match('bbcda') == [Res(0, 2, 4), Res(1, 2, 4)]
    m = _(_('b'), '{2}')(_('cd'))
    assert m.match('bbcda') == [Res(0, 2, 4)]


def t_opt_abc_bc():
    m = _('b', '{0,1}')(_('cd'))
    assert m.match('cdabcd') == [Res(0, 0, 2), Res(3, 4, 6), Res(4, 4, 6)]


def t_ab_c_star_c_plus():
    m = _('ab')(_('c', '*'))
    assert str(m.match('abcccc')) == '[FT(0, 2), FT(0, 3), FT(0, 4), FT(0, 5), FT(0, 6)]'
    m = _('ab')(_('c', '+'))
    assert str(m.match('abcccc')) == '[FT(0, 3), FT(0, 4), FT(0, 5), FT(0, 6)]'


def t_abc_and_abc():
    m = _(_('abc') & _('abc') & _('abc'))(_('d'))
    assert str(m) == '[abc&abc&abc]d'
    assert str(m.match('abcd')) == '[FT(0, 4)]'


def t_b_2_cd_counter():
    m = _('b', '{1,2}', '@b')(_('cd'))
    assert str(m.match('bbcda')) == "[FT(0, 4){'@b': [(0, 1), (0, 2)]}, FT(1, 4){'@b': [(1, 2)]}]"
    m = _(_('b'), '{2}', '@b')(_('cd'))
    assert str(m.match('bbcda')) == "[FT(0, 4){'@b': [(0, 2)]}]"
    m = _(_('b'), '{2}', '@b')(_('cd', '@b'))
    assert str(m.match('bbcdcd')) == "[FT(0, 4){'@b': [(0, 2)]}]"
    m = _(_('b'), '+', '@b')(_('cd', '@b'))
    assert str(m.match('bbcdcd')) == "[FT(1, 4){'@b': [(1, 2)]}, FT(0, 6){'@b': [(0, 1), (0, 2)]}]"


def t_letter_123():
    m = _(lambda x, _: str.isalpha(x), '*')(_('123'))
    assert str(m.match('atfgy123a')) == '[FT(0, 8), FT(1, 8), FT(2, 8), FT(3, 8), FT(4, 8), FT(5, 8)]'
    m = _(lambda x, _: str.isalpha(x), '*', mode=Mode.Greedy)(_('123'))
    assert str(m.match('ab123a')) == '[FT(0, 5)]'
    m = _(_(lambda x, _: str.isalpha(x)), '*', mode=Mode.Greedy)(_('123'))
    assert str(m) == '[%<lambda>%]{0,inf}123'
    assert str(m.match('ab123a')) == '[FT(0, 5)]'


def t_ignore_c():
    m = _('a')('b', _('c', 0), 'd')
    assert str(m.match('abd')) == '[FT(0, 3)]'


def t_str_num():
    m = _('a', 2)
    assert str(m) == 'a{2}'


def t_num_func():
    m = _('a', name='@a')(_('b', lambda epoch, ed, d: len(d.get('@a', ())) + 1))
    assert str(m.match('aabbbbb')) == "[FT(1, 4){'@a': [(1, 2)]}]"
    m = _('a', '+', '@a')(_('b', lambda epoch, ed, d: len(d.get('@a', ())) + 1))
    assert str(m.match('aabbbbb')) == "[FT(1, 4){'@a': [(1, 2)]}, FT(0, 5){'@a': [(0, 1), (0, 2)]}]"
    assert str(m) == 'a{1,inf}b{%<lambda>%}'


def t_lazy():
    m = _(_(lambda x, _: str.isalpha(x)), '*', mode=Mode.Lazy)(_('123'))
    assert str(m.match('ab123a')) == '[FT(2, 5)]'


def t_or_and():
    m = (_('abc') | _('abb')) & _('abc')
    assert str(m) == '[abc|abb]&abc'
    assert str(m.match('abc')) == '[FT(0, 3)]'

    alpha = _(lambda x, _: str.isalpha(x), '+')
    m = _(_(alpha)('abc')) & _(_('abc')(alpha))
    assert str(m) == '[%<lambda>%]{1,inf}abc&abc[%<lambda>%]{1,inf}'
    assert str(m.match('abcaabcd')) == '[FT(0, 7)]'
    m = _(_(alpha)('abc')) & _(_('abc')(alpha)) & _(_('abc')(alpha))
    assert str(m) == '[%<lambda>%]{1,inf}abc&abc[%<lambda>%]{1,inf}&abc[%<lambda>%]{1,inf}'
    assert str(m.match('abcaabcd')) == '[FT(0, 7)]'


def t_xor():
    pass


def t_invert():
    no_alpha = ~_(lambda x, _: str.isalpha(x))
    # assert str(no_alpha.match('123456')) == '[FT(-1, 0), FT(0, 1), FT(1, 2), FT(2, 3), ' \
    #                                         'FT(3, 4), FT(4, 5), FT(5, 6), FT(6, 7)]'
    mul_no_alpha = _(no_alpha, '+')
    print(mul_no_alpha.match('12'))
    mul_no_alpha = _(no_alpha, '+', mode=Mode.Greedy)
    print(mul_no_alpha.match('12'))
    mul_no_alpha = _(no_alpha, '+', mode=Mode.Lazy)
    print(mul_no_alpha.match('12'))
    # mul_no_alpha = _(lambda x, _: not str.isalpha(x), '+')
    # print(mul_no_alpha.match('123'))


for func in (
        t_str,
        t_abc,
        t_abcda,
        t_abc_bbc,
        t_b_2_cd,
        t_opt_abc_bc,
        t_ab_c_star_c_plus,
        t_abc_and_abc,
        t_b_2_cd_counter,
        t_letter_123,
        t_ignore_c,
        t_str_num,
        t_num_func,
        t_lazy,
        t_or_and,
        t_invert,
):
    func()
