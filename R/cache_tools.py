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
        def tpl(res: 'Result'):
            return id(self), resource, str(res)

        k = tpl(prev_result)
        offset, share_l, share_iter = cache.get(k, (0, [], imatch(self, resource, prev_result)))

        if offset <= len(share_l) - 1:
            yield from share_l
            print('hit', len(share_l))

        while True:
            echo = next(share_iter)
            share_l.append(echo)
            yield echo

    return memo_imatch
