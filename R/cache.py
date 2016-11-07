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
        k = (id(self), id(resource), '{}{}'.format(prev_result.ed, sorted(prev_result.capture.items())))
        share_l, share_iter = cache.setdefault(k, ([], imatch(self, resource, prev_result)))
        for echo in share_l:
            yield echo.clone(op=prev_result.ed)

        while True:
            try:
                echo = next(share_iter)
            except StopIteration:
                break
            share_l.append(echo)
            yield echo

    return memo_imatch
