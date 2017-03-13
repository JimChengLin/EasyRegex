from collections import defaultdict

from R import r, Mode

input_str = '''
void PiXiuCtrl::init_prop() {
    Glob_Reinsert_Chunk = NULL;
    this->cbt.root = NULL;
    this->st.init_prop();
}

$gen range_0_j(int j) {
    "'\\"'"
    '"\\'"'
    //
    /*
     *
     */
    int j;
    j = 2;
    for (int i = 0; i < j; ++i) {
        $yield(i);
    }
}

void PiXiuCtrl::free_prop() {
    this->st.free_prop();
    this->cbt.free_prop();
}
'''


def make_default(d: dict):
    default_dict = defaultdict(lambda: (), d)
    return default_dict


def success_get_0(capture: dict):
    capture = make_default(capture)
    if len(capture[':}']) == len(capture[':{']) and len(capture[':)']) == len(capture[':(']):
        return 0
    return 1


sentinel = r('\0', success_get_0)

may_spaces = r(str.isspace, '*')
char = r(lambda char: True)
char_except_pair = r(lambda char: char not in '(){}')
may_chars_except_pair = char_except_pair.clone('*')

l_p = r('(', name=':(')
r_p = r(')', name=':)')
l_bracket = r('{', name=':{')
r_bracket = r('}', name=':}')

func_name = r(lambda char: str.isalpha(char) or str.isdigit(char) or char == '_', '+')
func_params = l_p @ may_chars_except_pair @ r_p

# body
string_0 = may_spaces @ (r('"') @ (r('\\"') | (~r('"'))).clone('*') @ r('"')).clone(name=':string')
string_1 = may_spaces @ (r("'") @ (r("\\'") | (~r("'"))).clone('*') @ r("'")).clone(name=':string')
string = string_0 | string_1

comment_0 = may_spaces @ (r('//') @ (~r('\n')).clone('*') @ r('\n')).clone(name=':comment')
comment_1 = may_spaces @ (r('/*') @ char.clone('*', mode=Mode.lazy) @ r('*/')).clone(name=':comment')
comment = comment_0 | comment_1

# code
declaration = None
code = char_except_pair | l_p | r_p | l_bracket | r_bracket

func_body = (string | comment | code).clone('*', mode=Mode.lazy)
# _body

# assemble
matcher = (
    r('$gen ') @ may_spaces
    @ func_name @ may_spaces  # range_0_j
    @ func_params @ may_spaces  # (int j)
    @ l_bracket @ may_spaces  # {
    @ func_body @ may_spaces
    @ r_bracket  # }
    @ sentinel
)

result = matcher.match(input_str)
print(result)
for i in result:
    print()
    print(input_str[i.op:i.ed])
