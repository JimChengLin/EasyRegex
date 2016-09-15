from collections import namedtuple

Result = namedtuple('Result', 'epoche op ed')


def make_gen(target: str) -> callable:
    # 识别target的生成器
    # 生成器 -> FA
    def gen(epoche: int, op: int) -> iter:
        ed = op
        for expect_char in target:
            in_char = yield 'GO'
            if in_char == expect_char:
                ed += 1
            else:
                yield 'NO'
        yield Result(epoche, op, ed)

    return gen


# 状态有3个: 'GO' 'NO' Result, 由broadcast(char: str)返回
class R:
    def __init__(self, target_rule, num=None, name: str = None):
        # R有两种形态, matcher和wrapper
        # matcher识别target
        self.target_rule = target_rule
        self.num = num
        self.name = name

        self.next_r = None
        self.sibling_l = []

        if self.is_matcher:
            self.fa_l = []
            self.gen = make_gen(target_rule)

    @property
    def is_matcher(self) -> bool:
        return isinstance(self.target_rule, str)

    def __and__(self, other) -> 'R':
        assert isinstance(other, R)

    def __or__(self, other) -> 'R':
        assert isinstance(other, R)
        self.sibling_l.append(other)
        return self

    def __xor__(self, other) -> 'R':
        assert isinstance(other, R)

    def __invert__(self) -> 'R':
        pass

    def __call__(self, *other_l) -> 'R':
        if not other_l:
            return
        cursor = self
        for other in other_l:
            assert cursor.next_r is None and isinstance(other, R)
            cursor.next_r = other
            cursor = other
        return R(self)

    def __str__(self):
        s = str(self.target_rule)

        def s_group() -> str:
            return '[' + s + ']'

        def do_s_group() -> bool:
            return s.startswith('[') and s.endswith(']')

        if self.sibling_l:
            s += '|' + '|'.join(str(i) for i in self.sibling_l)
            s = s_group()

        if self.num is not None:
            if not do_s_group():
                s = s_group()
            s += self.num
        if self.next_r is not None:
            s += str(self.next_r)
        return s

    def broadcast(self, char: str):
        # 外到内广播char, 内到外返回result
        that_result = None
        if self.next_r:
            that_result = self.next_r.broadcast(char)

        # 广播完毕, 传递char给gen
        if self.is_matcher:
            # 状态
            state = {'GO': False, 'NO': False, 'Result': []}
            if self.fa_l:
                next_fa_l = []
                for fa in self.fa_l:
                    echo = fa.send(char)
                    if echo == 'GO':
                        state['GO'] = True
                        next_fa_l.append(fa)
                    elif isinstance(echo, Result):
                        state['Result'].append(echo)
                    elif echo == 'NO':
                        state['NO'] = True
                    else:
                        raise Exception
                self.fa_l = next_fa_l

            if state['Result']:
                # 激活下级
                if self.next_r:
                    for result in state['Result']:
                        self.next_r.active(result)
                this_result = state['Result']
            elif state['GO']:
                this_result = 'GO'
            elif state['NO'] or not self.fa_l:
                this_result = 'NO'
            else:
                raise Exception
        else:
            this_result = self.target_rule.broadcast(char)
            # 激活下级
            if isinstance(this_result, list) and self.next_r:
                for result in this_result:
                    self.next_r.active(result)

        if that_result is None and isinstance(this_result, list):
            return this_result
        if isinstance(that_result, list):
            return that_result
        if that_result == 'GO' or this_result == 'GO' or isinstance(this_result, list):
            return 'GO'
        if that_result == 'NO' or this_result == 'NO':
            return 'NO'
        raise Exception

    def active(self, prev_result: Result):
        if self.is_matcher:
            fa = self.gen(prev_result.epoche, prev_result.ed)
            next(fa)
            self.fa_l.append(fa)
        else:
            self.target_rule.active(prev_result)

    def match(self, resource: iter) -> list:
        result = []
        for i, char in enumerate(resource):
            self.active(Result(i, i, i))
            echo = self.broadcast(char)
            if isinstance(echo, list):
                result.extend(echo)
        return result


if __name__ == '__main__':
    def test_str():
        _ = R
        matcher = _(_(_('abc') | _('cfg'), '{1}')(_('iop'), _('iop')), '{1}')
        assert str(matcher) == '[[abc|cfg]{1}iopiop]{1}'


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


    for func in (test_str,
                 test_abc,
                 test_abcda):
        func()
