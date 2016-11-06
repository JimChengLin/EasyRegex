from copy import copy
from enum import Enum
from itertools import chain
from typing import Callable

from .Result import Result, Success, Fail
from .cache import cache_deco, cache_clear
from .util import parse_n, make_gen, str_n, explain_n


class Mode(Enum):
    '''
    贪心匹配 Mode.greedy
    懒惰匹配 Mode.lazy
    '''
    greedy = 'G'
    lazy = 'L'


class R:
    '''
    正则表达式引擎
    '''

    # --- basic ---
    def __init__(self, target, num=None, name: str = None, mode=Mode.greedy):
        self.target = target
        self.num_t = parse_n(num)
        self.name = name
        self.mode = mode

        # 逻辑关系单个实例中互斥
        self.and_r = None
        self.or_r = None
        self.invert = False
        self.xor_r = None
        self.next_r = None

        # 状态机
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
        this.xor_r = other
        return R(this)

    # @ 在 Python 中表示矩阵乘法, 非常近似于 next
    def __matmul__(self, other: 'R'):
        this = self.clone()
        this.next_r = other
        return R(this)

    def __repr__(self):
        if self.gen and isinstance(self.target, Callable):
            s = '%{}%'.format(self.target.__name__)
        else:
            s = str(self.target)
        num_str = str_n(self.num_t)
        if num_str:
            s = '({}{}{})'.format(s, num_str, '?' if self.mode is Mode.lazy else '')

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

    def clone(self, num=None, name: str = None, mode: Mode = None):
        this = copy(self)
        if num is not None:
            this.num_t = parse_n(num)
        if name:
            this.name = name
        if mode:
            this.mode = mode
        return this

    # --- core ---
    @cache_deco
    def imatch(self, resource: str, prev_result: Result):
        '''
        参数: 字符串(resource), 上一个状态机的结果(prev_result)
        返回 iter, 按模式 yield 所有结果

        正则匹配可以看成图论, imatch 就像节点用 stream 或者说 pipe 连接
        '''
        # 约定: from_num 和 to_num 在匹配开始时就已经确定
        from_num, to_num = explain_n(prev_result, self.num_t)

        def capture_add(echo: Result):
            '''
            在 capture 添加 echo, 用于捕获组
            '''
            if self.name and echo:
                group = echo.capture.get(self.name, ())
                prev_ed = group[-1][-1] if group else prev_result.ed
                echo.capture = {**echo.capture, self.name: [*group, (prev_ed, echo.ed)]}
            return echo

        if self.gen:
            # 已递归到最里层
            def stream4num():
                if from_num == 0:
                    # 可选匹配
                    yield prev_result
                if to_num == 0:
                    # 不会匹配到更多
                    return

                counter = 0
                fa = self.gen(prev_result)
                next(fa)
                for char in resource[prev_result.ed:]:
                    echo = fa.send(char)

                    if echo == 'GO':
                        continue
                    elif isinstance(echo, Success):
                        counter += 1
                        capture_add(echo)
                        if from_num <= counter <= to_num:
                            yield echo
                        if counter < to_num:
                            # 未到达边界, 置换 fa
                            fa = self.gen(echo)
                            next(fa)
                        else:
                            return
                    elif isinstance(echo, Fail):
                        yield echo
                        return

            stream4num = stream4num() if self.mode is Mode.lazy else reversed(tuple(stream4num()))
        else:
            def stream4num():
                if to_num == 0:
                    # 不能 return prev_result,
                    yield prev_result
                    return
                if self.mode is Mode.lazy and from_num == 0:
                    yield prev_result

                # DFS
                counter = 1
                curr_iter = (capture_add(echo) for echo in self.target.imatch(resource, prev_result))
                while counter < from_num:
                    counter += 1
                    curr_iter = (capture_add(echo) for echo in
                                 chain.from_iterable(self.target.imatch(resource, i) for i in curr_iter if i))

                def explode(seed, nth: int):
                    for echo in seed:
                        capture_add(echo)
                        if self.mode is Mode.lazy:
                            yield echo
                        if echo and nth < to_num:
                            yield from explode(self.imatch(resource, echo), nth + 1)
                        if self.mode is Mode.greedy:
                            yield echo

                yield from explode(curr_iter, counter)
                if self.mode is Mode.greedy and from_num == 0:
                    yield prev_result

            stream4num = stream4num()
            # 数量关系处理完毕

        if self.and_r:
            def stream4logic():
                for echo in stream4num:
                    if not echo:
                        yield echo
                    else:
                        echo.as_fail()
                        for and_echo in self.and_r.imatch(resource[prev_result.ed:echo.ed], Result(0, 0)):
                            if and_echo and and_echo.ed == echo.ed - prev_result.ed:
                                echo.as_success()
                                break
                        yield echo

        elif self.or_r:
            def stream4logic():
                yield from chain(stream4num, self.or_r.imatch(resource, prev_result))

        elif self.invert:
            def stream4logic():
                for echo in stream4num:
                    yield echo.invert()

        elif self.xor_r:
            def stream4logic():
                for echo in stream4num:
                    for xor_echo in self.xor_r.imatch(resource[prev_result.ed:echo.ed], Result(0, 0)):
                        if xor_echo and xor_echo.ed == echo.ed - prev_result.ed:
                            yield echo.as_fail() if echo else echo.as_success()
                            break
                    else:
                        yield echo

        else:
            def stream4logic():
                yield from stream4num
        # 逻辑关系处理完毕
        stream4logic = stream4logic()

        if self.next_r:
            yield from chain.from_iterable(self.next_r.imatch(resource, echo) for echo in filter(bool, stream4logic))
        else:
            yield from stream4logic

    def match(self, resource: str):
        output_l = []
        cursor = Result(0, 0)
        while cursor.ed < len(resource):
            for echo in self.imatch(resource, cursor):
                if echo:
                    output_l.append(echo)
                    op = max(echo.ed, cursor.ed + 1)
                    cursor = Result(op, op)
                    break
            else:
                cursor.op += 1
                cursor.ed += 1
        cache_clear()
        return output_l
