from collections import defaultdict, ChainMap


class Result:
    '''
    用于记录一个字符串已匹配部分的开始和结束, 还有沿途捕获的组
    调用时要保持只读, 从而在状态机之间一层一层安全传递
    '''

    def __init__(self, op: int, ed: int, capture: dict = None):
        self.op = op
        self.ed = ed
        # {..., name: [... (op, ed)]}
        self.capture = capture if capture is not None else defaultdict(list)

    def __repr__(self):
        return 'Result({}, {}, {})'.format(self.op, self.ed, self.capture)

    def clone(self, **kwargs):
        return Result(**ChainMap(kwargs, self.__dict__))

    # 由于需要对结果取 XOR, NOT, 所以结果有两个状态 Success 和 Fail 态, 并可以互相转化
    def as_success(self):
        self.__class__ = Success
        return self

    def as_fail(self):
        self.__class__ = Fail
        return self


class Success(Result):
    '''
    Success 为真
    '''

    def __bool__(self):
        return True

    def invert(self):
        return self.as_fail()


class Fail(Result):
    '''
    Fail 为假
    '''

    def __bool__(self):
        return False

    def invert(self):
        return self.as_success()
