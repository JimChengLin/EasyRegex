from collections import OrderedDict

if False:
    # 仅用于类型检查
    from .Result import Result
    from .R import R

# {..., k: (share_l, share_iter)}
cache = OrderedDict()


def cache_clear():
    cache.clear()


def cache_deco(imatch):
    def memo_imatch(self: 'R', resource: str, prev_result: 'Result'):
        def tpl(result: 'Result'):
            return id(self), id(resource), str(result)

        k = tpl(prev_result)
        share_l, share_iter = cache.setdefault(k, ([], imatch(self, resource, prev_result)))
        cache.move_to_end(k)
        if len(cache) > 128:
            cache.popitem(last=False)

        yield from share_l
        while True:
            try:
                echo = next(share_iter)
            except StopIteration:
                break
            share_l.append(echo)
            yield echo

    return memo_imatch
