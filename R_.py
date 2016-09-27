from math import inf


class Result:
    def __init__(self, epoch: int, ed: int, table: dict):
        self.epoch = epoch
        self.ed = ed
        self.table = table

    @property
    def capture_record(self) -> dict:
        record = {}
        for k in self.table:
            if k.startswith('@'):
                op = self.table['_' + k]
                record[k] = [(op, ed) for ed in self.table[k]]
        return record

    def __repr__(self):
        record = self.capture_record
        return 'FT({}, {}){}'.format(self.epoch, self.ed, record or '')

    def __eq__(self, other):
        if isinstance(other, Result):
            return self.epoch == other.epoch and self.ed == other.ed


class Success(Result):
    def invert(self) -> 'Fail':
        self.__class__ = Fail
        return self


class Fail(Result):
    def invert(self) -> 'Success':
        self.__class__ = Success
        return self


def make_gen(target, num: tuple) -> callable:
    # gen -> fa
    if isinstance(target, str):
        def gen(epoch: int, op: int, table: dict, log: bool) -> iter:
            table = table.copy()
            ed = op
            table['$prev_str'] = ''
            for expect_char in target:
                recv_char = yield 'GO'
                if log:
                    table['$prev_str'] += recv_char
                if recv_char == expect_char:
                    ed += 1
                else:
                    yield Fail(epoch, ed, table)
            yield Success(epoch, ed, table)
            yield 'NO'
    elif callable(target):
        def gen(epoch: int, op: int, table: dict, log: bool) -> iter:
            table = table.copy()
            recv_char = yield 'GO'
            table['$prev_str'] = recv_char if log else ''
            if target(recv_char, (epoch, op, table)):
                yield Success(epoch, op + 1, table)
            else:
                yield Fail(epoch, op + 1, table)
            yield 'NO'
    else:
        raise Exception

    if num == (1, 1):
        return gen
    else:
        def decorate_g(epoch: int, op: int, table: dict, log: bool) -> iter:
            counter = 0
            from_num, to_num = num
            if isinstance(from_num, str):
                from_num = to_num = len(table.get(from_num, ()))
            elif callable(from_num):
                from_num, to_num = from_num(epoch, op, table), to_num(epoch, op, table)
            assert 0 <= from_num <= to_num
            curr_state = Success(epoch, op, table.copy()) if from_num == 0 else 'GO'
            if to_num == 0:
                yield curr_state

            inner_gen = gen(epoch, op, table, log)
            next(inner_gen)
            while counter < to_num:
                recv_char = yield curr_state
                echo = inner_gen.send(recv_char)
                if isinstance(echo, Success):
                    counter += 1
                    if counter < to_num:
                        inner_gen = gen(epoch, echo.ed, table)
                        next(inner_gen)
                    if counter < from_num:
                        echo = 'GO'
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
    if isinstance(num, int) or callable(num):
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


def str_n(num: tuple) -> str:
    from_num, to_num = num
    if callable(from_num):
        from_num = '<{}>'.format(from_num.__name__)
        to_num = '<{}>'.format(to_num.__name__)
    if from_num == to_num:
        if from_num == 1:
            return ''
        return '{' + str(from_num) + '}'
    else:
        return '{' + str(from_num) + ',' + str(to_num) + '}'


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
            self.gen = make_gen(self.target_rule, self.num)

        self.xor_r = None
        self.invert = False

    @property
    def is_matcher(self) -> bool:
        return not self.is_wrapper

    @property
    def is_wrapper(self) -> bool:
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
            return '[' + s + ']'

        def is_group() -> bool:
            return s.startswith('[') and s.endswith(']')

        if self.xor_r:
            s = '[{}^{}]'.format(s, self.xor_r)
        elif self.invert:
            s = '~[{}]'.format(s)
        else:
            if self.demand_r:
                s += '&' + str(self.demand_r)
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
        return matcher
