from copy import copy
from math import inf

NULL = '\00'


class Result:
    def __init__(self, epoche: int, op: int, ed: int, nth=0, prev_str=''):
        self.epoche = epoche
        self.op = op
        self.ed = ed
        self.nth = nth
        self.prev_str = prev_str

    def __eq__(self, other):
        if isinstance(other, Result):
            return self.epoche == other.epoche and self.ed == other.ed

    def __repr__(self):
        return 'FT' + str((self.epoche, self.ed))


def make_gen(target: str, num: tuple) -> callable:
    # 识别target的生成器
    # 生成器 -> FA
    def gen(epoche: int, op: int, nth: int, record: bool) -> iter:
        ed = op
        prev_str = ''
        for expect_char in target:
            recv_char = yield 'GO'
            if record:
                prev_str += recv_char
            if recv_char == expect_char:
                ed += 1
            else:
                yield 'NO'
        yield Result(epoche, op, ed, nth, prev_str)
        yield 'NO'

    if num[-1] == 1:
        return gen
    else:
        def decorate_g(epoche: int, op: int, nth: int, record: bool) -> iter:
            counter = 0
            from_num, to_num = num
            inner_gen = gen(epoche, op, nth, record)
            next(inner_gen)
            curr_state = 'GO'

            while counter < to_num:
                recv_char = yield curr_state
                echo = inner_gen.send(recv_char)
                if isinstance(echo, Result):
                    counter += 1
                    ed = echo.ed
                    if counter < from_num:
                        echo = 'GO'
                    if counter < to_num:
                        inner_gen = gen(epoche, ed, nth, record)
                        next(inner_gen)
                    elif counter == to_num:
                        yield echo
                curr_state = echo
            yield 'NO'

        return decorate_g


def is_l(obj) -> bool:
    return isinstance(obj, list)


def parse_n(num) -> tuple:
    if num is None:
        return 1, 1
    if isinstance(num, int):
        return num, num
    if isinstance(num, tuple):
        return num
    if isinstance(num, str):
        if num == '*':
            return 0, inf
        if num == '+':
            return 1, inf
        assert num.startswith('{') and num.endswith('}')
        num = num[1:-1]
        num = tuple(map(int, num.split(',')))
        if len(num) == 1:
            num *= 2
        return num
    raise Exception


def str_n(num: tuple) -> str:
    from_num, to_num = num
    assert from_num <= to_num
    if from_num == to_num:
        if from_num == 1:
            return ''
        return '{' + str(from_num) + '}'
    else:
        return '{' + str(from_num) + ',' + str(to_num) + '}'


