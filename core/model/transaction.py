# Copyright 2018 Virgil Dupras
#
# This software is licensed under the "GPLv3" License as described in the "LICENSE" file,
# which should be included with this package. The terms are also available at
# http://www.gnu.org/licenses/gpl-3.0.html

import time
import datetime

from core.util import allsame, first

from ..const import NOEDIT
from .amount import parse_amount, convert_amount, of_currency
from ._ccore import Split, Transaction as TransactionBase

class Transaction(TransactionBase):
    """A movement of money between two or more accounts at a specific date.

    Money movements that a transaction implies are listed in :attr:`splits`. The splits of a
    transaction *always balance*, which means that the sum of amounts in its splits is always zero.

    Whenever a potentially unbalancing operation is made on the splits, call :meth:`balance` to
    balance the transaction out.

    Initialization arguments are mostly just directly assigned to their relevant attributes in the
    transaction, except for ``account`` and ``amount`` (there is no such attributes). If specified,
    we initialize what would otherwise be an empty split list with two splits: One adding ``amount``
    to ``account``, and the other adding ``-amount`` to ``None`` (an unassigned split).
    """

    TYPE = 1 # Used in CCore

    def __init__(self, date, description=None, payee=None, checkno=None, account=None, amount=None):
        TransactionBase.__init__(
            self, self.TYPE, date, description, payee, checkno, account, amount)

    def __repr__(self):
        return '<%s %r %r>' % (self.__class__.__name__, self.date, self.description)

    def __deepcopy__(self, *args, **kwargs):
        res = Transaction(self.date)
        res.copy_from(self)
        return res

    def amount_for_account(self, account, currency):
        """Returns the total sum attributed to ``account``.

        All amounts are converted to ``currency`` before doing the sum. This is needed because we
        might have amounts with different currencies here.

        :param account: :class:`.Account`
        :Param currency: :class:`.Currency`

        .. seealso:: :func:`.convert_amount`
        """
        splits = (s for s in self.splits if s.account == account)
        return sum(convert_amount(s.amount, currency, self.date) for s in splits)

    def affected_accounts(self):
        """Returns a set of all accounts affected by self.

        ... meaning all accounts references by our :attr:`splits`.
        """
        return set(s.account for s in self.splits if s.account is not None)

    def assign_imbalance(self, target_split):
        """Assigns remaining imbalance to the selected split.

        If the ``target_split`` is not an assigned split, does nothing.
        """
        if target_split.account is None:
            return
        unassigned = [
            split for split in self.splits
            if split.account is None and split.amount
        ]
        if not unassigned:
            return
        if target_split.amount:
            target_currency = target_split.amount.currency_code
        else:
            # Use whatever is the currency of the first split to show up
            target_currency = unassigned[0].amount.currency_code
        unassigned = [split for split in unassigned if split.amount.currency_code == target_currency]
        amount = sum(split.amount for split in unassigned)
        target_split.amount += amount
        for split in unassigned:
            self.remove_split(split)

    def change(
            self, date=NOEDIT, description=NOEDIT, payee=NOEDIT, checkno=NOEDIT, from_=NOEDIT,
            to=NOEDIT, amount=NOEDIT, currency=NOEDIT, notes=NOEDIT):
        """Changes our transaction and do all proper stuff.

        Sets all specified arguments to their specified values and do proper adjustments, such as
        making sure that our :attr:`Split.reconciliation_date` still make sense and updates our
        :attr:`mtime`.

        Moreover, it offers a convenient interface to specify a two-way transaction with ``from_``,
        ``to`` and ``amount``. When those are set, we'll set up splits corresponding to this two-way
        money movement.

        If ``currency`` is set, it changes the currency of the amounts in all :attr:`splits`,
        without conversion with exchange rates. Amounts are kept intact.

        :param date: ``datetime.date``
        :param description: ``str``
        :param payee: ``str``
        :param checkno: ``str``
        :param from_: :class:`.Account`
        :param to: :class:`.Account`
        :param amount: :class:`.Amount`
        :param currency: :class:`.Currency`
        :param notes: ``str``
        """
        # from_ and to are Account instances
        if date is not NOEDIT:
            # If reconciliation dates were equal to txn date, make it follow
            for split in self.splits:
                if split.reconciliation_date == self.date:
                    split.reconciliation_date = date
            # If the new date is in the future, we de-reconcile the splits
            if date > datetime.date.today():
                for split in self.splits:
                    split.reconciliation_date = None
            self.date = date
        if description is not NOEDIT:
            self.description = description
        if payee is not NOEDIT:
            self.payee = payee
        if checkno is not NOEDIT:
            self.checkno = checkno
        if notes is not NOEDIT:
            self.notes = notes
        # the amount field has to be set first so that splitted_splits() is not confused by splits
        # with no amount.
        if (amount is not NOEDIT) and self.can_set_amount:
            self.amount = abs(amount)
        if from_ is not NOEDIT:
            fsplits, _ = self.splitted_splits()
            if len(fsplits) == 1:
                fsplit = fsplits[0]
                fsplit.account = from_
        if to is not NOEDIT:
            _, tsplits = self.splitted_splits()
            if len(tsplits) == 1:
                tsplit = tsplits[0]
                tsplit.account = to
        if currency is not NOEDIT:
            tochange = (s for s in self.splits if s.amount and s.amount.currency_code != currency)
            for split in tochange:
                split.amount = parse_amount('{} {}'.format(float(split.amount), currency))
                split.reconciliation_date = None
        # Reconciliation can never be lower than txn date
        for split in self.splits:
            if split.reconciliation_date is not None:
                split.reconciliation_date = max(split.reconciliation_date, self.date)
        self.mtime = time.time()

    def matches(self, query):
        """Return whether ``self`` is matching ``query``.

        ``query`` is a ``dict`` of all criteria to look for (example: ``{'payee': 'Barber shop'}``.
        List of possible dict keys:

        * description
        * payee
        * checkno
        * memo
        * amount
        * account
        * group

        All of these queries are string-based, except ``amount``, which requires an
        :class:`.Amount`.

        Returns true if any criteria matches, false otherwise.
        """
        query_description = query.get('description')
        if query_description is not None:
            if query_description in self.description.lower():
                return True
        query_payee = query.get('payee')
        if query_payee is not None:
            if query_payee in self.payee.lower():
                return True
        query_checkno = query.get('checkno')
        if query_checkno is not None:
            if query_checkno == self.checkno.lower():
                return True
        query_memo = query.get('memo')
        if query_memo is not None:
            for split in self.splits:
                if query_memo in split.memo.lower():
                    return True
        query_amount = query.get('amount')
        if query_amount is not None:
            query_value = float(query_amount) if query_amount else 0
            for split in self.splits:
                split_value = float(split.amount) if split.amount else 0
                if query_value == abs(split_value):
                    return True
        query_account = query.get('account')
        if query_account is not None:
            for split in self.splits:
                if split.account and split.account.name.lower() in query_account:
                    return True
        query_group = query.get('group')
        if query_group is not None:
            for split in self.splits:
                if split.account and split.account.groupname and \
                        split.account.groupname.lower() in query_group:
                    return True
        return False

    def mct_balance(self, new_split_currency):
        """Balances a :ref:`multi-currency transaction <multi-currency-txn>` using exchange rates.

        *This balancing doesn't occur automatically, it is a user-initiated action.*

        Sums up the value of all splits in ``new_split_currency``, using exchange rates for
        :attr:`date`. If not zero, create a new unassigned split with the opposite of that amount.

        Of course, we need to have called :meth:`balance` before we can call this.

        :param new_split_currency: :class:`.Currency`
        """
        converted_amounts = (convert_amount(split.amount, new_split_currency, self.date) for split in self.splits)
        converted_total = sum(converted_amounts)
        if converted_total != 0:
            target = first(s for s in self.splits if (s.account is None) and of_currency(s.amount, new_split_currency))
            if target is not None:
                target.amount -= converted_total
            else:
                self.add_split(Split(None, -converted_total))

    def reassign_account(self, account, reassign_to=None):
        """Reassign all splits from ``account`` to ``reassign_to``.

        All :attr:`splits` belonging to ``account`` will be changed to ``reassign_to``.

        :param account: :class:`.Account`
        :param reassign_to: :class:`.Account`
        """
        for split in self.splits:
            if split.account == account:
                split.reconciliation_date = None
                split.account = reassign_to

    def remove_split(self, split):
        TransactionBase.remove_split(self, split)
        self.balance()

    def replicate(self):
        res = Transaction(self.date)
        res.copy_from(self)
        return res

    def set_splits(self, splits):
        self.splits = splits

    def splitted_splits(self):
        """Returns :attr:`splits` separated in two groups ("froms" and "tos").

        "froms" are splits with a negative amount and "tos", the positive ones. Null splits are
        generally sent to the "froms" side, unless "tos" is empty.

        Returns ``(froms, tos)``.
        """
        splits = self.splits
        null_amounts = [s for s in splits if s.amount == 0]
        froms = [s for s in splits if s.amount < 0]
        tos = [s for s in splits if s.amount > 0]
        if not tos and null_amounts:
            tos.append(null_amounts.pop())
        froms += null_amounts
        return froms, tos

    # --- Properties
    @property
    def amount(self):
        """*get/set*. :class:`.Amount`. Total amount of the transaction.

        In short, the sum of all positive :attr:`splits`.

        Can only be set if :attr:`can_set_amount` is true, that is, if we have less than two splits.
        When set, we'll set :attr:`splits` in order to create a two-way transaction of that amount,
        preserving from and to accounts if needed.
        """
        if self.is_mct:
            # We need an approximation for the amount value. What we do is we take the currency of the
            # first split and use it as a base currency. Then, we sum up all amounts, convert them, and
            # divide the sum by 2.
            splits_with_amount = [s for s in self.splits if s.amount != 0]
            currency = splits_with_amount[0].amount.currency_code
            convert = lambda a: convert_amount(abs(a), currency, self.date)
            amount_sum = sum(convert(s.amount) for s in splits_with_amount)
            return amount_sum * 0.5
        else:
            return sum(s.debit for s in self.splits)

    @amount.setter
    def amount(self, value):
        assert self.can_set_amount
        if value == self.amount:
            return
        debit = first(s for s in self.splits if s.debit)
        credit = first(s for s in self.splits if s.credit)
        debit_account = debit.account if debit is not None else None
        credit_account = credit.account if credit is not None else None
        self.splits = [Split(debit_account, value), Split(credit_account, -value)]

    @property
    def can_set_amount(self):
        """*readonly*. ``bool``. Whether we can set :attr:`amount`.

        True is we have two or less splits of the same currency.
        """
        return (len(self.splits) <= 2) and (not self.is_mct)

    @property
    def has_unassigned_split(self):
        """*readonly*. ``bool``. Whether any of our splits is unassigned (None)."""
        return any(s.account is None for s in self.splits)

    @property
    def is_mct(self):
        """*readonly*. ``bool``. Whether our splits contain more than one currency."""
        splits_with_amount = (s for s in self.splits if s.amount != 0)
        try:
            return not allsame(s.amount.currency_code for s in splits_with_amount)
        except ValueError: # no split with amount
            return False

    @property
    def is_null(self):
        """*readonly*. ``bool``. Whether our splits all have null amounts."""
        return all(not s.amount for s in self.splits)
