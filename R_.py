NULL = '\00'


class Result:
    def __init__(self, epoch: int, ed: int):
        self.epoch = epoch
        self.ed = ed
        self._table = None

    @property
    def table(self) -> dict:
        if self._table is None:
            self._table = {}
        return self._table

    @property
    def capture_record(self) -> dict:
        if self._table:
            record = {}
            for k in self._table:
                if k.startswith('@'):
                    record[k] = [(self._table.get(k[1:], i[0]), i[1]) for i in self._table[k]]
                    record[k] = list(map(lambda t: (self._table.get(k[1:], t[0]), t[1]), self._table[k]))
            return record

    def __eq__(self, other):
        if isinstance(other, Result):
            return self.epoch == other.epoch and self.ed == other.ed

    def __repr__(self):
        capture = ''
        if self._table:
            capture_record = {}
            for key in self._table:
                pass
