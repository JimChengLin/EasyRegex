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
    pass


class Fail(Result):
    pass


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
                    elif counter == to_num:
                        yield echo
                    if counter < from_num:
                        echo = 'GO'
                curr_state = echo
            yield 'NO'

        return decorate_g


def is_l(obj) -> bool:
    return isinstance(obj, list)


def parse_n(num) -> tuple:
    if num is None:
        return 1, 1
