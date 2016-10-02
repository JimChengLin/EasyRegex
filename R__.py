from itertools import chain
from math import inf
from typing import Iterable, Callable


class Res:
    def __init__(self, epoch: int, ed: int, nth=0, prev_str='', capture_t=(), op: int = None):
        self.epoch = epoch
        self.ed = ed
        self.nth = nth
        self.prev_str = prev_str
        self.capture_t = capture_t
        self.op = op

    @property
    def capture_d(self):
        d = {}
        for k, op, ed in self.capture_t:
            d.setdefault(k, []).append((op, ed))
        return d

    def __repr__(self):
        return 'FT({}, {}){}'.format(self.epoch, self.ed, self.capture_d or '')

    def __eq__(self, other):
        if isinstance(other, Res):
            return self.epoch == other.epoch and self.ed == other.ed

    def copy(self):
        return Res(self.epoch, self.ed, self.nth, self.prev_str, self.capture_t)

    def as_success(self):
        self.__class__ = Success
        return self

    def as_fail(self):
        self.__class__ = Fail
        return self


class Success(Res):
    def invert(self):
        self.__class__ = Fail
        return self


class Fail(Res):
    def invert(self):
        self.__class__ = Success
        return self


def make_gen(target, num_t: tuple):  # fa
    if isinstance(target, Iterable):
        def gen(prev_res: Res, log: bool):
            res = prev_res.copy()
            for expect in target:
                recv = yield 'GO'
                if log:
                    res.prev_str += recv
                if recv == expect:
                    res.ed += 1
                else:
                    yield res.as_fail()
                    yield 'NO'
            yield res.as_success()
            yield 'NO'
    elif isinstance(target, Callable):
        def gen(prev_res: Res, log: bool):
            res = prev_res.copy()
            recv = yield 'GO'
            res.prev_str = recv if log else ''
            if target(recv, prev_res):
                yield res.as_success()
            else:
                yield res.as_fail()
            yield 'No'
    else:
        raise Exception

    if num_t == (1, 1):
        return gen
    else:
        def decorate_gen(prev_res: Res, log: bool):
            counter = 0
            from_num, to_num = explain_n(prev_res, num_t)
            curr_state = 'OK' if from_num == 0 else 'GO'
            if to_num == 0:
                yield curr_state

            inner_gen = gen(prev_res, log)
            next(inner_gen)
            while counter < to_num:
                recv = yield curr_state
                echo = inner_gen.send(recv)
                if isinstance(echo, Success):
                    counter += 1
                    if counter < to_num:
                        inner_gen = gen(echo, log)
                        next(inner_gen)
                    if counter < from_num:
                        echo = 'GO'
                    elif counter == to_num:
                        yield echo
                elif isinstance(echo, Fail):
                    yield echo
                    yield 'NO'
                curr_state = echo
            yield 'NO'

        return decorate_gen


def is_l(obj):
    return isinstance(obj, list)


def parse_n(num):
    if num is None:
        return 1, 1
    if isinstance(num, (int, Callable)):
        return num, num
    if isinstance(num, tuple):
        assert isinstance(num[0], type(num[1]))
        return num
    if isinstance(num, str):
        if num == '*':
            return 0, inf
        if num == '+':
            return 1, inf
        if num.startswith('@'):
            return num, num
        if num.startswith('{') and num.endswith('}'):
            num = num[1:-1]
            num = tuple(map(int, num.split(',')))
            if len(num) == 1:
                num *= 2
            return num
    raise Exception


def str_n(num_t: tuple):
    from_num, to_num = num_t
    if isinstance(from_num, Callable):
        tpl = '<{}>'.format
        from_num, to_num = tpl(from_num.__name__), tpl(to_num.__name__)
    if from_num == to_num:
        if from_num == 1:
            return ''
        return '{' + str(from_num) + '}'
    else:
        return '{' + str(from_num) + ',' + str(to_num) + '}'


def explain_n(res: Res, num_t: tuple):
    epoch, op, capture_d = res.epoch, res.ed, res.capture_d
    from_num, to_num = num_t
    if isinstance(from_num, str):
        from_num = to_num = len(capture_d.get(from_num, ()))
    elif isinstance(from_num, Callable):
        from_num, to_num = from_num(epoch, op, capture_d), to_num(epoch, op, capture_d)
    assert 0 <= from_num <= to_num
    return from_num, to_num


