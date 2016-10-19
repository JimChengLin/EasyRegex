from enum import Enum
from typing import Callable

from Util import parse_n, make_gen


class Mode(Enum):
    Greedy = 'G'
    Lazy = 'L'


class Rule:
    def __init__(self, target_rule, num=None, name=None, mode=Mode.Greedy):
        self.target_rule = target_rule
        self.num_t = parse_n(num)
        self.name = name
        self.mode = mode

        self.and_r = None
        self.or_r_l = []
        self.invert = False
        self.xor_r = None
        self.next_r = None
        self._is_caller = False

        if self.is_matcher:
            self.fa = None
            self.gen = make_gen(target_rule, self.num_t, name)

    @property
    def is_matcher(self):
        return not self.is_wrapper

    @property
    def is_wrapper(self):
        return isinstance(self.target_rule, Rule)

    @property
    def is_caller(self):
        return self._is_caller

    @is_caller.setter
    def is_caller(self, val):
        cursor = self
        while True:
            cursor._is_caller = val
            if cursor.is_wrapper:
                cursor = cursor.target_rule
            else:
                break

    def __and__(self, other):
        other = other.clone()
        self_clone = self.clone()
        if self_clone.or_r_l:
            cursor = self_clone = R(self_clone)
        else:
            cursor = self_clone
            while cursor.and_r is not None:
                cursor = cursor.and_r
        cursor.and_r = other
        return self_clone

    def __or__(self, other):
        other = other.clone()
        self_clone = self.clone()
        self_clone.or_r_l.append(other)
        return self_clone

    def __xor__(self, other):
        other = other.clone()
        self_clone = R(self.clone())
        self_clone.xor_r = other
        return R(self_clone)

    def __invert__(self):
        self_clone = R(self.clone())
        self_clone.invert = True
        return R(self_clone)

    def __matmul__(self, other):
        other = other.clone()
        self_clone = self.clone()
        self_clone.next_r = other
        return R(self_clone)

    def __repr__(self):
        if self.is_matcher and isinstance(self.target_rule, Callable):
            s = '%{}%'.format(self.target_rule.__name__)
        else:
            s = str(self.target_rule)

        if self.xor_r:
            s = '({}^{})'.format(s, self.xor_r)
        elif self.invert:
            s = '(~{})'.format(s)
        else:
            if self.and_r:
                s = '({}&{})'.format(s, self.and_r)
            if self.or_r_l:
                s = '({}|{})'.format(s, '|'.join(str(or_r) for or_r in self.or_r_l))

        num_s = str_n(self.num_t)
        if num_s:
            if len(s) > 1 and not (s.startswith('(') and s.endswith(')')):
                s = '({})'.format(s)
            s += num_s
        if self.next_r:
            s += str(self.next_r)
        return s

    def clone(self):
        pass
