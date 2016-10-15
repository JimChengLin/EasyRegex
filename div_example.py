from R import R

# 用下划线alias R, 单纯为了减少视觉干扰
_ = R

# 每个R都是一个匹配器(状态机), 这是接受任何字符的匹配器
any_char = _(lambda char, args: True)  # 等价于标准正则中的"."

# R重载了and(&), or(|), xor(^), invert(~)4种操作, 用function call串联
# "_(any_char & ~_('>'), '*')"意为匹配零或多个不为">"的任意字符
open_div = _('<div')(_(any_char & ~_('>'), '*'), '>')  # div起始标签

# 名为"@open_div"存入符号表
open_div = _(open_div, name='@open_div')
# close_div类似
close_div = _('</div>', name='@close_div')

# 标签之间仅有3种情况
# 1. open_div
# 2. close_div
# 3. 不是open_div或close_div一部分的标签之间的字符
inner = open_div | close_div

# 匹配一个open_div,然后不断识别嵌套的open_div和close_div, 直到两者数量相等
div = open_div(_(inner, '*'), _(close_div, num='@open_div'))  # 完整div定义

t_source = '''
<div class="outer"><div class="inner"></div></div>
'''
print(len(t_source), div.match(t_source))
