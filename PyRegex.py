match_pool = []
string = 'abexabbcsagvbafabcec'


# FA for 'abc'
def gen_abc(entry: int):
    out = entry
    in_char = yield
    if in_char == 'a':
        out += 1
        in_char = yield
        if in_char == 'b':
            out += 1
            in_char = yield
            if in_char == 'c':
                out += 1
                print('accept', entry, out)
                yield 'accept'
            else:
                yield 'fail'
        else:
            yield 'fail'
    else:
        yield 'fail'


# desire pattern for 'abc'
def gen_abc_1(entry: int):
    out = entry
    for expected in ('a', 'b', 'c'):
        in_char = yield
        if in_char == expected:
            out += 1
        else:
            yield 'fail'
    print('accept', entry, out)
    yield 'accept'


def make_gen(s: str):
    token_id = 'LYJ'

    def generator(entry: int):
        out = entry
        for expected in s:
            in_char = yield
            if in_char == expected:
                out += 1
            else:
                yield 'fail'
        print('accept', entry, out)
        print('for', token_id)
        yield 'accept'

    return generator


# FA for 'a|b|c'
def gen_a_b_c(entry: int):
    for char in ('a', 'b', 'c'):
        gen = make_gen(char)(entry)
        next(gen)
        match_pool.append(gen)
    yield
    yield 'fail'


# FA for 'ab+c' == 'abb*c'
def gen_a__b__c(op: int):
    ed = op

    # a
    in_char = yield
    if in_char == 'a':
        ed += 1
    else:
        yield 'fail'

    # b+ == bb*
    # b
    in_char = yield
    if in_char == 'b':
        ed += 1
    else:
        yield 'fail'

    # b*
    while True:
        in_char = yield
        if in_char == 'b':
            ed += 1
        else:
            break

    # c
    if in_char == 'c':
        ed += 1
    else:
        yield 'fail'

    print('accept', op, ed, string[op:ed])
    yield 'accept'


if __name__ == '__main__':
    _gen_abc = make_gen('abc')
    for i, char in enumerate(string):
        new_pool = []
        gen = gen_a__b__c(i)
        next(gen)
        match_pool.append(gen)
        for nfa in match_pool:
            echo = nfa.send(char)
            if echo not in ('accept', 'fail'):
                new_pool.append(nfa)
        match_pool[:] = new_pool
