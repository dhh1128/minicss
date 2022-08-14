import re

not_in_table = 0
in_header_row = 1
in_divider_row = 2
in_table_content = 3

bad_format_err = "Format error. Expected very simple markdown consisting of one or more tables."

divider_row_pat = re.compile(r'--+(\s*\|\s*--+){2}')
content_row_pat = re.compile(r'([-a-z]+)\s*\|([^|])*\|\s*(.*)')


def load(fname):
    parsed_lines = []
    with open(fname, 'rt') as f:
        lines = [l.rstrip() for l in f.readlines()]
    state = not_in_table
    i = 0
    for line in lines:
        parsed_lines.append([line,None])
        if state == not_in_table:
            if '|' in line:
                if divider_row_pat.match(line):
                    raise Exception(bad_format_err)
                state = in_header_row
        elif state == in_header_row:
            if divider_row_pat.match(line):
                state = in_divider_row
            else:
                raise Exception(bad_format_err)
        elif state == in_divider_row:
            if divider_row_pat.match(line):
                raise Exception(bad_format_err)
            m = content_row_pat.match(line)
            if m:
                state = in_table_content
                parsed_lines[-1][1] = m
            else:
                raise Exception(bad_format_err)
        elif state == in_table_content:
            m = content_row_pat.match(line)
            if m:
                parsed_lines[-1][1] = m
            else:
                state = not_in_table
        i += 1
    return parsed_lines


def _next_way_to_reach(total, counts):
    # This func is never called directly. We can safely assume
    # that it is always possible to reach total based on what's
    # in counts.

    # Suppose total = 3 and counts = [5, 2, 1]
    take = min(total, counts[0])
    for i in range(take, 0, -1):
        prefix = [i]
        remainder = total - i
        if remainder:
            if len(counts) > 1:
                for way in _next_way_to_reach(remainder, counts[1:]):
                    combo = prefix + way
                    yield combo
        else:
            yield prefix


def _next_minu_cfg(counts):
    for total in range(1, sum(counts) + 1):
        for way in _next_way_to_reach(total, counts):
            yield way


def _make_minu(words, cfg):
    minu = ""
    i = 0
    for char_count in cfg:
        prefix = words[i][:char_count]
        minu += prefix + "-"
        i += 1
    return minu[:-1]


def _next_minu(token):
    words = token.split('-')
    counts = [len(w) for w in words]
    for cfg in _next_minu_cfg(counts):
        yield _make_minu(words, cfg)


def _minu_matches(minu, token):
    assert minu
    assert token
    left_end = len(minu)
    right_end = len(token)
    left_i = 0
    right_i = 0
    while True:
        left_c = minu[left_i]
        if left_c == '-': # skip ahead on right
            right_i = token.find('-', right_i)
            if right_i == -1:
                return False
        right_c = token[right_i]
        if left_c != right_c:
            return False
        left_i += 1
        if left_i == left_end:
            return True
        right_i += 1
        if right_i == right_end:
            return False


def _find_match(tokens, minu, skip_idxs):
    for i in range(len(tokens)):
        if i not in skip_idxs:
            if _minu_matches(minu, tokens[i]):
                return i
    return -1


def _get_indexes_of_long_forms(short, tokens):
    short += '-'
    idxs = []
    for i in range(len(tokens)):
        if tokens[i].startswith(short):
            idxs.append(i)
    return idxs


def _get_ith_minu(tokens, i):
    token = tokens[i]
    words = token.split('-')
    counts = [len(w) for w in words]
    skip_idxs = [i] + _get_indexes_of_long_forms(token, tokens)
    for cfg in _next_minu_cfg(counts):
        minu = _make_minu(words, cfg)
        if _find_match(tokens, minu, skip_idxs) == -1:
            return minu
    return token


def to_camel(minu):
    words = minu.split('-')
    if len(words) > 1:
        words = [words[0]] + [x[0].upper() + x[1:] for x in words[1:]]
    return ''.join(words)


def get_all_minu(tokens):
    """
    For each token (string) in a list, get a shortened token that is minimally unique.

    This requires an algorithm that's a bit different from naive algorithms that calculate
    the smallest unique prefix. That's because CSS tokens are word-oriented and human-
    friendly. They consist of multiple words separated by hyphens. What we want is to pick
    the shortest sequence of abbreviated words that is unique and still recognizable to
    someone who knows CSS. So, for each token, we need the sequence of word prefixes that,
    IN COMBINATION, uniquely identifies the full value.

    A naive algorithm would do this:

    token        | minimally unique
    ------------ | ---
    abcd-efg     | <-- NO UNIQUE PREFIX!
    abcd-efg-x   | abcd-efg-x
    abcd-efg-y   | abcd-efg-y
    abcd-pqr-de  | abcd-pq
    abcdm-pyx-de | abcdm
    abcdn-zyx-de | abcdn
    aw-ex-y      | aw
    abz-eqr-x    | abz
    abcd-efh     | abcd-efh
    ayz-efg      | ay

    ... but what we want is this:

    token        | minimally unique
    ------------ | ---
    abcd-efg     | ab-efg <-- the combo "ab" + "efg" is unique among 2-word tokens
    abcd-efg-x   | a-ef-x <-- the combo "a" + "ef" + "x" is unique among 3-word tokens
    abcd-efg-y   | ab-e-y <-- need "b" to differentiate from 3*1-char version of next
    abcd-pqr-de  | a-pq <-- short form with 3rd word, a-pq-d, adds unnecessary redundancy
    abcdm-pyx-de | a-py <-- shorter and more intuitive than abcdm
    abcdn-zyx-de | a-z
    aw-ex-y      | aw
    abz-eqr-x    | abz
    abcd-efh     | a-efh
    ayz-efg      | ay

    The algorithm below is not optimized for speed or cleverness. We only run this code once in a great
    while, and we don't care how long it takes. Rather, it's optimized for the understanding of coders.
    """
    i = 0
    x = []
    for t in tokens:
        x.append(_get_ith_minu(tokens, i))
        i += 1
    return x


if __name__ == '__main__':
    print(to_camel("a-bc-def"))
    #import sys
    #parsed_lines = load(sys.argv[1])
    import os
    fname = os.path.join(os.path.dirname(os.path.abspath(__file__)), "property-names.md")
    parsed_lines = load(fname)
    tokens = [l[1].group(1) for l in parsed_lines if l[1]]
    minus = get_all_minu(tokens)
    i = 0
    for pl in parsed_lines:
        if pl[1]:
            minu = minus[i]
            camel = to_camel(minu)
            if camel != minu:
                minu = minu + ' or ' + camel
            print(tokens[i] + " | " + minu + ' | ' + pl[1].group(3))
            i += 1
        else:
            print(pl[0])
