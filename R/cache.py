if False:
    # 仅用于类型检查
    from .Result import Result
    from .R import R

# {..., k: (share_l, share_iter)}
cache = {}


def cache_clear():
    cache.clear()


def cache_deco(imatch):
    '''
    缓存 R 中 imatch 的修饰器
    '''

    def memo_imatch(self: 'R', resource: str, prev_result: 'Result'):
        def recursion_correct(result: 'Result'):
            result.op = max(result.op, prev_result.op)
            return result

        k = (id(self), prev_result.ed, prev_result.hash)
        share_l, share_iter = cache.setdefault(k, ([], imatch(self, resource, prev_result)))
        yield from map(lambda echo: recursion_correct(echo.clone(op=prev_result.ed)), share_l)

        while True:
            try:
                echo = next(share_iter)
            except StopIteration:
                break
            share_l.append(echo)
            yield recursion_correct(echo)

    return memo_imatch