class R:
    def __init__(self, target_rule, num=None, name: str = None):
        self.target_rule = target_rule
        self.num = parse_n(num)
        self.name = name

        self.next_r = None
        self.sibling_l = []
        self.demand_r = None

        if self.is_matcher:
            self.fa_l = []
            self.gen = make_gen(self.target_rule, self.num)

        self.xor_r = None
        self.invert = Fail

    @property
    def is_matcher(self):
        return not self.is_wrapper

    @property
    def is_wrapper(self):
        return isinstance(self.target_rule, R)

    def __and__(self, other: 'R') -> 'R':
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

    def __or__(self, other: 'R') -> 'R':
        other = other.clone()
        self_clone = self.clone()
        self_clone.sibling_l.append(other)
        return self_clone

    def __xor__(self, other: 'R') -> 'R':
        other = other.clone()
        self_clone = R(self.clone())
        self_clone.xor_r = other
        return R(self_clone)

    def __invert__(self) -> 'R':
        self_clone = R(self.clone())
        self_clone.invert = True
        return R(self_clone)

    def __call__(self, *other_l) -> 'R':
        if not other_l:
            return self
        self_clone = self.clone()
        cursor = self_clone
        for other in other_l:
            assert cursor.next_r is None
            other = other.clone() if isinstance(other, R) else R(other)
            cursor.next_r = other
            cursor = other
        return R(self_clone)

    def __repr__(self):
        s = str(self.target_rule)

        def group() -> str:
            return '[{}]'.format(s)

        def is_group() -> bool:
            return s.startswith('[') and s.endswith(']')

        if self.xor_r:
            s = '[{}^{}]'.format(s, self.xor_r)
        elif self.invert:
            s = '~[{}]'.format(s)
        else:
            if self.demand_r:
                s += '&{}'.format(self.demand_r)
            if self.sibling_l:
                s += '|' + '|'.join(str(i) for i in self.sibling_l)
                s = group()
            if (self.demand_r or (self.is_wrapper and self.target_rule.demand_r)) and self.next_r and not is_group():
                s = group()

        num_str = str_n(self.num)
        if num_str:
            if len(s) > 1 and not is_group():
                s = group()
            s += num_str
        if self.next_r:
            s += str(self.next_r)
        return s

    def broadcast(self, char):
        return char

    def active(self, prev_res: Res, log=False, append=True):
        log = bool(log or self.demand_r or self.xor_r)
        if self.is_matcher:
            fa = self.gen(prev_res, log)
            echo = next(fa)
            if append:
                self.fa_l.append(fa)
        else:
            echo = self.target_rule.active(prev_res, log)
            if echo == 'GO':
                from_num, _ = explain_n(prev_res, self.num)
                if from_num == 0:
                    echo = 'OK'

        if self.xor_r:
            xor_echo = self.xor_r.active(prev_res, append=False)
            if xor_echo == echo:
                echo = 'GO'
            else:
                echo = 'OK'
        elif self.invert:
            if echo == 'GO':
                echo = 'OK'
            else:
                echo = 'GO'
        else:
            if echo == 'OK' and self.demand_r:
                demand_echo = self.demand_r.active(prev_res, append=False)
                if demand_echo != 'OK':
                    echo = 'GO'
            for sibling in self.sibling_l:
                sibling_echo = sibling.active(prev_res, append=False)
                if sibling_echo == 'OK':
                    echo = 'OK'
                    break
        return echo

    def match(self, source: Iterable) -> list:
        res_l = []
        for i, char in chain([(-1, MatchStart)], enumerate(chain(source, [MatchEnd]))):
            self.active(Res(i, i))
            this_echo = self.broadcast(char)
            if is_l(this_echo):
                res_l.extend(this_echo)
        return res_l

    def clone(self) -> 'R':
        matcher = R(self.target_rule if self.is_matcher else self.target_rule.clone(), self.num, self.name)
        if self.demand_r:
            matcher.demand_r = self.demand_r.clone()
        matcher.sibling_l.extend(i.clone() for i in self.sibling_l)
        if self.xor_r:
            matcher.xor_r = self.xor_r.clone()
        matcher.invert = self.invert
        if self.next_r:
            matcher.next_r = self.next_r.clone()


class MatchStart:
    pass


class MatchEnd:
    pass
