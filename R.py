from enum import Enum
from itertools import chain
from math import inf
from typing import Iterable, Callable


class Res:
    def __init__(self, epoch: int, op: int, ed: int = None, nth=0, prev_str='', capture_t=()):
        self.epoch = epoch
        self.op = op

        self.ed = ed or op
        self.nth = nth
        self.prev_str = prev_str
        self.capture_t = capture_t

    @property
    def capture_d(self):
        d = {}
        for k, *item in self.capture_t:
            if isinstance(k, str):
                op, ed = item
                d.setdefault(k, []).append((op, ed))
        return d

    def __repr__(self):
        return 'FT({}, {}){}'.format(self.epoch, self.ed, self.capture_d or '')

    def __eq__(self, other):
        if isinstance(other, Res):
            return self.epoch == other.epoch and self.ed == other.ed

    def clone(self, **kwargs):
        return Res(**{**self.__dict__, **kwargs})

    def as_success(self):
        self.__class__ = Success
        return self

    def as_fail(self):
        self.__class__ = Fail
        return self

    def to_param(self):
        return self.epoch, self.ed, self.capture_d


class Success(Res):
    def invert(self):
        return self.as_fail()

    def __bool__(self):
        return True


class Fail(Res):
    def invert(self):
        return self.as_success()

    def __bool__(self):
        return False


def concat(prev_str, recv):
    result = (*prev_str, recv) if isinstance(prev_str, tuple) or not isinstance(recv, str) else prev_str + recv
    return result


def make_gen(target, num_t: tuple):
    if isinstance(target, Iterable):
        def gen(prev_res: Res, log: bool):
            res = prev_res.clone()
            for expect in target:
                recv = yield 'GO'
                res.ed += 1
                if log:
                    res.prev_str = concat(res.prev_str, recv)
                if recv != expect:
                    yield res.as_fail()
                    yield 'DONE'
            yield res.as_success()
            yield 'DONE'
    elif isinstance(target, Callable):
        def gen(prev_res: Res, log: bool):
            res = prev_res.clone()
            recv = yield 'GO'
            res.ed += 1
            res.prev_str = recv if log else ''
            try:
                accept = target(recv, res.to_param())
            except TypeError:
                accept = False
            if accept:
                yield res.as_success()
            else:
                yield res.as_fail()
            yield 'DONE'
    else:
        raise Exception

    if num_t == (1, 1):
        return gen
    else:
        def decorate_gen(prev_res: Res, log: bool):
            from_num, to_num = explain_n(prev_res, num_t)
            curr_state = 'OPT' if from_num == 0 else 'GO'
            if to_num == 0:
                yield curr_state

            counter = 0
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
                    if counter == to_num:
                        yield echo
                elif isinstance(echo, Fail):
                    yield echo
                    break
                curr_state = echo
            yield 'DONE'

        return decorate_gen


def parse_n(num):
    if num is None:
        return 1, 1
    if isinstance(num, (int, Callable)):
        return num, num
    if isinstance(num, tuple):
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
    from_num, to_num = num_t
    if isinstance(from_num, str):
        from_num = to_num = len(res.capture_d.get(from_num, ()))
    elif isinstance(from_num, Callable):
        from_num, to_num = from_num(res.to_param()), to_num(res.to_param())
    assert 0 <= from_num <= to_num
    return from_num, to_num


class Mode(Enum):
    All = 'A'
    Greedy = 'G'
    Lazy = 'L'


def gl_update(res_l: list):
    update_res_l = []
    for res in filter(bool, res_l):
        for k, *item in res.capture_t:
            if isinstance(k, str):
                break
            v = item.pop()
            k.best_length = max(v, k.best_length or 0) if k.mode is Mode.Greedy else min(v, k.best_length or inf)
        update_res_l.append(res)
    return update_res_l


def gl_filter(res_l: list):
    filter_res_l = []
    for res in res_l:
        for k, *item in res.capture_t:
            if isinstance(k, str):
                filter_res_l.append(res)
                break
            v = item.pop()
            if k.mode is Mode.Greedy:
                if v < (k.best_length or 0):
                    break
            else:
                if v > (k.best_length or inf):
                    break
        else:
            filter_res_l.append(res)
    return filter_res_l


