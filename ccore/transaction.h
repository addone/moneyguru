#pragma once
#include <time.h>
#include <stdbool.h>
#include "split.h"

typedef enum {
    TXN_TYPE_NORMAL = 1,
    TXN_TYPE_RECURRENCE = 2,
    TXN_TYPE_BUDGET = 3,
} TransactionType;

typedef struct {
    TransactionType type;
    // Date at which the transation occurs.
    time_t date;
    // Description of the transaction.
    char *description;
    // Person or entity related to the transaction.
    char *payee;
    // Check number related to the transaction.
    char *checkno;
    // Freeform note about the transaction.
    char *notes;
    // Ordering attributes. When two transactions have the same date, we order
    // them with this.
    int position;
    // Timestamp of the last modification. Used in the UI to let the user sort
    // his transactions.  This is useful for finding a mistake that we know was
    // introduced recently.
    time_t mtime;
    // Splits belonging to that txn. The transaction owns the splits and the
    // list is never over-allocated. This means that all splits are "valid".
    Split *splits;
    unsigned int splitcount;
} Transaction;

void
transaction_init(Transaction *txn, TransactionType type, time_t date);

/* Balances a multi-currency transaction.
 * 
 * Balancing out multi-currencies transasctions can be real easy because we
 * consider that currencies can never mix (and we would never make the gross
 * mistake of using market exchange rates to do our balancing), so, if we have
 * at least one split on each side of different currencies, we consider
 * ourselves balanced and do nothing.
 * 
 * However, we might be in a situation of "logical imbalance", which means that
 * the transaction doesn't logically makes sense. For example, if all our
 * splits are on the same side, we can't possibly balance out. If we have EUR
 * and CAD splits, that CAD splits themselves balance out but that EUR splits
 * are all on the same side, we have a logical imbalance.
 * 
 * This method finds those imbalance and fix them by creating unsassigned
 * splits balancing out every currency being in that situation.
 * 
 * `strong_split` is the split that was last edited (can be `NULL`). See
 * balance() for details.
 */
void
transaction_balance_currencies(Transaction *txn, const Split *strong_split);

// If dst is a fresh instance, it *has* to have been zeroed out before calling
// this.
bool
transaction_copy(Transaction *dst, Transaction *src);

Split*
transaction_add_split(Transaction *txn);

bool
transaction_move_split(Transaction *txn, Split *split, unsigned int newindex);

bool
transaction_remove_split(Transaction *txn, Split *split);

// Reallocate split array to `newsize`. If larger than the old splitcount, new
// splits are initialized to NULL account and zero amount.
void
transaction_resize_splits(Transaction *txn, unsigned int newsize);

int
transaction_cmp(const Transaction *a, const Transaction *b);

void
transaction_deinit(Transaction *txn);
