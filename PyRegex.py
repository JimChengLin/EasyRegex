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


if __name__ == '__main__':
    string = 'ababcababc'
    match_pool = []
    for i, char in enumerate(string):
        new_pool = []
        gen = gen_abc(i)
        next(gen)
        match_pool.append(gen)
        for nfa in match_pool:
            echo = nfa.send(char)
            if echo not in ('accept', 'fail'):
                new_pool.append(nfa)
        match_pool[:] = new_pool
