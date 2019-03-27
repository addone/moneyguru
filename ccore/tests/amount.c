#include <CUnit/CUnit.h>
#include "../amount.h"
#include "../currency.h"

static bool ap(Amount *dest, const char *s, const char *default_currency)
{
    return amount_parse(dest, s, default_currency, true, false, false);
}

static void eq(Amount *a, uint64_t val, const Currency *cur)
{
    CU_ASSERT_EQUAL(a->val, val);
    CU_ASSERT_PTR_EQUAL(a->currency, cur);
}

static void acheck(const char *s, const char *dc, uint64_t val, const Currency *cur)
{
    Amount a;
    CU_ASSERT_TRUE(ap(&a, s, cur->code));
    eq(&a, val, cur);
}

static void test_parse()
{
    Amount a;

    Currency *USD = currency_get("USD");
    Currency *CAD = currency_get("CAD");
    Currency *EUR = currency_get("EUR");

    // Simple amounts
    acheck("1 EUR", NULL, 100, EUR);
    acheck("1.23 CAD", NULL, 123, CAD);

    // commas are correctly parsed when used instead of a dot for decimal
    // separators.
    acheck("54,67", "USD", 5467, USD);

    // When a comma is used as a grouping separator, it doesn't prevent the
    // number from being read.
    acheck("1,454,67", "USD", 145467, USD);
    acheck("CAD 3,000.00", "USD", 300000, CAD);
    acheck("CAD 3 000.00", "USD", 300000, CAD);

    // Prefixing or suffixing the amount with a currency ISO code sets the
    // currency attr of the amount.
    acheck("42.12 eur", NULL, 4212, EUR);
    acheck("eur42.12", NULL, 4212, EUR);

    CU_ASSERT_FALSE(ap(&a, "42.12 foo", NULL));

    // If there is garbage in addition to the currency, the whole amount is
    // invalid.
    CU_ASSERT_FALSE(ap(&a, "42.12 cadalala", NULL));

    // Dividing an amount by another amount gives a float.
    acheck("1 / 2 CAD", NULL, 50, CAD);

    // Parse empty, zero
    acheck("", NULL, 0, NULL);
    acheck(" ", NULL, 0, NULL);
    acheck("0", NULL, 0, NULL);

    // Expressions
    acheck("18 + 24 CAD", NULL, 4200, CAD);
    acheck("56.23 - 13.99 USD", NULL, 4224, USD);
    acheck("21 * 4 / (1 + 1) EUR", NULL, 4200, EUR);

    // Amounts with garbage around them can still be parsed.
    acheck("$10.42", "USD", 1042, USD);
    acheck("foo10bar", "USD", 1000, USD);
    acheck("$.42", "USD", 42, USD);

    // invalid expr
    CU_ASSERT_FALSE(ap(&a, "asdf", NULL));
    CU_ASSERT_FALSE(ap(&a, "+-.", NULL));
    CU_ASSERT_FALSE(ap(&a, "()", NULL));
    CU_ASSERT_FALSE(ap(&a, "42/0", NULL));

    // an amount using quotes as grouping sep is correctly parsed.
    acheck("1'234.56", "USD", 123456, USD);

    // In the thousand sep regexp, I used \u00A0 which ended up being a mistake
    // because it somehow matched the '0' character which made '10000' be
    // parsed as 1000! I'm glad I caught this because it wasn't directly
    // tested.
    acheck("10000", "USD", 1000000, USD);

    // Parsing an amount prefixed by a zero does not result in it being
    // interpreted as an octal number.
    acheck("0200+0200 CAD", NULL, 40000, CAD);

    // A 0 after a dot dot not get misinterpreted as an octal prefix.
    acheck(".02 EUR", NULL, 2, EUR);

    // When auto_decimal_place is True, the decimal is automatically placed.
    CU_ASSERT_TRUE(amount_parse(&a, "1234", "USD", true, true, false));
    eq(&a, 1234, USD);

    // When the currency has a different exponent, the decimal is correctly
    // placed.  TND has 3 decimal places.
    Currency *JPY = currency_register("JPY", 3, 0, 0, 0, 0);
    Currency *TND = currency_register("TND", 0, 0, 0, 0, 0);
    CU_ASSERT_TRUE(amount_parse(&a, "1234", "TND", true, true, false));
    eq(&a, 1234, TND);
    CU_ASSERT_TRUE(amount_parse(&a, "1234", "JPY", true, true, false));
    eq(&a, 1234, JPY);

    // Parsing correctly occurs when the amount of numbers typed is below the
    // decimal places. TND has 3 decimal places.
    CU_ASSERT_TRUE(amount_parse(&a, "123", "TND", true, true, false));
    eq(&a, 123, TND);
    CU_ASSERT_TRUE(amount_parse(&a, "1", "TND", true, true, false));
    eq(&a, 1, TND);

    // Spaces are correctly trimmed when counting decimal places.
    CU_ASSERT_TRUE(amount_parse(&a, "1234 ", "USD", true, true, false));
    eq(&a, 1234, USD);

    // When there's an expression, the auto_decimal_place option is ignored
    CU_ASSERT_TRUE(amount_parse(&a, "2+3", "USD", true, true, false));
    eq(&a, 500, USD);

    // Thousand separators are correctly seen as such (in bug #336, it was
    // mistaken for a decimal sep).
    acheck("1,000", "USD", 100000, USD);

    // Expression with thousand sep
    acheck("1,000.00*1.1", "USD", 110000, USD);

    // Dinars have 3 decimal places, making them awkward to parse because for
    // "normal" currencies, we specifically look for 2 digits after the
    // separator to avoid confusion with thousand sep. For dinars, however, we
    // look for 3 digits adter the decimal sep. So yes, we are vulnerable to
    // confusion with the thousand sep, but well, there isn't much we can do
    // about that.
    Currency *BHD = currency_register("BHD", 3, 0, 0, 0, 0);
    acheck("1,000 BHD", NULL, 1000, BHD);
    // Moreover, with custom currencies, we might have currencies with even
    // bigger exponent.
    Currency *ABC = currency_register("ABC", 5, 0, 0, 0, 0);
    acheck("1.23456 abc", NULL, 123456, ABC);

    // Test that a negative amount is correctly parsed
    acheck("-12.34", "USD", -1234, USD);
    CU_ASSERT_TRUE(amount_parse(&a, "-12.34", "USD", false, false, false));
    eq(&a, -1234, USD);

    // Test that a negative amount denoted with parenthesis
    // is parsed correctly
    CU_ASSERT_TRUE(amount_parse(&a, "(12.34)", "USD", false, false, false));
    eq(&a, -1234, USD);
    CU_ASSERT_TRUE(amount_parse(&a, "$(12.34)", "USD", false, false, false));
    eq(&a, -1234, USD);
    CU_ASSERT_TRUE(amount_parse(&a, "-(12.34)", "USD", false, false, false));
    eq(&a, -1234, USD);

    // dot ambiguity. ref #379
    acheck("USD 1000*1.055", NULL, 105500, USD);
    // first dot should be considered a thousand sep
    acheck("USD 1.000*1.055", NULL, 105500, USD);

    // With the strict_currency flag enabled, we return false on unsupported
    // currencies, even with a default_currency.
    CU_ASSERT_TRUE(amount_parse(&a, "42", "USD", true, false, true));
    eq(&a, 4200, USD);
    CU_ASSERT_FALSE(amount_parse(&a, "ZZZ 42", "USD", true, false, true));
}

