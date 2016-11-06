if False:
    # 仅用于类型检查
    from .Result import Result
    from .R import R

# {..., k: (share_l, share_iter)}
pri_cache = {}
# {..., k: (pri_k, offset)}
sec_cache = {}


def cache_clear():
    pri_cache.clear()
    sec_cache.clear()


def cache_deco(imatch):
    '''
    一级缓存
    缓存 R 中 imatch 的修饰器
    '''

    def memo_imatch(self: 'R', resource: str, prev_result: 'Result'):
        def tpl(res: 'Result'):
            return id(self), id(resource), str(res)

        k = tpl(prev_result)
        share_l, share_iter = pri_cache.setdefault(k, ([], imatch(self, resource, prev_result)))
        yield from share_l

        while True:
            try:
                echo = next(share_iter)
            except StopIteration:
                break
            share_l.append(echo)
            yield echo

    return memo_imatch


def add_sec_cache(r: 'R', resource: str, prev_result: 'Result', curr_result: 'Result'):
    '''
    二级缓存有更多的入口点, 复用一级缓存
    '''

    def tpl(res: 'Result'):
        return id(r), id(resource), str(res)

    pri_k = tpl(prev_result)
    sec_k = tpl(curr_result)
    sec_cache[sec_k] = (pri_k, len(pri_cache[pri_k][0]))
