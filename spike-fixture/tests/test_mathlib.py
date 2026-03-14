from mathlib import add, multiply, is_positive


def test_add_positive():
    assert add(2, 3) == 5


def test_add_negative():
    assert add(-1, 1) == 0


def test_multiply():
    assert multiply(3, 4) == 12


def test_multiply_zero():
    assert multiply(5, 0) == 0


def test_is_positive():
    assert is_positive(1) is True
    assert is_positive(-1) is False
    assert is_positive(0) is False
