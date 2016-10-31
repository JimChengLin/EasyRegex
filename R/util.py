from math import inf
from typing import Callable

if False:
    # 仅用于类型检查
    from .Result import Result


def parse_n(num):
    '''
    将构造 R 时的 num 参数转化为统一的 tuple
    约定: 如果是 num 本身就是 tuple, 那么默认长度为 2 且内容类型相同
    '''
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
    raise TypeError


def str_n(num_t: tuple):
    '''
    将 parse_t 得到的 num_t 转化为字符串
    '''
    from_num, to_num = num_t
    if isinstance(from_num, Callable):
        tpl = '%{}%'.format
        from_num, to_num = tpl(from_num.__name__), tpl(to_num.__name__)

    if from_num == to_num:
        # {1, 1}无需显示
        if from_num == 1:
            return ''
        return '{' + str(from_num) + '}'
    else:
        return '{' + str(from_num) + ',' + str(to_num) + '}'


def explain_n(result: Result, num_t: tuple):
    '''
    如果 num 是由符号和函数定义的, 那么需要在运行时得到确定的 num_t
    '''
    from_num, to_num = num_t

    # 符号定义, 则查询捕获组
    if isinstance(from_num, str):
        from_num = len(result.capture.get(from_num, ()))
        to_num = len(result.capture.get(to_num, ()))

    # 函数定义, 传入捕获组
    elif isinstance(from_num, Callable):
        from_num = from_num(result.capture)
        to_num = to_num(result.capture)

    assert 0 <= from_num <= to_num
    return from_num, to_num


def make_gen(target):
    '''
    返回一个 generator 来抽象状态机
    generator 接受一个 Result 来实例化
    '''
    if isinstance(target, str):
        # 目标是 str, 则不断拿 send 来的 char 来比对目标中的 char
        def gen(prev_result: Result):
            curr_result = prev_result.clone()

            for expect_char in target:
                recv_char = yield 'GO'
                curr_result.ed += 1

                if recv_char != expect_char:
                    yield curr_result.as_fail()
            # 全匹配
            yield curr_result.as_success()

    elif isinstance(target, Callable):
        # 目标是函数, 以 recv_char 执行一次, 根据真假返回结果
        def gen(prev_result: Result):
            curr_result = prev_result.clone()
            recv_char = yield 'GO'
            curr_result.ed += 1

            if target(recv_char):
                yield curr_result.as_success()
            else:
                yield curr_result.as_fail()

    else:
        raise TypeError
    return gen