# 状态: 'GO' 'NO' Result, 由broadcast(char: str)返回
class R:
    def __init__(self, target_rule, num=None, name: str = None):
        # R有两种形态, matcher和wrapper
        # matcher识别target
        self.target_rule = target_rule
        self.num = parse_n(num)
        self.name = name

        self.next_r = None
        self.demand_r = None
        self.sibling_l = []

        if self.is_matcher:
            self.fa_l = []
            self.gen = make_gen(target_rule, self.num)

    @property
    def is_matcher(self) -> bool:
        return isinstance(self.target_rule, str)

    def __and__(self, other) -> 'R':
        assert isinstance(other, R)
        other = other.clone()
        self_clone = self.clone()
        if self_clone.sibling_l:
            cursor = R(self_clone)
        else:
            cursor = self_clone
            while cursor.demand_r is not None:
                cursor = cursor.demand_r
        cursor.demand_r = other
        return self_clone

    def __or__(self, other) -> 'R':
        assert isinstance(other, R)
        other = other.clone()
        self_clone = self.clone()
        self_clone.sibling_l.append(other)
        return self_clone

    def __xor__(self, other) -> 'R':
        assert isinstance(other, R)

    def __invert__(self) -> 'R':
        pass

    def __call__(self, *other_l) -> 'R':
        if not other_l:
            return
        self_clone = self.clone()
        cursor = self_clone
        for other in other_l:
            assert cursor.next_r is None and isinstance(other, R)
            other = other.clone()
            cursor.next_r = other
            cursor = other
        return R(self_clone)

    def __repr__(self):
        s = str(self.target_rule)

        def s_group() -> str:
            return '[' + s + ']'

        def do_s_group() -> bool:
            return s.startswith('[') and s.endswith(']')

        if self.demand_r:
            s += '&' + str(self.demand_r)
            if self.next_r and self.next_r.demand_r is None:
                s = s_group()
        if self.sibling_l:
            s += '|' + '|'.join(str(i) for i in self.sibling_l)
            s = s_group()

        num_str = str_n(self.num)
        if num_str:
            if len(s) > 1 and not do_s_group():
                s = s_group()
            s += num_str
        if self.next_r is not None:
            s += str(self.next_r)
        return s

    def broadcast(self, char: str):
        # 广播char
        that_result = None
        if self.next_r:
            that_result = self.next_r.broadcast(char)

        active_result = []
        # 传递char给自身
        if self.is_matcher:
            # 状态
            state = {'GO': False, 'NO': False, 'Result': []}
            if self.fa_l:
                fa_l = []
                for fa in self.fa_l:
                    echo = fa.send(char)
                    if echo == 'GO':
                        state['GO'] = True
                        fa_l.append(fa)
                    elif isinstance(echo, Result):
                        state['Result'].append(echo)
                        fa_l.append(fa)
                    elif echo == 'NO':
                        state['NO'] = True
                    else:
                        raise Exception
                self.fa_l = fa_l

            if state['Result']:
                active_result.extend(state['Result'])
                this_result = state['Result']
            elif state['GO']:
                this_result = 'GO'
            elif state['NO'] or not self.fa_l:
                this_result = 'NO'
            else:
                raise Exception
        else:
            this_result = self.target_rule.broadcast(char)
            if is_l(this_result):
                filter_result = []
                # 有效区间
                from_num, to_num = self.num
                for res in this_result:
                    res.nth += 1
                    if res.nth < to_num:
                        self.active(res)
                    if from_num <= res.nth <= to_num:
                        res.nth = 0
                        filter_result.append(res)
                this_result = filter_result
                if this_result:
                    active_result.extend(this_result)
                else:
                    this_result = 'GO'

        if self.demand_r and is_l(this_result):  # OP AND
            filter_result = []
            for res in this_result:
                demand_result = None
                self.demand_r.active(Result(res.epoche, res.op, res.op))
                for char in res.prev_str:
                    demand_result = self.demand_r.broadcast(char)
                self.demand_r.broadcast(NULL)
                if is_l(demand_result):
                    for demand_res in demand_result:
                        if demand_res.epoche == res.epoche and demand_res.ed == res.ed:
                            filter_result.append(res)
                            break
            if filter_result:
                this_result = filter_result
            else:
                this_result = 'GO'

        # 传递char给sibling
        for sibling in self.sibling_l:
            sibling_result = sibling.broadcast(char)
            if is_l(sibling_result):
                active_result.extend(sibling_result)
                if is_l(this_result):
                    this_result.extend(sibling_result)
                else:
                    this_result = sibling_result
            elif sibling_result == 'GO' and this_result == 'NO':
                this_result = 'GO'

        # 激活下级
        if self.next_r:
            for res in active_result:
                self.next_r.active(res)
            if self.next_r.num[0] == 0 and self.next_r.next_r is None:
                if is_l(that_result):
                    that_result.extend(active_result)
                else:
                    that_result = active_result

        if that_result is None and is_l(this_result):
            return this_result
        if is_l(that_result):
            return that_result
        if that_result == 'GO' or this_result == 'GO' or is_l(this_result):
            return 'GO'
        if that_result == 'NO' or this_result == 'NO':
            return 'NO'
        raise Exception

    def active(self, prev_result: Result, record=False):
        if self.is_matcher:
            fa = self.gen(prev_result.epoche, prev_result.ed, prev_result.nth, record or bool(self.demand_r))
            next(fa)
            self.fa_l.append(fa)
        else:
            self.target_rule.active(prev_result, bool(self.demand_r))

        for sibling in self.sibling_l:
            sibling.active(prev_result)
        if self.num[0] == 0 and self.next_r:
            self.next_r.active(prev_result)

    def match(self, source: iter) -> list:
        assert self.num[0] > 0
        res_l = []
        for i, char in enumerate(source):
            self.active(Result(i, i, i))
            this_result = self.broadcast(char)
            if is_l(this_result):
                res_l.extend(this_result)
        return res_l

    def clone(self) -> 'R':
        matcher = copy(self)
        if matcher.next_r:
            matcher.next_r = matcher.next_r.clone()
        if matcher.demand_r:
            matcher.demand_r = matcher.demand_r.clone()
        matcher.sibling_l = [i.clone() for i in matcher.sibling_l]

        if matcher.is_matcher:
            matcher.fa_l = []
        else:
            matcher.target_rule = matcher.target_rule.clone()
        return matcher


if __name__ == '__main__':
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
        matcher = (_('abc') & _('abc') & _('abc'))(_('d'))
        assert str(matcher) == '[abc&abc&abc]d'
        assert str(matcher.match('abcd')) == '[FT(0, 4)]'


    for func in (
            test_str,
            test_abc,
            test_abcda,
            test_abc_bbc,
            test_b_2_cd,
            test_optional_abc_bc,
            test_ab_c_star_c_plus,
            test_abc_and_abc,
    ):
        func()
