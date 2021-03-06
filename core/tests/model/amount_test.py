# Copyright 2019 Virgil Dupras
#
# This software is licensed under the "GPLv3" License as described in the "LICENSE" file,
# which should be included with this package. The terms are also available at
# http://www.gnu.org/licenses/gpl-3.0.html

from pytest import raises
from ..testutil import eq_

from ...model._ccore import amount_format
from ..base import Amount


# --- Amount
def test_add():
    # Amounts can be added together, given that their currencies are the same.
    eq_(Amount(1, 'CAD') + Amount(2, 'CAD'), Amount(3, 'CAD'))
    with raises(ValueError):
        Amount(1, 'CAD') + Amount(2, 'USD')

def test_add_other_types():
    # You can't add something else to an amount and vice-versa.
    with raises(TypeError):
        Amount(1, 'CAD') + 2
    with raises(TypeError):
        1 + Amount(2, 'CAD')

def test_add_zero():
    # It's possible to add 0 to an amount.
    eq_(Amount(1, 'CAD') + 0, Amount(1, 'CAD'))
    eq_(0 + Amount(2, 'CAD'), Amount(2, 'CAD'))
    eq_(Amount(1, 'CAD') + Amount(0, 'USD'), Amount(1, 'CAD'))
    eq_(Amount(0, 'USD') + Amount(2, 'CAD'), Amount(2, 'CAD'))

def test_cmp():
    # Amounts support inequalities with other amounts with the same currency.
    assert Amount(10, 'CAD') > Amount(9, 'CAD')
    assert Amount(10, 'CAD') >= Amount(9, 'CAD')
    assert not Amount(10, 'CAD') < Amount(9, 'CAD')
    assert not Amount(10, 'CAD') <= Amount(9, 'CAD')

def test_cmp_with_zero():
    # Amounts are comparable to zero, but not any other number.
    assert Amount(42, 'CAD') > 0
    with raises(TypeError):
        Amount(0, 'CAD') > 42
    assert Amount(42, 'CAD') >= 0
    with raises(TypeError):
        Amount(0, 'CAD') >= 42
    assert not Amount(42, 'CAD') < 0
    with raises(TypeError):
        Amount(0, 'CAD') < 42
    assert not Amount(42, 'CAD') <= 0
    with raises(TypeError):
        Amount(0, 'CAD') <= 42

def test_div_with_amount():
    # Amounts can be divided by other amounts if they all amounts share the same currency. That
    # yields a plain number.
    eq_(Amount(1, 'CAD') / Amount(2, 'CAD'), 0.5)
    with raises(ValueError):
        Amount(1, 'CAD') / Amount(2, 'USD')

def test_div_with_number():
    # Amounts can be divided by a number, yielding an amount.
    eq_(Amount(10, 'CAD') / 2, Amount(5, 'CAD'))
    eq_(Amount(3, 'CAD') / 1.5, Amount(2, 'CAD'))

def test_div_number_with_amount():
    # You can't divide a number with an amount.
    with raises(TypeError):
        10 / Amount(3, 'CAD')

def test_eq():
    # Amounts are equal if they have the same value and the same
    # currency. An amount with a value of zero is equal to 0. Any other
    # case yields non-equality.
    assert Amount(10, 'CAD') == Amount(10, 'CAD')
    assert not Amount(10, 'CAD') == Amount(11, 'CAD')
    assert not Amount(42, 'CAD') == Amount(42, 'USD')
    assert not Amount(10, 'CAD') != Amount(10, 'CAD')
    assert Amount(11, 'CAD') != Amount(10, 'CAD')
    assert Amount(42, 'CAD') != Amount(42, 'USD')

def test_eq_other_type():
    # An amount is not equal to any other type (except in the zero case).
    assert not Amount(10, 'CAD') == 'foobar'
    assert not Amount(0, 'CAD') == 'foobar'

def test_eq_zero():
    # An amount with a value of zero is equal to 0.
    assert Amount(0, 'CAD') == 0
    assert not Amount(0, 'CAD') == 42
    assert not Amount(42, 'CAD') == 0

