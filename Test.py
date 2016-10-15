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
    assert str(m(m).match('abcdabcd')) == '[FT(0, 8)]'


def t_b_2_cd_counter():
    m = _('b', '{1,2}', '@b')(_('cd'))
    assert str(m.match('bbcda')) == "[FT(0, 4){'@b': [(0, 2), (0, 1)]}, FT(1, 4){'@b': [(1, 2)]}]"
    m = _(_('b'), '{2}', '@b')(_('cd'))
    assert str(m.match('bbcda')) == "[FT(0, 4){'@b': [(0, 2)]}]"
    m = _(_('b'), '{2}', '@b')(_('cd', '@b'))
    assert str(m.match('bbcdcd')) == "[FT(0, 4){'@b': [(0, 2)]}]"
    m = _(_('b'), '+', '@b')(_('cd', '@b'))
    assert str(m.match('bbcdcd')) == "[FT(1, 4){'@b': [(1, 2)]}, FT(0, 6){'@b': [(0, 2), (0, 1)]}]"


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
    assert str(m.match('aabbbbb')) == "[FT(1, 4){'@a': [(1, 2)]}, FT(0, 5){'@a': [(0, 2), (0, 1)]}]"
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


def t_invert():
    no_alpha = ~_(lambda x, _: str.isalpha(x))
    assert str(no_alpha) == '[~%<lambda>%]'
    assert str(no_alpha.match('123456')) == '[FT(-1, 0), FT(0, 1), FT(1, 2), FT(2, 3),' \
                                            ' FT(3, 4), FT(4, 5), FT(5, 6), FT(6, 7)]'
    assert str(no_alpha.match('abc')) == '[FT(-1, 0), FT(3, 4)]'
    mul_no_alpha = _(no_alpha, '+')
    assert str(mul_no_alpha.match('12')) == '[FT(-1, 0), FT(-1, 1), FT(0, 1), FT(-1, 2), FT(0, 2), FT(1, 2),' \
                                            ' FT(-1, 3), FT(0, 3), FT(1, 3), FT(2, 3)]'
    mul_no_alpha = _(no_alpha, '+', mode=Mode.Greedy)
    assert str(mul_no_alpha.match('12')) == '[FT(-1, 3)]'
    mul_no_alpha = _(no_alpha, '+', mode=Mode.Lazy)
    assert str(mul_no_alpha.match('12')) == '[FT(-1, 0), FT(0, 1), FT(1, 2), FT(2, 3)]'
    mul_no_alpha = _(lambda x, _: not str.isalpha(x), '+')
    assert str(mul_no_alpha.match('123')) == '[FT(0, 1), FT(0, 2), FT(1, 2), FT(0, 3), FT(1, 3), FT(2, 3)]'


def t_exception():
    counter = 0
    try:
        _(1)
    except Exception:
        counter += 1
    try:
        _('1', '1')
    except Exception:
        counter += 1
    assert counter == 2


def t_and_or_opt():
    m = _('abc') & _('bcd', '*')
    assert str(m.match('abc')) == '[FT(0, 3)]'
    m = (_('abc') | _('c', '*'))('e')
    assert str(m.match('ee')) == '[FT(0, 1), FT(1, 2)]'
    m = (_('c', '*') & _('c', '*'))('e')
    assert str(m.match('ee')) == '[FT(0, 1), FT(1, 2)]'
    m = (_('c', '*') & _('c'))('e')
    assert str(m.match('ee')) == '[]'
    assert str(m.match('ce')) == '[FT(0, 2)]'


def t_clone():
    m = _('a')
    assert m != m() != m.clone()


def t_xor():
    m = (_('a') ^ _('b'))('c')
    assert str(m) == '[a^b]c'
    assert str(m.match('ac')) == '[FT(0, 2)]'
    assert str(m.match('bc')) == '[FT(0, 2)]'
    assert str(m.match('cc')) == '[]'
    m = (_('a') ^ _('ab'))('c')
    assert str(m.match('ac')) == '[FT(0, 2)]'
    assert str(m.match('abc')) == '[]'


def t_xor_opt():
    m = (_('a') ^ _('b', '*'))('e')
    assert str(m.match('ce')) == '[FT(0, 2), FT(1, 2)]'


def t_capture_num_merge():
    m = (_('a') ^ _('b', '@b'))('c')
    assert str(m.match('ac')) == '[FT(1, 2)]'
    assert str(m.match('bc')) == '[FT(0, 2), FT(1, 2)]'
    m = (_('a', '@a') ^ _('b', '@b'))('c')
    assert str(m.match('bc')) == '[]'
    m = (_('a', name='@a') ^ _('b', name='@b'))('c')
    assert str(m.match('ac')) == "[FT(0, 2){'@a': [(0, 1)]}]"
    assert str(m.match('bc')) == "[FT(0, 2){'@b': [(0, 1)]}]"
    m = _('ab', name='@1') & _('ab', name='@2')
    assert str(m.match('ab')) in ("[FT(0, 2){'@1': [(0, 2)], '@2': [(0, 2)]}]",
                                  "[FT(0, 2){'@2': [(0, 2)], '@1': [(0, 2)]}]")


def t_div():
    any_char = _(lambda char, args: True)
    open_div = _(_('<div')(_(any_char & (~_('>')), '*'), '>'), name='@open_div')
    assert str(open_div.match('<div></div>')) == "[FT(0, 5){'@open_div': [(0, 5)]}]"
    assert str(open_div.match('<div class="test"></div>')) == "[FT(0, 18){'@open_div': [(0, 18)]}]"


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
        t_exception,
        t_and_or_opt,
        t_clone,
        t_xor,
        t_xor_opt,
        t_capture_num_merge,
        t_div,
        t_div_or_any,
):
    func()
