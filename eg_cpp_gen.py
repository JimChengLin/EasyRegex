from collections import defaultdict

from R import r, Mode

input_str = '''
void PiXiuCtrl::init_prop() {
    Glob_Reinsert_Chunk = NULL;
    this->cbt.root = NULL;
    this->st.init_prop();
}

async range_0_j(int j) {
    for (int i = 0; i < j; ++i) {
        yield(i)
    }
}

void PiXiuCtrl::free_prop() {
    this->st.free_prop();
    this->cbt.free_prop();
}
'''


def mk_default(d: dict):
    default_dict = defaultdict(lambda: (), d)
    return default_dict


def success_get_0(capture: dict):
    capture = mk_default(capture)
    if len(capture[':}']) == len(capture[':{']) and len(capture[':)']) == len(capture[':(']):
        return 0
    return 1


maybe_spaces = r(' ', '*')
func_name = r(lambda char: str.isalpha(char) or str.isdigit(char) or char == '_', '+')

left_p_mark = r('(', name=':(')
right_p_mark = r(')', name=':)')

char_except_pair = r(lambda char: char not in '(){}')
maybe_chars_except_pair = char_except_pair.clone('*')

left_b_mark = r('{', name=':{')
right_b_mark = r('}', name=':}')
sentinel = r('\0', success_get_0)

# --- func
func_body = (char_except_pair | left_p_mark | right_p_mark | left_b_mark | right_b_mark).clone('+', mode=Mode.lazy)
# ---

matcher = (
    r('async') @ maybe_spaces
    @ func_name @ maybe_spaces  # range_0_j
    @ left_p_mark @ maybe_chars_except_pair @ right_p_mark @ maybe_spaces  # (int j)
    @ left_b_mark @ maybe_spaces  # {
    @ func_body
    @ right_b_mark
    @ sentinel
)

result = matcher.match(input_str)
print(result)
for i in result:
    print(input_str[i.op:i.ed])