def test_float():
    # It's possible to convert an Amount with currency to float.
    eq_(float(Amount(42, 'USD')), 42)

def test_immutable():
    # Amount is an immutable class (can't set currency).
    try:
        Amount(42, 'CAD').currency = 'foo'
    except AttributeError:
        pass # what should happen
    else:
        raise AssertionError("It shouldn't be possible to set an Amount's currency")

def test_mul_amount():
    # It doesn't make sense to multiply two amounts together.
    with raises(TypeError):
        Amount(2, 'CAD') * Amount(2, 'CAD')

def test_mul_number():
    # It's possible to multiply an amount by a number.
    eq_(Amount(2, 'CAD') * 2, Amount(4, 'CAD'))
    eq_(Amount(2, 'CAD') * 1.5, Amount(3, 'CAD'))
    eq_(1.5 * Amount(2, 'CAD'), Amount(3, 'CAD'))

def test_op():
    # Amount currency is preserved after an operation.
    eq_(-Amount(42, 'CAD'), Amount(-42, 'CAD'))
    eq_(abs(Amount(-42, 'CAD')), Amount(42, 'CAD'))
    # This one is to make sure that __abs__ is overriden. __abs__ only seems to be called when
    # the starting numeral is positive.
    eq_(abs(Amount(42, 'CAD')), Amount(42, 'CAD'))
    eq_(Amount(42, 'CAD') * 2, Amount(84, 'CAD'))
    eq_(Amount(42, 'CAD') / 2, Amount(21, 'CAD'))

def test_op_float():
    # As opposed to Decimal, Amount allows operations with floats.
    eq_(Amount(42, 'CAD') * 2.0, Amount(84, 'CAD'))
    eq_(Amount(42, 'CAD') / 2.0, Amount(21, 'CAD'))

def test_sub():
    # Amounts can be substracted one from another, given that their currencies are the same.
    eq_(Amount(10, 'CAD') - Amount(1, 'CAD'), Amount(9, 'CAD'))
    with raises(ValueError):
        Amount(10, 'CAD') - Amount(1, 'USD')

def test_sub_other_type():
    # You can't subtract something else from an amount and vice-versa.
    with raises(TypeError):
        Amount(10, 'CAD') - 1
    with raises(TypeError):
        10 - Amount(1, 'CAD')

def test_sub_zero():
    # It is possible to substract zero and from zero.
    eq_(Amount(2, 'CAD') - 0, Amount(2, 'CAD'))
    eq_(0 - Amount(22, 'CAD'), Amount(-22, 'CAD'))
    eq_(Amount(0, 'USD') - Amount(22, 'CAD'), Amount(-22, 'CAD'))
    eq_(Amount(2, 'CAD') - Amount(0, 'USD'), Amount(2, 'CAD'))

def test_hash():
    eq_(hash(Amount(2, 'CAD')), hash(Amount(2, 'CAD')))
    assert hash(Amount(2, 'CAD')) != hash(Amount(3, 'CAD'))
    assert hash(Amount(2, 'CAD')) != hash(Amount(2, 'USD'))

# --- Format amount
def test_format_default_currency():
    # If the amount currency matches default_currency, the currency is not shown.
    eq_(amount_format(Amount(12.34, 'CAD'), default_currency='CAD'), '12.34')
    eq_(amount_format(Amount(12.34, 'CAD'), default_currency='USD'), 'CAD 12.34')

def test_format_none():
    # When None is given, return ''.
    eq_(amount_format(None), '')

def test_format_zero():
    # Zero is always shown without a currency, except if zero_currency is not None.
    eq_(amount_format(0), '0.00')
    eq_(amount_format(Amount(0, 'CAD')), '0.00')
    eq_(amount_format(Amount(0, 'USD'), default_currency='CAD'), '0.00')
    eq_(amount_format(0, default_currency='CAD', zero_currency='EUR'), 'EUR 0.00')
    eq_(amount_format(0, default_currency='EUR', zero_currency='EUR'), '0.00')
