from collections import OrderedDict
from functools import wraps

if False:
    # 仅用于类型检查
    from .Result import Result
    from .R import R

MAX_LEN = 4096


class LRUCache(OrderedDict):
    def __setitem__(self, k, v):
        if len(self) > MAX_LEN:
            self.popitem(last=False)
        super().__setitem__(k, v)

    def __getitem__(self, k):
        self.move_to_end(k)
        return super().__getitem__(k)


cache = LRUCache()


def cache_clear():
    cache.clear()


def cache_deco(func):
    '''
    缓存 R 中 imatch
    '''

    @wraps(func)
    def cache_imatch(self: 'R', resource: str, prev_result: 'Result'):
        pass

    return func
