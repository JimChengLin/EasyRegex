from copy import copy
from pprint import pformat


class Result:
    '''
    记录字符串已匹配的开始和结束, 以及沿途捕获的组
    '''

    def __init__(self, op: int, ed: int, capture: dict = None):
        self.op = op
        self.ed = ed
        # {..., name: [... (op, ed)]}
        self._capture = capture if capture is not None else {}

        self._hash = 0
        self.update = True

    def __repr__(self):
        return 'Result({}, {}, {})'.format(self.op, self.ed, pformat(self.capture))

    @property
    def capture(self):
        return self._capture

    @capture.setter
    def capture(self, val: dict):
        self.update = True
        self._capture = val

    @property
    def hash(self):
        if self.update:
            self.update = False
            self._hash = str(sorted(self.capture.items()))
        return self._hash

    def clone(self, **kwargs):
        this = copy(self)
        for k, v in kwargs:
            setattr(this, k, v)
        return this

    # 由于需要对结果取 XOR, NOT, 所以有两个状态 Success 和 Fail, 并可以互相转化
    def as_success(self):
        self.__class__ = Success
        return self

    def as_fail(self):
        self.__class__ = Fail
        return self


class Success(Result):
    def invert(self):
        return self.as_fail()


class Fail(Result):
    def __bool__(self):
        return False

    def invert(self):
        return self.as_success()
