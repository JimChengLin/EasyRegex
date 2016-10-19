from math import inf
from typing import Callable, Iterable

from Res import Success, Fail


def parse_n(num):
    if num is None:
        return 1, 1
    if isinstance(num, tuple):
        return num
    if isinstance(num, (int, Callable)):
        return num, num
    if isinstance(num, str):
        if num == '*':
            return 0, inf
        if num == '+':
            return 1, inf
        if num.startswith('@'):
            return num, num
        if num.startswith('{') and num.endswith('}'):
            num = tuple(map(int, num[1:-1].split(',')))
            if len(num) == 1:
                num *= 2
            return num
    raise Exception


def str_n(num_t):
    from_num, to_num = num_t
    if isinstance(from_num, Callable):
        tpl = '%{}%'.format
        from_num, to_num = tpl(from_num.__name__), tpl(to_num.__name__)
    if from_num == to_num:
        if from_num == 1:
            return ''
        return '{' + str(from_num) + '}'
    else:
        return '{' + str(from_num) + ',' + str(to_num) + '}'


def explain_n(res, num_t):
    from_num, to_num = num_t
    if isinstance(from_num, str):
        from_num = to_num = len(res.capture.get(from_num, ())), len(res.capture.get(to_num, ()))
    elif isinstance(from_num, Callable):
        param = res.to_param()
        from_num, to_num = from_num(*param), to_num(*param)
    assert 0 <= from_num <= to_num
    return from_num, to_num


def make_gen(target, num_t, name):
    if isinstance(target, Iterable):
        def gen(prev_res):
            res = prev_res.clone()
            for expect in target:
                recv = yield 'GO'
                res.ed += 1
                if recv != expect:
                    yield res.as_fail()
                    yield 'DONE'
            yield res.as_success()
            yield 'DONE'
    elif isinstance(target, Callable):
        def gen(prev_res):
            res = prev_res.clone()
            recv = yield 'GO'
            res.ed += 1
            if target(recv, res.to_param()):
                yield res.as_success()
            else:
                yield res.as_fail()
            yield 'DONE'
    else:
        raise Exception

    if num_t == (1, 1):
        return gen
    else:
        def num_gen(prev_res):
            from_num, to_num = explain_n(prev_res, num_t)
            curr_state = 'OPT' if from_num == 0 else 'GO'
            if to_num == 0:
                yield curr_state

            counter = 0
            inner_gen = gen(prev_res)
            next(inner_gen)
            while counter < to_num:
                recv = yield curr_state
                echo = inner_gen.send(recv)

                if isinstance(echo, Success):
                    counter += 1
                    if counter < to_num:
                        inner_gen = gen(
                            echo.clone(capture={**echo.capture, name: [*echo.capture[name], (echo.op, echo.ed)]})
                            if name and from_num <= counter else echo)
                        next(inner_gen)
                    if counter < from_num:
                        echo = 'GO'
                    if counter == to_num:
                        yield echo
                elif isinstance(echo, Fail):
                    yield echo
                    break
                curr_state = echo
            yield 'DONE'

        return num_gen
