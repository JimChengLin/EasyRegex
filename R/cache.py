from collections import OrderedDict

if False:
    # 仅用于类型检查
    from .Result import Result
    from .R import R


class LRUCache(OrderedDict):
    def __setitem__(self, k, v):
        if len(self) > 4096:
            self.popitem(last=False)
        super().__setitem__(k, v)

    def __getitem__(self, k):
        self.move_to_end(k)
        return super().__getitem__(k)


# {..., k: (offset, share_l, share_iter)}
cache = LRUCache()


def cache_clear():
    cache.clear()


def cache_deco(imatch):
    def memo_imatch(self: 'R', resource: str, prev_result: 'Result'):
        def tpl(val: 'Result'):
            return id(self), id(resource), str(val)

        k = tpl(prev_result)
        share_l, share_iter = cache.setdefault(k, ([], imatch(self, resource, prev_result)))
        yield from share_l

        while True:
            echo = next(share_iter)
            share_l.append(echo)
            yield echo

    return memo_imatch
