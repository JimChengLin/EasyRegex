# EasyRegex
一个符合程序员直觉的正则引擎

MIT协议发布

## 使用方法
拷贝 R 文件夹到程序的 root

依赖: Python 3.5+

```Python
from R import r

# 匹配'abc'
m = r('abc')
m.match('abcdabdabccc')
# >> [Result(0, 3, {}), Result(7, 10, {})]
# Result(0, 3, {}) 表示从位置0匹配到位置3, 捕获组为空

# 用 @ 连接 R 对象, 以匹配更长的字符串
m = r('abc') @ r('d') @ r('a') # 等价于 r('abcda')
m.match('abcdabdabccc')
# >> [Result(0, 5, {})]

# 函数作为匹配目标
m = r('1') @ r(str.isalpha) @ r('1')
m.match('a1a1')
# >> [Result(1, 4, {})]

# 带数量条件的匹配
m = r('b', '{1,2}') @ r('cd')
m = r('b', (1, 2)) @ r('cd') # 二者等价
m.match('bbcda')
# >> [Result(0, 4, {})]

from R import Mode

# 懒惰模式(默认贪婪模式)
m = r('ab') @ r('c', '*', Mode.lazy)
m = r('ab') @ r('c', (0, inf), Mode.lazy) # 二者等价
m.match('abcccc')
# >> [Result(0, 2, {})]

# 通配符
dot = r(lambda char: True)
m = r('a') @ dot.clone('*') @ r('a')
m = r('a') @ r(lambda char: True, '*') @ r('a') # 二者等价
m.match('123a123a123')
# >> [Result(3, 8, {})]

# 嵌套
m = r(r('a'), 5)
m = r('a', 5) # 二者等价
m.match('qaaaaaq')
# >> [Result(1, 6, {})]
m = r('q') @ r(r('a'), '+', Mode.lazy)
m = r('q') @ r('a', (1, inf), Mode.lazy) # 二者等价
m.match('qaaaaaa')
# >> [Result(0, 2, {})]

# AND
m = (r('abc') & r('abc')) @ r('d')
m.match('abcd')
# >> [Result(0, 4, {})]
startswith_abc = r('abc') @ dot.clone('*')
endswith_abc = dot.clone('*') @ r('abc')
m = startswith_abc & endswith_abc # 等价于标准正则的 abc.*abc
m.match('1abchhabc1')
# >> [Result(1, 9, {})]

# OR
m = (r('a') | r('b')) @ r('bc')
m.match('abcbbc')
# >> [Result(0, 3, {}), Result(3, 6, {})]

# NOT
digit = r(str.isdigit)
no_digit = ~digit # 非数字
m = no_digit.clone('+')
m.match('123yyyyy123')
# >> [Result(3, 8, {})]

# XOR
m = (r('ab') ^ r('ab')) @ r('c')
m.match('abc')
# >> []

# 带捕获组的匹配
m = r('b', '{1,2}', ':b') @ r('cd')
m.match('bbcda')
# >> [Result(0, 4, {':b': [(0, 1), (1, 2)]})]

# 捕获组影响数量条件
m = r('b', '+', ':b') @ r('cd', ':b')
# 含义: 贪婪匹配一或多个'b'并以':b'为名字存入捕获组
# 接下来需要'cd'的个数是名为':b'的捕获组的长度
m.match('bbcdcd')
# >> [Result(0, 6, {':b': [(0, 1), (1, 2)]})]

# 函数数量条件
m = r('a', name=':a') @ r('b',
    lambda capture: len(capture.get(':a',())) + 1)
# 含义: 匹配1个'a'并存入捕获组, 接下来'b'的个数是名为':a'的捕获组的长度加一

# 更多更详细的例子, 参见 git 中的 test.py 文件
```

## 进阶用法
以匹配嵌套DIV标签为例

```Python
div_head = r('<div', name=':head')
div_tail = r('</div>', name=':tail')
no_head_tail = ~(div_head | div_tail)

# 当捕获组内':head'和':tail'的长度相等时返回0, 否则为1
def stop_head_tail_equal(capture: dict):
    head_group = capture.get(':head', ())
    tail_group = capture.get(':tail', ())
    return 1 if not head_group or not tail_group or len(head_group) != len(tail_group) else 0

# '\0'是一个不可能存在的字符, 这里拿来当开关用
sentinel = r('\0', stop_head_tail_equal)

div = div_head @ r(div_head | div_tail | no_head_tail, '+') @ div_tail @ sentinel
# 含义: 不断匹配 DIV 头标签和尾标签, 直到二者数量相同
m.match('0<div>1<div>2</div>3</div>4')
# >> [Result(1, 26, {':head': [(1, 5), (5, 11)], ':tail': [(13, 19), (19, 26)]})]
# '0<div>1<div>2</div>3</div>4'[1:26] == '<div>1<div>2</div>3</div>'
```
