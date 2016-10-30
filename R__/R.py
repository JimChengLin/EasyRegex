from copy import copy
from enum import Enum
from typing import Callable

from Result import Result
from util import parse_n, make_gen, str_n


class Mode(Enum):
    '''
    贪心匹配 Mode.Greedy
    懒惰匹配 Mode.Lazy
    '''
    Greedy = 'G'
    Lazy = 'L'


class R:
    '''
    正则表达式解析引擎
    '''

    # --- basic
    def __init__(self, target, num=None, name: str = None, mode=Mode.Greedy):
        self.target = target
        self.num_t = parse_n(num)
        self.name = name
        self.mode = mode

        # 关系 property, 单个实例中互斥
        self.and_r = None
        self.or_r = None
        self.invert = False
        self.xor_r = None
        self.next_r = None

        # 状态机 generator
        self.gen = make_gen(target) if not isinstance(target, R) else None

    def __and__(self, other: 'R'):
        this = self.clone()
        this.and_r = other
        return R(this)

    def __or__(self, other: 'R'):
        this = self.clone()
        this.or_r = other
        return R(this)

    def __invert__(self):
        this = self.clone()
        this.invert = True
        return R(this)

    def __xor__(self, other: 'R'):
        this = self.clone()
        this.or_r = other
        return R(this)

    # @在 Python 中表示矩阵乘法, 非常近似于 next
    def __matmul__(self, other: 'R'):
        this = self.clone()
        this.next_r = other
        return R(this)

    def __repr__(self):
        if self.gen and isinstance(self.target, Callable):
            s = '${}$'.format(self.target.__name__)
        else:
            s = str(self.target)

        if self.and_r:
            s = '({}&{})'.format(s, self.and_r)
        elif self.or_r:
            s = '({}|{})'.format(s, self.or_r)
        elif self.invert:
            s = '(~{})'.format(s)
        elif self.xor_r:
            s = '({}^{})'.format(s, self.xor_r)
        else:
            s = '({})'.format(s)

        s += str_n(self.num_t)
        if self.next_r:
            s += str(self.next_r)
        return s

    def clone(self, **kwargs):
        this = copy(self)
        for k, v in kwargs.items():
            setattr(this, k, v)
        return this

    # --- core
    def imatch(self, resource: str, prev_result: Result):
        '''
        每个 imatch要做的工作都非常简单, 给定一个prev_result, 然后不断返回可能的结果
        这是一个iter, 概念类似 pipe
        先不考虑num
        '''
        if self.gen:
            fa = self.gen(prev_result)
            for i in resource[prev_result.ed:]:
                echo = fa.send(i)
                if 1:
                    pass

    def match(self):
        pass