class R:
    def __init__(self, target_rule, num=None, name: str = None, mode=Mode.All):
        self.target_rule = target_rule
        self.num_t = parse_n(num)
        self.name = name
        self.mode = mode

        self.and_r = None
        self.or_r_l = []
        self.next_r = None

        self.xor_r = None
        self.invert = False
        self._is_top = False

        if self.is_matcher:
            self.fa_l = []
            self.gen = make_gen(self.target_rule, self.num_t)
        if self.mode is not Mode.All:
            self.best_length = None

    @property
    def is_matcher(self):
        return not self.is_wrapper

    @property
    def is_wrapper(self):
        return isinstance(self.target_rule, R)

    @property
    def is_top(self):
        return self._is_top

    @is_top.setter
    def is_top(self, val: bool):
        cursor = self
        while True:
            cursor._is_top = val
            if cursor.is_wrapper:
                cursor = cursor.target_rule
            else:
                break

    def __and__(self, other: 'R'):
        other = other.clone()
        self_clone = self.clone()
        if self_clone.or_r_l:
            cursor = R(self_clone)
        else:
            cursor = self_clone
            while cursor.and_r is not None:
                cursor = cursor.and_r
        cursor.and_r = other
        return self_clone

    def __or__(self, other: 'R'):
        other = other.clone()
        self_clone = self.clone()
        self_clone.or_r_l.append(other)
        return self_clone

    def __xor__(self, other: 'R'):
        other = other.clone()
        self_clone = R(self.clone())
        self_clone.xor_r = other
        return R(self_clone)

    def __invert__(self):
        self_clone = R(self.clone())
        self_clone.invert = True
        return R(self_clone)

    def __call__(self, *other_l):
        self_clone = self.clone()
        if not other_l:
            return self_clone
        cursor = self_clone
        for other in other_l:
            assert cursor.next_r is None
            other = other.clone() if isinstance(other, R) else R(other)  # 自动转化
            cursor.next_r = other
            cursor = other
        return R(self_clone)

    def __repr__(self):
        if self.is_matcher and isinstance(self.target_rule, Callable):
            s = '<{}>'.format(self.target_rule.__name__)
        else:
            s = str(self.target_rule)

        def group():
            return '[{}]'.format(s)

        def is_group():
            return s.startswith('[') and s.endswith(']')

        if self.xor_r:
            s = '[{}^{}]'.format(s, self.xor_r)
        elif self.invert:
            s = '[~{}]'.format(s)
        else:
            if self.and_r:
                s = '{}&{}'.format(s, self.and_r)
            if self.or_r_l:
                s = '[{}|{}]'.format(s, '|'.join(str(or_r) for or_r in self.or_r_l))
            if (self.and_r or (self.is_wrapper and self.target_rule.and_r)) and self.next_r and not is_group():
                s = group()

        num_str = str_n(self.num_t)
        if num_str:
            if len(s) > 1 and not is_group():
                s = group()
            s += num_str
        if self.next_r:
            s += str(self.next_r)
        return s

    def broadcast(self, char=None):
        if char is None:
            if self.is_matcher:
                self.fa_l.clear()
            if self.mode is not Mode.All:
                self.best_length = None
        if self.next_r:
            next_res_l = self.next_r.broadcast(char)

        if self.is_matcher:
            self_res_l = []
            if self.fa_l:
                fa_l = []
                for fa in self.fa_l:
                    echo = fa.send(char)
                    if echo != 'DONE':
                        fa_l.append(fa)
                    if isinstance(echo, Res):
                        self_res_l.append(echo)
                self.fa_l = fa_l
        else:
            self_res_l = self.target_rule.broadcast(char)
            res_l = []
            for res in self_res_l:
                if not res:
                    res_l.append(res)
                else:
                    from_num, to_num = explain_n(res, self.num_t)
                    res.nth += 1
                    if res.nth < to_num:
                        if self.name and from_num <= res.nth <= to_num:
                            seed = res.clone(capture_t=(*res.capture_t, (self.name, res.op, res.ed)))
                        else:
                            seed = res
                        self.active(seed)
                    if from_num <= res.nth <= to_num:
                        res.nth = 0  # 已激活
                        res_l.append(res)
            self_res_l = res_l

        if self.xor_r:
            for res in self_res_l:
                self.xor_r.active(res.clone(ed=res.op, prev_str=''))
                for char in res.prev_str:
                    xor_res_l = self.xor_r.broadcast(char)
                self.xor_r.broadcast()

                if res:
                    res.as_fail()
                    for xor_res in xor_res_l:
                        if not xor_res:
                            res.as_success()
                            res.capture_t += xor_res.capture_t
                    if not xor_res_l:
                        res.as_success()
                else:
                    for xor_res in xor_res_l:
                        if xor_res:
                            res.as_success()
                            res.capture_t += xor_res.capture_t
        elif self.invert:
            for i in self_res_l:
                i.invert()
        else:
            if self.and_r:
                for res in self_res_l:
                    if not res:
                        continue
                    else:
                        self.and_r.active(res.clone(ed=res.op, prev_str=''))
                        for char in res.prev_str:
                            and_res_l = self.and_r.broadcast(char)
                        self.and_r.broadcast()

                        res.as_fail()
                        for and_res in and_res_l:
                            if and_res:
                                res.as_success()
                                res.capture_t += and_res.capture_t
            for or_r in self.or_r_l:
                or_r_res_l = or_r.broadcast(char)
                self_res_l.extend(or_r_res_l)

        for res in filter(bool, self_res_l):
            if self.name:
                res.capture_t = (*res.capture_t, (self.name, res.op, res.ed))
            if self.mode is not Mode.All:
                res.capture_t = ((self, res.ed - res.op), *res.capture_t)
        self_res_l = gl_filter(self_res_l)
        if self.next_r:
            parent = self
            next_r = self.next_r
            seed_res_l = list(filter(bool, self_res_l))
            while seed_res_l:
                res_l = []
                for res in seed_res_l:
                    echo = next_r.active(res.clone(op=res.ed, prev_str=''))
                    if echo == 'OPT' and (not self.is_top or (self.is_top and not next_r.next_r)):
                        if parent.mode is not Mode.All:
                            res_l.append(res.clone(capture_t=((parent, 0), *res.capture_t)))
                        else:
                            res_l.append(res)
                seed_res_l = res_l
                if next_r.next_r:
                    parent = next_r
                    next_r = next_r.next_r
                else:
                    next_res_l.extend(res_l)
                    break
        if self.next_r:
            return next_res_l
        else:
            return self_res_l

    def active(self, prev_res: Res, log=False, affect=True):
        log = bool(log or self.and_r or self.xor_r)
        if self.is_matcher:
            fa = self.gen(prev_res, log)
            echo = next(fa)
            if affect:
                self.fa_l.append(fa)
        else:
            echo = self.target_rule.active(prev_res, log, affect)
            if echo == 'GO':
                from_num, _ = explain_n(prev_res, self.num_t)
                if from_num == 0:
                    echo = 'OPT'

        if self.xor_r:
            xor_echo = self.xor_r.active(prev_res, affect=False)
            echo = 'GO' if xor_echo == echo else 'OPT'
        elif self.invert:
            echo = 'GO' if echo == 'OPT' else 'OPT'
        else:
            if echo == 'OPT' and self.and_r:
                and_echo = self.and_r.active(prev_res, affect=False)
                if and_echo != 'OPT':
                    echo = 'GO'
            for or_r in self.or_r_l:
                or_r_echo = or_r.active(prev_res)
                if or_r_echo == 'OPT':
                    echo = 'OPT'
        if self.next_r and echo == 'OPT' and self.is_top:
            if self.mode is not Mode.All:
                self.next_r.active(prev_res.clone(capture_t=((self, 0), *prev_res.capture_t)))
            else:
                self.next_r.active(prev_res)
        return echo

    def match(self, source: Iterable):
        self.is_top = True
        res_l = []
        for i, char in enumerate(chain([EOF], source, [EOF])):
            i -= 1
            self.active(Res(i, i))
            res_l.extend(gl_update(self.broadcast(char)))
        res_l = gl_filter(res_l)
        self.broadcast()
        self.is_top = False
        return res_l

    def clone(self):
        matcher = R(self.target_rule if self.is_matcher else self.target_rule.clone(), self.num_t, self.name, self.mode)
        if self.and_r:
            matcher.and_r = self.and_r.clone()
        matcher.or_r_l[:] = (i.clone() for i in self.or_r_l)
        if self.xor_r:
            matcher.xor_r = self.xor_r.clone()
        matcher.invert = self.invert
        if self.next_r:
            matcher.next_r = self.next_r.clone()
        return matcher


class EOF:
    def __repr__(self):
        return '(EOF)'
