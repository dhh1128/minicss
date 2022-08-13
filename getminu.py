import re
import sys

not_in_table = 0
in_header_row = 1
in_divider_row = 2
in_table_content = 3

bad_format_err = "Format error. Expected very simple markdown consisting of one or more tables."

divider_row_pat = re.compile(r'--+(\s*\|\s*--+)+')
content_row_pat = re.compile(r'([-a-z]+)(?:\s*\|\s*[^|]+)+')


def load(fname):
    tokens = []
    with open(fname, 'rt') as f:
        lines = [l.strip() for l in f.readlines() if l.strip()]
    state = not_in_table
    for line in lines:
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
                tokens.append(m.group(1))
            else:
                raise Exception(bad_format_err)
        elif state == in_table_content:
            m = content_row_pat.match(line)
            if m:
                tokens.append(m.group(1))
            else:
                state = not_in_table


def tweak_case(token):
    j = 1
    while True:
        i = token.find('-', j)
        if i == -1:
            break
        token = token[:i + 1] + token[i + 1].upper() + token[i + 2:]


def get_naive_unique_prefix(word, words):
    if not word:
        raise ValueError("empty word")
    common_char_count = 0
    word_len = len(word)
    for w in words:
        if w != word:
            w_len = len(w)
            end = min(word_len, w_len)
            found_diff = False
            for i in range(end):
                if word[i] != w[i]:
                    found_diff = True
                    break
                if i + 1 > common_char_count:
                    common_char_count = i + 1
            if not found_diff:
                raise Exception("no unique prefix")
    if common_char_count == word_len:
        raise Exception("no unique prefix")
    return word[:max(common_char_count, 1)]


def get_prefix_set(words_in_token, indexes):
    x = []
    for i in range(len(words_in_token)):
        word = words_in_token[i]
        idx = indexes[i]
        if idx >= len(word):
            return None
        x.append(word[:idx + 1])
    return x


def increment_index_per_word(idx_per_word, len_per_word, last_incremented_idx, word_count):
    while True:
        to_increment = (last_incremented_idx + 1) % word_count
        if last_incremented_idx < word_count - 1:
            if idx_per_word[last_incremented_idx] > 0:
                idx_per_word[last_incremented_idx] -= 1
        if idx_per_word[to_increment] < len_per_word[to_increment]:
            idx_per_word[to_increment] += 1
            return to_increment
        else:
            last_incremented_idx += 1
            if last_incremented_idx == 0 and idx_per_word == len_per_word:
                raise Exception("overflow")


def get_best_with_same_word_count(words_in_tokens_with_same_wordcount, token_idx):
    """
    Given a set of tokens that all have N words, and one of those tokens T for which we're trying
    to find the minimally unique value, calculate the shortest form that is still unique, that
    still has N words, and that diverges as far to the left as possible.

    We do this by iterating over all possible alt forms of T until we find one that is unique.
    The order of our iteration is crucial. First we iterate over all alt forms that use only
    one character from each word. If that's not enough, we add a new character on the first
    (leftmost) word and check again. If that's not enough, we remove the extra character from
    the first word and instead add an extra character to the second word. This is the counter-
    intuitive step. *We are holding the length constant until we've tried the extra character
    in every word, rather than just appending more and more characters to the leftmost word.
    This is because we prefer shorter to longer MORE than we prefer characters to accumulate
    at the left.
    """
    this_tokens_words = words_in_tokens_with_same_wordcount[token_idx]
    word_count = len(this_tokens_words)
    len_per_word = [len(w) for w in this_tokens_words]
    idx_per_word = [0] * word_count
    last_incremented_idx = word_count - 1
    other_count = len(words_in_tokens_with_same_wordcount) - 1
    while True:
        different_count = 0
        combo = get_prefix_set(this_tokens_words, idx_per_word)
        for i in range(len(words_in_tokens_with_same_wordcount)):
            if i != token_idx:
                other_words = words_in_tokens_with_same_wordcount[i]
                other_combo = get_prefix_set(other_words, idx_per_word)
                # If we found a divergence between the token of interest and this one,
                # remove this one from those that are not unique yet.
                if combo != other_combo:
                    different_count += 1
        # If the current combo has diverged from every other token's combo, we've found something unique.
        if different_count == other_count:
            return combo
        last_incremented_idx = increment_index_per_word(idx_per_word, len_per_word, last_incremented_idx, word_count)


