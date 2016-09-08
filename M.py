from collections import namedtuple


class DONE:
    pass


Result = namedtuple('Result', ('op', 'ed', 'token'))

fa_l = []  # 不断吃饲料的状态机
seed_l = []  # 用于实例化状态机的生成器函数
delay_l = []  # 状态转移过程中生成的新状态机
result_l = []


def make_chars_fa(s: str):
    def fa(op: int, token: str = None):
        ed = op
        for expected in s:
            in_char = yield
            if in_char == expected:
                ed += 1
            else:
                yield DONE
        if op != ed:
            result_l.append(Result(op, ed, token))
        yield DONE

    return fa


def match(input_str: str):
    global fa_l
    for i, char in enumerate(input_str):
        new_fa_l = []
        for seed in seed_l:
            new_fa = seed(i)
            next(new_fa)
            fa_l.append(new_fa)
        fa_l.extend(delay_l)
        delay_l.clear()

        for fa in fa_l:
            echo = fa.send(char)
            if echo is not DONE:
                new_fa_l.append(fa)
        fa_l = new_fa_l


if __name__ == '__main__':
    if False:
        seed_l.append(make_chars_fa('abc'))
        match('abexabcsagvbafbecabc')
        print(result_l)


class M:
    counter = 0

    def __init__(self, target: str):
        self.token = M.counter
        M.counter += 1

    def compile(self):
        pass
