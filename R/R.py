from copy import copy
from enum import Enum
from typing import Callable

from .Result import Result, Success, Fail
from .util import parse_n, make_gen, str_n, explain_n


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

    # --- basic ---
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
            s = '%{}%'.format(self.target.__name__)
        else:
            s = str(self.target)
        s = '({}{})'.format(s, str_n(self.num_t))

        if self.and_r:
            s = '({}&{})'.format(s, self.and_r)
        elif self.or_r:
            s = '({}|{})'.format(s, self.or_r)
        elif self.invert:
            s = '(~{})'.format(s)
        elif self.xor_r:
            s = '({}^{})'.format(s, self.xor_r)

        if self.next_r:
            s += str(self.next_r)
        return s

    def clone(self, **kwargs):
        this = copy(self)
        for k, v in kwargs.items():
            setattr(this, k, v)
        return this

    # --- core ---
    def imatch(self, resource: str, prev_result: Result):
        '''
        imatch 接受两个参数, 匹配的字符串(resource), 上一个状态机生成的结果(prev_result)
        返回一个 iter, yield 所有可能结果

        字符串匹配可以看成图论, imatch 就像节点用 stream 或者说 pipe 连接
        '''
        # 约定: from_num 和 to_num 在匹配开始时就已经完全确定
        from_num, to_num = explain_n(prev_result, self.num_t)

        if self.gen:
            # 已递归到最里层
            # 定义一个 iter, yield 有效数量区间内所有成功结果, 直到一个失败结果(包含)或字符串耗尽
            def stream_fab():
                if from_num == 0:
                    # 可选匹配
                    yield prev_result  # 必然成功态, 无需转换
                if to_num == 0:
                    # 不会匹配到更多
                    return

                counter = 0
                fa = self.gen(prev_result)
                for char in resource[prev_result.ed:]:
                    echo = fa.send(char)

                    if echo == 'GO':
                        continue
                    elif isinstance(echo, Success):
                        counter += 1
                        if from_num <= counter <= to_num:
                            yield echo
                        if counter < to_num:
                            # 未到达边界, 更新 fa
                            fa = self.gen(echo)
                        else:
                            return
                    elif isinstance(echo, Fail):
                        yield echo
                        return

        else:
            def stream_fab():
                # imatch 的 echo 只有可能是 Success 或者 Fail, 但可能有多个 echo
                if from_num == 0:
                    yield prev_result
                if to_num == 0:
                    return

                # 使用 2 个 queue 来 DFS
                q_a = [prev_result]
                q_b = []

                counter = 1
                while q_a and from_num <= counter <= to_num:
                    result = q_a.pop()
                    for echo in self.target.imatch(resource, result):
                        if echo:
                            q_b.append(echo)
                            yield echo
                        else:
                            yield echo
                            break
                    if not q_a:
                        counter += 1
                        q_a, q_b = q_b, q_a
        # num 关系处理完毕
        stream = stream_fab()

        if self.and_r:
            pass
        elif self.or_r:
            pass
        elif self.invert:
            pass
        elif self.xor_r:
            pass