def truncated_matches(combo, other_words):
    for i in range(len(combo)):
        if not other_words[i].startswith(combo[i]):
            return False
    return True


def cut_redundant_suffixes(first_answer, words_in_tokens_with_same_wordcount, token_idx):
    shortest = first_answer
    while len(shortest) > 1:
        suffix = shortest[-1]
        if len(suffix) > 1:
            break
        shorter = shortest[:-1]
        for i in range(len(words_in_tokens_with_same_wordcount)):
            if i != token_idx:
                other_words = words_in_tokens_with_same_wordcount[i]
                if truncated_matches(shorter, other_words):
                    return shortest
        shortest = shorter
    return shortest


def get_minu(words_in_tokens_with_same_wordcount, token_idx):
    """
    Suppose we want to find the minimally unique repr for "abcd-pqr-de" within the token set:
    { "abcd-efg-x", "abcd-efg-y", "abcd-pqr-de", "abcdm-pyx-de", "abcdn-zyx-de" }. Then:

    words_in_tokens_with_same_wordcount = an array of arrays matching that token set (i.e.,
      the first array = ["abcde", "efg", "x"], and so forth)
    token_idx = 2

    The correct output is the value "a-pq". We calculate it in two steps:

    1. Find the shortest unique 3-word form ("a-pq-d" for the situation above).
    2. Check and realize we can optimize by dropping the '-d' suffix.
    """
    best = get_best_with_same_word_count(
        words_in_tokens_with_same_wordcount, token_idx)
    best = cut_redundant_suffixes(best, words_in_tokens_with_same_wordcount, token_idx)
    return '-'.join(best)


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
    abcd-efg-x   | a-e-x <-- the combo "a" + "e" + x is unique among 3-word tokens
    abcd-efg-y   | ab-e-y <-- need "b" to differentiate from 3*1-char version of next
    abcd-pqr-de  | a-pq <-- short form with 3rd word, a-pq-d, adds unnecessary redundancy
    abcdm-pyx-de | a-py <-- shorter and more intuitive than abcdm
    abcdn-zyx-de | a-z
    aw-ex-y      | aw
    abz-eqr-x    | abz
    abcd-efh     | ab-efh
    ayz-efg      | ay                    <

    The algorithm below is not optimized for speed or cleverness. We only run this code once in a great
    while, and we don't care how long it takes. Rather, it's optimized for the understanding of coders.
    """

    # First, convert tokens to sequences of words, so we're not constantly slicing and parsing tokens.
    tokens_as_words = [t.split('-') for t in tokens]
    # We want to group subsets of tokens according to how many words they contain, because this
    # makes analysis easier; it limits how many potential colliding tokens we need to consider for
    # any given token. Allocate an array to hold sets. Assume there won't e more than 8 different
    # sets (meaning no token will have more than 8 words). If this assumption is false, something
    # will blow up.
    sets_by_word_count = [None]*8
    for i in range(len(tokens_as_words)):
        t = tokens_as_words[i]
        wc_set_idx = len(t)
        this_set = sets_by_word_count[wc_set_idx]
        if not this_set:
            this_set = []
            sets_by_word_count[wc_set_idx] = this_set
        this_set.append((t, i))
    minu_list = [None] * len(tokens_as_words)
    # Now analyze all tokens with the same wordcount as a set over which uniqueness must be achieved.
    for this_set in sets_by_word_count:
        if this_set:
            list_of_token_words = [pair[0] for pair in this_set]
            indexes = [pair[1] for pair in this_set]
            for i in range(len(list_of_token_words)):
                minu_list[indexes[i]] = get_minu(list_of_token_words, i)
    return minu_list


if __name__ == '__main__':
    tokens = load(sys.argv[1])
    mins = get_all_minu(tokens)
