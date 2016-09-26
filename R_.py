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
        if self._table is not None:
            record = {}
            for k in self._table:
                if k.startswith('@'):  # capture记号
                    # OP可能存在于'_{k}'
                    record[k] = [(self._table.get('_' + k, i[0]), i[1]) for i in self._table[k]]
            return record

    def __eq__(self, other):
        if isinstance(other, Result):
            return self.epoch == other.epoch and self.ed == other.ed

    def __repr__(self):
        return 'FT({}, {})'.format(self.epoch, self.ed) + ('' if self._table is None else str(self.capture_record))
