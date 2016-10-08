from R import R, Res as Result, Mode


def test_str():
    _ = R
    matcher = _(_(_('abc') | _('cfg'), '{1}')(_('iop'), _('iop')), '{1}')
    assert str(matcher) == '[abc|cfg]iopiop'


def test_abc():
    _ = R
    matcher = _('abc')
    assert matcher.match('abcdabdabccc') == [Result(0, 0, 3), Result(7, 7, 10)]


def test_abcda():
    _ = R
    matcher = _('abc')(_('d'), _('a'))
    assert matcher.match('abcdabdabccc') == [Result(0, 4, 5)]
    matcher = _('abc')(_('d'), _('a'))
    assert matcher.match('aabcdabdabccc') == [Result(1, 5, 6)]


def test_abc_bbc():
    _ = R
    matcher = (_('a') | _('b'))(_('bc'))
    assert matcher.match('abcbbc') == [Result(0, 1, 3), Result(3, 4, 6)]


def test_b_2_cd():
    _ = R
    matcher = _('b', '{1,2}')(_('cd'))
    assert matcher.match('bbcda') == [Result(0, 2, 4), Result(1, 2, 4)]
    matcher = _(_('b'), '{2}')(_('cd'))
    assert matcher.match('bbcda') == [Result(0, 2, 4)]


def test_optional_abc_bc():
    _ = R
    matcher = _('b', '{0,1}')(_('cd'))
    assert matcher.match('cdabcd') == [Result(0, 0, 2), Result(3, 4, 6), Result(4, 4, 6)]


def test_ab_c_star_c_plus():
    _ = R
    matcher = _('ab')(_('c', '*'))
    assert str(matcher.match('abcccc')) == '[FT(0, 2), FT(0, 3), FT(0, 4), FT(0, 5), FT(0, 6)]'
    matcher = _('ab')(_('c', '+'))
    assert str(matcher.match('abcccc')) == '[FT(0, 3), FT(0, 4), FT(0, 5), FT(0, 6)]'


def test_abc_and_abc():
    _ = R
    matcher = _(_('abc') & _('abc') & _('abc'))(_('d'))
    assert str(matcher) == '[abc&abc&abc]d'
    assert str(matcher.match('abcd')) == '[FT(0, 4)]'


def test_b_2_cd_counter():
    _ = R
    matcher = _('b', '{1,2}', '@b')(_('cd'))
    assert str(matcher.match('bbcda')) == "[FT(0, 4){'@b': [(0, 2)]}, FT(1, 4){'@b': [(1, 2)]}]"
    matcher = _(_('b'), '{2}', '@b')(_('cd'))
    assert str(matcher.match('bbcda')) == "[FT(0, 4){'@b': [(0, 2)]}]"
    matcher = _(_('b'), '{2}', '@b')(_('cd', '@b'))
    assert str(matcher.match('bbcdcd')) == "[FT(0, 4){'@b': [(0, 2)]}]"
    matcher = _(_('b'), '+', '@b')(_('cd', '@b'))
    assert str(matcher.match('bbcdcd')) == "[FT(1, 4){'@b': [(1, 2)]}, FT(0, 6){'@b': [(0, 1), (0, 2)]}]"


def test_letter_123():
    _ = R
    matcher = _(lambda x, _: str.isalpha(x), '*')(_('123'))
    assert str(matcher.match('atfgy123a')) == '[FT(0, 8), FT(1, 8), FT(2, 8), FT(3, 8), FT(4, 8), FT(5, 8)]'
    matcher = _(lambda x, _: str.isalpha(x), '*', mode=Mode.Greedy)(_('123'))
    assert str(matcher.match('ab123a')) == '[FT(0, 5)]'
    matcher = _(_(lambda x, _: str.isalpha(x)), '*', mode=Mode.Greedy)(_('123'))
    assert str(matcher) == '[%<lambda>%]:G{0,inf}123'
    assert str(matcher.match('ab123a')) == '[FT(0, 5)]'


for func in (
        test_str,
        test_abc,
        test_abcda,
        test_abc_bbc,
        test_b_2_cd,
        test_optional_abc_bc,
        test_ab_c_star_c_plus,
        test_abc_and_abc,
        test_b_2_cd_counter,
        test_letter_123,
):
    func()
