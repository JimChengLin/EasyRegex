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


class Fail(Result):
    pass


def make_gen(target, num: tuple) -> callable:
    # make -> gen -> fa
    if isinstance(target, str):
        def gen(epoch: int, op: int, table: dict):
            log = table.get('$log', False)
            ed = op
            prev_str = ''
            for expect_char in target:
                recv_char = yield 'GO'
                if log:
                    prev_str += recv_char
                if recv_char == expect_char:
                    ed += 1
                else:
                    yield Fail(epoch, ed, )
