from math import inf
from typing import Iterable, Callable, Iterator, Dict, List, Tuple, TypeVar


class Res:
    def __init__(self, epoch: int, ed: int, table: dict):
        self.epoch = epoch
        self.ed = ed
        self.table = table

    def __repr__(self):
        return 'FT({}, {}){}'.format(self.epoch, self.ed, self.capture_record or '')

    def __eq__(self, other):
        if isinstance(other, Res):
            return self.epoch == other.epoch and self.ed == other.ed

    @property
    def capture_record(self) -> Dict[str, List[Tuple[int, int]]]:
        record = {}
        for k in self.table:
            if k.startswith('@'):
                op = self.table['_' + k]
                record[k] = [(op, ed) for ed in self.table[k]]
        return record


class Success(Res):
    def invert(self) -> 'Fail':
        self.__class__ = Fail
        return self


class Fail(Res):
    def invert(self) -> 'Success':
        self.__class__ = Success
        return self


Echo = TypeVar('Echo', Success, Fail, 'NO')


def make_gen(target, num: tuple) -> Callable:  # -> fa
    if isinstance(target, Iterable):
        def gen(epoch: int, op: int, table: dict, log: bool) -> Iterable[Success, Fail, str]:
            table = table.copy()
            ed = op
            table['$prev_str'] = ''
            for expect in target:
                recv = yield 'GO'
                if log:
                    table['$prev_str'] += recv
                if recv == expect:
                    ed += 1
                else:
                    yield Fail(epoch, ed, table)
            yield Success(epoch, ed, table)
            yield 'NO'
    elif isinstance(target, Callable):
        def gen(epoch: int, op: int, table: dict, log: bool):
            table = table.copy()
            recv = yield 'GO'
            table['$prev_str'] = recv if log else ''
            if target(recv, (epoch, op, table)):
                yield Success(epoch, op + 1, table)
            else:
                yield Fail(epoch, op + 1, table)
            yield 'NO'
    else:
        raise Exception

    if num == (1, 1):
        return gen
    else:
        def decorate_g(epoch: int, op: int, table: dict, log: bool):
            counter = 0
            from_num, to_num = num
            if isinstance(from_num, str):
                from_num = to_num = len(table.get(from_num, ()))
            elif isinstance(from_num, Callable):
                from_num, to_num = from_num(epoch, op, table), to_num(epoch, op, table)
            assert 0 <= from_num <= to_num
            curr_state = 'OPTION' if from_num == 0 else 'GO'
            if to_num == 0:
                yield curr_state

            inner_gen = gen(epoch, op, table, log)
            next(inner_gen)
            while counter < to_num:
                recv = yield curr_state
                echo = inner_gen.send(recv)
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


def str_n(num: tuple) -> str:
    from_num, to_num = num
    if isinstance(from_num, Callable):
        tpl = '<{}>'.format
        from_num, to_num = tpl(from_num.__name__), tpl(to_num.__name__)
    if from_num == to_num:
        if from_num == 1:
            return ''
        return '{' + str(from_num) + '}'
    else:
        return '{' + str(from_num) + ',' + str(to_num) + '}'


def explain_n(num: tuple, res: Res) -> tuple:
    epoch, op, table = res.epoch, res.ed, res.table
    from_num, to_num = num
    if isinstance(from_num, str):
        from_num = to_num = len(table.get(from_num, ()))
    elif isinstance(from_num, Callable):
        from_num, to_num = from_num(epoch, op, table), to_num(epoch, op, table)
    return from_num, to_num


class R:
    def __init__(self, target_rule, num=None, name: str = None):
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

    def auto_flip(self, echo):
        if self.invert and isinstance(echo, (Success, Fail)):
            echo = echo.invert()
        if isinstance(echo, Fail):
            echo = 'NO'
        return echo

    def broadcast(self, char):
        next_echo = None
        if self.next_r:
            next_echo = self.next_r.broadcast(char)

        seed_echo = []
        if self.is_matcher:
            state = {'GO': False, 'NO': False, 'Res': []}
            if self.fa_l:
                fa_l = []
                for fa in self.fa_l:
                    echo = self.auto_flip(fa.send(char))
                    if echo == 'GO':
                        state['GO'] = True
                        fa_l.append(fa)
                    elif isinstance(echo, Success):
                        state['Res'].append(echo)
                    elif echo == 'NO':
                        state['NO'] = True
                    else:
                        raise Exception
                self.fa_l = fa_l

            if state['Res']:
                seed_echo.extend(state['Res'])
                this_echo = state['Res']
            elif state['GO']:
                this_echo = 'GO'
            elif state['NO'] or not self.fa_l:
                this_echo = 'NO'
            else:
                raise Exception
        else:
            this_echo = self.target_rule.broadcast(char)
            if is_l(this_echo):
                filter_echo = []
                for res in this_echo:
                    from_num, to_num = explain_n(self.num, res)
                    if self.name and '_' + self.name not in res.table:
                        res.table['_' + self.name] = res.op

                    if '$nth' not in res.table:
                        res.table['$nth'] = 1
                    if res.table['$nth'] < to_num:
                        self.active(res)
                    if from_num <= res.table['$nth'] <= to_num:
                        res.table['$nth'] = 0
                        filter_echo.append(res)
                this_echo = filter_echo
                if this_echo:
                    seed_echo.extend(this_echo)

    def active(self, prev_res: Res, log=False, append=True) -> str:
        if self.is_matcher:
            fa = self.gen(prev_res.epoch, prev_res.ed, prev_res.table, log or bool(self.demand_r))
            echo = next(fa)
            if append:
                self.fa_l.append(fa)
        else:
            echo = self.target_rule.active(prev_res, bool(self.demand_r))
            if echo == 'GO':
                from_num, _ = self.num
                epoch, op, table = prev_res.epoch, prev_res.ed, prev_res.table
                if isinstance(from_num, str):
                    from_num = len(table.get(from_num, ()))
                elif isinstance(from_num, Callable):
                    from_num = from_num(epoch, op, table)
                if from_num == 0:
                    echo = 'OPTION'

        if self.xor_r:
            xor_echo = self.xor_r.active(prev_res, append=False)
            if xor_echo != echo:
                echo = 'OPTION'
        elif self.invert:
            if echo == 'GO':
                echo = 'OPTION'
            elif echo == 'OPTION':
                echo = 'GO'
            else:
                raise Exception
        else:
            if echo == 'OPTION' and self.demand_r:
                demand_echo = self.demand_r.active(prev_res, append=False)
                if demand_echo != 'OPTION':
                    echo = 'GO'
            for sibling in self.sibling_l:
                sibling_echo = sibling.active(prev_res, append=False)
                if sibling_echo == 'OPTION':
                    echo = 'OPTION'
        return echo

    def match(self, source: Iterable) -> list:
        res_l = []
        for i, char in enumerate(source):
            self.active(Res(i, i, {}))
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
        return matcher


class MatchStart:
    pass


class MatchEnd:
    pass
