from itertools import chain
from math import inf
from typing import Iterable, Callable


class Res:
    def __init__(self, epoch: int, ed: int, nth=0, prev_str='', capture_t=(), **_):
        self.epoch = epoch
        self.ed = self.op = ed

        self.nth = nth
        self.prev_str = prev_str
        self.capture_t = capture_t

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
        return Res(**self.__dict__)

    def as_success(self):
        self.__class__ = Success
        return self

    def as_fail(self):
        self.__class__ = Fail
        return self


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


def make_gen(target, num_t: tuple):  # -> fa
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
                    yield 'DONE'
            yield res.as_success()
            yield 'DONE'
    elif isinstance(target, Callable):
        def gen(prev_res: Res, log: bool):
            res = prev_res.copy()
            recv = yield 'GO'
            res.prev_str = recv if log else ''
            if target(recv, prev_res):
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
            counter = 0
            from_num, to_num = explain_n(prev_res, num_t)
            curr_state = 'OPT' if from_num == 0 else 'GO'
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
    from_num, to_num = num_t
    if isinstance(from_num, str):
        from_num = to_num = len(res.capture_d.get(from_num, ()))
    elif isinstance(from_num, Callable):
        from_num, to_num = from_num(res), to_num(res)
    assert 0 <= from_num <= to_num
    return from_num, to_num


class R:
    def __init__(self, target_rule, num=None, name: str = None):
        self.target_rule = target_rule
        self.num_t = parse_n(num)
        self.name = name

        self.and_r = None
        self.or_r_l = []
        self.next_r = None

        if self.is_matcher:
            self.fa_l = []
            self.gen = make_gen(self.target_rule, self.num_t)

        self.xor_r = None
        self.invert = False

    @property
    def is_matcher(self):
        return not self.is_wrapper

    @property
    def is_wrapper(self):
        return isinstance(self.target_rule, R)

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
        if not other_l:
            return self
        self_clone = self.clone()
        cursor = self_clone
        for other in other_l:
            assert cursor.next_r is None
            other = other.clone() if isinstance(other, R) else R(other)  # 自动转化
            cursor.next_r = other
            cursor = other
        return R(self_clone)

    def __repr__(self):
        if isinstance(self.target_rule, Callable):
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
                s += '&' + str(self.and_r)
            if self.or_r_l:
                s += '|' + '|'.join(str(or_r) for or_r in self.or_r_l)
                s = group()
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

    def broadcast(self, char):
        if self.next_r:
            next_res_l = self.next_r.broadcast(char)

        if self.is_matcher:
            this_res_l = []
            if self.fa_l:
                fa_l = []
                for fa in self.fa_l:
                    echo = fa.send(char)
                    if echo != 'NO':
                        fa_l.append(fa)
                    if isinstance(echo, Res):
                        this_res_l.append(echo)
                self.fa_l = fa_l
        else:
            this_res_l = self.target_rule.broadcast(char)
            res_l = []
            for res in this_res_l:
                from_num, to_num = explain_n(res, self.num_t)
                res.nth += 1
                if res.nth < to_num:
                    self.active(res)
                if from_num <= res.nth <= to_num:
                    res.nth = 0  # 已激活
                    res_l.append(res)
            this_res_l = res_l

        if self.xor_r:
            res_l = []
            for res in this_res_l:
                self.xor_r.active(res)
                for char in res.prev_str:
                    xor_res_l = self.xor_r.broadcast(char)
                self.xor_r.broadcast(None)
                if xor_res_l:
                    res_l.append(res)
                    break
            for res in this_res_l:
                self.xor_r.active(res)
                for char in res.prev_str:
                    xor_res_l = self.xor_r.broadcast(char)
                self.xor_r.broadcast(None)
                if xor_res_l:
                    res_l.append(res)
                    break
            this_res_l = res_l
        elif self.invert:
            this_res_l = [i.invert() for i in this_res_l]
        else:
            if self.and_r and this_res_l:
                res_l = []
                for res in this_res_l:
                    self.and_r.active(res)
                    for char in res.prev_str:
                        and_res_l = self.and_r.broadcast(char)
                    self.and_r.broadcast(None)
                    if and_res_l:
                        res_l.append(res)
                        break
                this_res_l = res_l

            for or_r in self.or_r_l:
                or_r_res_l = or_r.broadcast(char)
                this_res_l.extend(or_r_res_l)
        if self.name and this_res_l:
            for res in this_res_l:
                res.capture_t += (self.name, res.op, res.ed)

        if self.next_r:
            cursor = self.next_r
            seed_res_l = this_res_l[:]
            while seed_res_l:
                res_l = []
                for res in seed_res_l:
                    echo = cursor.active(res)
                    if echo == 'OPT':
                        res_l.append(res)
                if self.next_r.next_r:
                    cursor = self.next_r
                    seed_res_l = res_l
                else:
                    next_res_l.extend(res_l)
        if self.next_r:
            return next_res_l
        else:
            return this_res_l

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
        return echo

    def match(self, source: Iterable):
        res_l = []
        for i, char in enumerate(chain([EOF], source, [EOF])):
            self.active(Res(i - 1, i - 1))
            res_l.extend(filter(bool, self.broadcast(char)))
        return res_l

    def clone(self):
        matcher = R(self.target_rule if self.is_matcher else self.target_rule.clone(), self.num_t, self.name)
        if self.and_r:
            matcher.and_r = self.and_r.clone()
        matcher.or_r_l.extend(i.clone() for i in self.or_r_l)
        if self.xor_r:
            matcher.xor_r = self.xor_r.clone()
        matcher.invert = self.invert
        if self.next_r:
            matcher.next_r = self.next_r.clone()


class EOF:
    pass
