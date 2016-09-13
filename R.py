from collections import namedtuple

# 原则上, 节点状态有3个: 'GO' 'NO' Result, 由broadcast(char)返回
Result = namedtuple('Result', 'epoche op ed')


def make_gen(target: str):
    # 识别target的生成器
    # 生成器 -> FA
    def gen(epoche: int, op: int):
        ed = op
        for expect_char in target:
            in_char = yield 'GO'
            if in_char == expect_char:
                ed += 1
            else:
                yield 'NO'
        yield Result(epoche, op, ed)

    return gen


class R:
    # 所有Result的容器
    bucket = []

    def __init__(self, target_rule, num=None, name: str = None):
        # R有两种形态, matcher和wrapper
        # matcher识别target
        self.target_rule = target_rule
        self.num = num
        self.name = name

        self.sibling_l = []
        self.next_rule = None

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
            assert cursor.next_rule is None and isinstance(other, R)
            cursor.next_rule = other
            cursor = other
        return R(self)

    def __str__(self):
        s = str(self.target_rule)

        def s_group() -> str:
            return '[' + s + ']'

        def did_s_group() -> bool:
            return s.startswith('[') and s.endswith(']')

        if self.sibling_l:
            s += '|' + '|'.join(str(i) for i in self.sibling_l)
            s = s_group()

        if self.num is not None:
            if not did_s_group():
                s = s_group()
            s += self.num
        if self.next_rule is not None:
            s += str(self.next_rule)
        return s

    def broadcast(self, char: str):
        ret = None
        # 层层广播, 使得状态转移
        if self.is_matcher:
            go_flag = False
            no_flag = False
            result_flag = None

            if self.fa_l:
                # 将char广播给状态机
                next_fa_l = []
                for fa in self.fa_l:
                    echo = fa.send(char)
                    if echo == 'GO':
                        go_flag = True
                        next_fa_l.append(fa)
                    elif isinstance(echo, Result):
                        # 成功, 将结果放入bucket中, 并激活下一级的R
                        result_flag = echo
                        R.bucket.append(echo)
                        if self.next_rule:
                            self.next_rule.active(echo)
                    elif echo == 'NO':
                        no_flag = True
                    else:
                        raise Exception
            if result_flag:
                ret = result_flag
            elif go_flag:
                ret = 'GO'
            elif no_flag and not go_flag:
                ret = 'No'
            else:
                raise Exception
        else:
            ret = self.target_rule.broadcast(char)
        return ret

    def active(self, prev: Result):
        if self.is_matcher:
            pass


if __name__ == '__main__':
    def test():
        _ = R
        matcher = _(_(_('abc') | _('cfg'), '{1}')(_('iop'), _('iop')), '{1}')
        print(matcher)


    test()
