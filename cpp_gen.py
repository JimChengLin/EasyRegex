from collections import defaultdict

from R import r, Mode

input_str = '''
void PiXiuCtrl::init_prop() {
    Glob_Reinsert_Chunk = NULL;
    this->cbt.root = NULL;
    this->st.init_prop();
}

async range_0_j(int j) {
    "'\\"'"
    '"\\'"'
    //
    /*
     *
     */
    for (int i = 0; i < j; ++i) {
        yield(i)
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
any_char = r(lambda char: True)
may_spaces = r(str.isspace, '*')

char_except_pair = r(lambda char: char not in '(){}')
may_chars_except_pair = char_except_pair.clone('*')

left_p = r('(', name=':(')
right_p = r(')', name=':)')

left_b = r('{', name=':{')
right_b = r('}', name=':}')

func_name = r(lambda char: str.isalpha(char) or str.isdigit(char) or char == '_', '+')
func_params = left_p @ may_chars_except_pair @ right_p

# --- func body
string_0 = may_spaces @ (r('"') @ (r('\\"') | (~r('"'))).clone('*') @ r('"')).clone(name=':string')
string_1 = may_spaces @ (r("'") @ (r("\\'") | (~r("'"))).clone('*') @ r("'")).clone(name=':string')
string = string_0 | string_1

comment_0 = may_spaces @ (r('//') @ (~r('\n')).clone('*') @ r('\n')).clone(name=':comment')
comment_1 = may_spaces @ (r('/*') @ any_char.clone('*', mode=Mode.lazy) @ r('*/')).clone(name=':comment')
comment = comment_0 | comment_1

code = char_except_pair | left_p | right_p | left_b | right_b
func_body = (string | comment | code).clone('*', mode=Mode.lazy)
# ---

matcher = (
    r('async') @ may_spaces
    @ func_name @ may_spaces  # range_0_j
    @ func_params @ may_spaces  # (int j)
    @ left_b @ may_spaces  # {
    @ func_body @ may_spaces
    @ right_b  # }
    @ sentinel
)

result = matcher.match(input_str)
print(result)
for i in result:
    print(input_str[i.op:i.ed])
