# 理想
# 现在的正则表达式有一个严重的问题就是不严格区分识别的内容和修饰内容的数据
# 比如/[ab]*/, 内容ab和数量*是合并在一个str里的,这就造成了Debug的困难
# 我理想的API应该是类似M('ab').num('*'), M是Match的缩写
# 不同片段之间严格区分, 比如/.+abc/就应该是M('.').num('+') + M('abc')
# 以及, /a|b/就应该是M('a') | M('b')
# 分组捕获不再依靠顺序, 比如/(a)(b)/, 应当是M('a').as('A') + M('b').as('B')
# match之后的结果直接用类似get('A')的方式获取
# 理想状态下应该增加一个我曾经手写程序获取HTML标签元素使用到的计数器,比如<div><div></div></div>
# 结尾</div>的个数取决于之前<div>的个数
# 理想的写法应当是M('<div>').num_to('DIV_NUM')+M('</div>').num_from('DIV_NUM')
# 这样<div><div><div></div></div>


class M:
    def __init__(self):
        pass
