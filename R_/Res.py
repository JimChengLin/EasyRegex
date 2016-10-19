from collections import ChainMap, defaultdict


class Res:
    def __init__(self, epoch, op, ed=None, capture=None):
        self.epoch = epoch
        self.op = op
        self.ed = ed if ed is not None else op
        self.capture = capture if capture is not None else defaultdict(list)

    def __repr__(self):
        return 'Res({}, {}){}'.format(self.epoch, self.ed, self.capture or '')

    def clone(self, **kwargs):
        return Res(**ChainMap(kwargs, self.__dict__))

    def as_success(self):
        self.__class__ = Success
        return self

    def as_fail(self):
        self.__class__ = Fail
        return self

    def to_param(self):
        return self.epoch, self.ed, self.capture


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
