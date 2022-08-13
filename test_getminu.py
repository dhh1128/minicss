from getminu import *
import pytest


def test_get_naive_unique_prefix():
    values = ['abc', 'abd', 'afghi']
    assert get_naive_unique_prefix('abe', values) == 'ab'
    assert get_naive_unique_prefix('abexyz', values) == 'ab'
    assert get_naive_unique_prefix('x', values) == 'x'
    assert get_naive_unique_prefix('a', []) == 'a'
    with pytest.raises(Exception):
        get_naive_unique_prefix('afghijk', values)
    with pytest.raises(Exception):
        get_naive_unique_prefix('a', values)
    with pytest.raises(ValueError):
        get_naive_unique_prefix('', values)


def test_get_minu():
    data = [
        ("abcd-efg", "ab-efg"),
        ("abcd-efg-x", "a-e-x"),
        ("abcd-efg-y", "ab-e-y"),
        ("abcd-pqr-de", "a-pq"),
        ("abcdm-pyx-de", "a-py"),
        ("abcdn-zyx-de", "a-z"),
        ("aw-ex-y", "aw"),
        ("abz-eqr-x", "abz"),
        ("abcd-efh", "ab-efh"),
        ("ayz-efg", "ay")
    ]
    full_forms = [item[0] for item in data]
    expected_minu_forms = [item[1] for item in data]
    actual_minu_forms = get_all_minu(full_forms)
    bad = []
    for i in range(len(data)):
        if actual_minu_forms[i] != expected_minu_forms[i]:
            bad.append((i, actual_minu_forms[i]))
    if bad:
        print("\n".join(["for " + data[x[0]][0] + " expected " + data[x[0]][1]
                        + " but got " + x[1] for x in bad]))
        pytest.fail("Actual minu forms didn't match expected; pytest -s for details.")


if __name__ == "__main__":
    test_get_minu()