static void test_format()
{
    char buf[128] = {0};
    Currency *USD = currency_get("USD");
    Currency *CAD = currency_get("CAD");
    Amount a;

    amount_configure('.', ',');
    // The normal behavior is to show the amount and the currency.
    amount_set(&a, 3300, USD);
    amount_format(buf, &a, true, false);
    CU_ASSERT_STRING_EQUAL(buf, "USD 33.00");

    // When blank_zero is True, 0 is rendered as an empty string.
    amount_set(&a, 0, NULL);
    amount_format(buf, &a, true, true);
    CU_ASSERT_STRING_EQUAL(buf, "");
    a.currency = CAD;
    amount_format(buf, &a, true, true);
    CU_ASSERT_STRING_EQUAL(buf, "");
    a.val = 1200;
    amount_format(buf, &a, true, true);
    CU_ASSERT_STRING_EQUAL(buf, "CAD 12.00");

    // It's possible to specify an alternate decimal separator
    amount_configure(',', ' ');
    a.val = 1234;
    amount_format(buf, &a, false, false);
    CU_ASSERT_STRING_EQUAL(buf, "12,34");

    // Previously, there was a bug causing comma to be placed everywhere
    amount_configure(',', '.');
    a.val = 123499;
    amount_format(buf, &a, false, false);
    CU_ASSERT_STRING_EQUAL(buf, "1.234,99");

    // Grouping sep
    amount_configure('.', ' ');
    a.val = 1299;
    amount_format(buf, &a, false, false);
    CU_ASSERT_STRING_EQUAL(buf, "12.99");
    a.val = 123499;
    amount_format(buf, &a, false, false);
    CU_ASSERT_STRING_EQUAL(buf, "1 234.99");
    a.val = 123456799;
    amount_format(buf, &a, false, false);
    CU_ASSERT_STRING_EQUAL(buf, "1 234 567.99");
    a.val = 123456789099;
    amount_format(buf, &a, false, false);
    CU_ASSERT_STRING_EQUAL(buf, "1 234 567 890.99");
    a.val = 2306044;
    amount_format(buf, &a, false, false);
    CU_ASSERT_STRING_EQUAL(buf, "23 060.44");

    // Grouping separation ignore the negative sign
    a.val = -12345;
    amount_format(buf, &a, false, false);
    CU_ASSERT_STRING_EQUAL(buf, "-123.45");

    // We can show zero with a currency
    a.val = 0;
    amount_format(buf, &a, true, false);
    CU_ASSERT_STRING_EQUAL(buf, "CAD 0.00");

    // Currency exponents are properly considered
    Currency *JPY = currency_register("JPY", 3, 0, 0, 0, 0);
    amount_set(&a, 12345, JPY);
    amount_format(buf, &a, true, false);
    CU_ASSERT_STRING_EQUAL(buf, "JPY 12.345");
}

void test_amount_init()
{
    CU_pSuite s;

    s = CU_add_suite("Amount", NULL, NULL);
    CU_ADD_TEST(s, test_parse);
    CU_ADD_TEST(s, test_format);
}

