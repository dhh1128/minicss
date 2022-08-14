from getminu import _next_minu, _next_minu_cfg, _minu_matches, _get_ith_minu
try:
    import pytest
except:
    pass


def test_minu_matches():
    assert _minu_matches("a", "a")
    assert _minu_matches("a", "a")
    assert not _minu_matches("b", "a")
    assert _minu_matches("ab", "abc")
    assert _minu_matches("abc", "abc")
    assert _minu_matches("abc", "abc-xyz")
    assert _minu_matches("a-x", "abc-xyz")
    assert _minu_matches("abc-x", "abc-xyz")
    assert _minu_matches("a-xyz", "abc-xyz")
    assert _minu_matches("ab-xy", "abc-xyz")
    assert not _minu_matches("abcd-xy", "abc-xyz")
    assert not _minu_matches("a-b-xy", "abc-xyz")
    assert not _minu_matches("abc-xyz-", "abc-xyz")
    assert not _minu_matches("abc-xyz-pqr", "abc-xyz")


def test_next_minu_cfg():
    assert str([x for x in _next_minu_cfg([3, 1, 1])]) == \
           '[[1], [2], [1, 1], [3], [2, 1], [1, 1, 1], [3, 1], [2, 1, 1], [3, 1, 1]]'


def test_next_minu():
    assert ','.join([x for x in _next_minu("abc-d-e")]) == 'a,ab,a-d,abc,ab-d,a-d-e,abc-d,ab-d-e,abc-d-e'


def test_get_minu():
    tokens = [
        "abcd-efg",
        "abcd-efg-x",
        "abcd-efg-y",
        "abcd-pqr-de",
        "abcdm-pyx-de",
        "abcdn-zyx-de",
        "aw-ex-y",
        "abz-eqr-x",
        "abcd-efh",
        "ayz-efg"
    ]
    assert _get_ith_minu(tokens, 0) == "ab-efg"
    assert _get_ith_minu(tokens, 1) == "a-ef-x"
    assert _get_ith_minu(tokens, 2) == "ab-e-y"
    assert _get_ith_minu(tokens, 3) == "a-pq"
    assert _get_ith_minu(tokens, 4) == "a-py"
    assert _get_ith_minu(tokens, 5) == "a-z"
    assert _get_ith_minu(tokens, 6) == "aw"
    assert _get_ith_minu(tokens, 7) == "abz"
    assert _get_ith_minu(tokens, 8) == "a-efh"
    assert _get_ith_minu(tokens, 9) == "ay"


if __name__ == "__main__":
    test_get_minu()
