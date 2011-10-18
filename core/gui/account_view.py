# Created By: Virgil Dupras
# Created On: 2010-01-09
# Copyright 2011 Hardcoded Software (http://www.hardcoded.net)
# 
# This software is licensed under the "BSD" License as described in the "LICENSE" file, 
# which should be included with this package. The terms are also available at 
# http://www.hardcoded.net/licenses/bsd_license

from hscommon.trans import tr
from ..const import PaneType
from .base import BaseView, MESSAGES_DOCUMENT_CHANGED
from .filter_bar import EntryFilterBar

class AccountView(BaseView):
    VIEW_TYPE = PaneType.Account
    PRINT_TITLE_FORMAT = tr('{account_name}\nEntries from {start_date} to {end_date}')
    INVALIDATING_MESSAGES = MESSAGES_DOCUMENT_CHANGED | {'filter_applied',
        'date_range_changed', 'transactions_selected', 'shown_account_changed'}
    
    def __init__(self, view, mainwindow):
        BaseView.__init__(self, view, mainwindow)
        self._shown_graph = None
        self._reconciliation_mode = False
        self.filter_bar = EntryFilterBar(self)
    
    def set_children(self, children):
        self.etable, self.balgraph, self.bargraph = children
        self.maintable = self.etable
        self._shown_graph = self.balgraph
        # we count the graphs separately because the show/hide rules for them are special
        BaseView.set_children(self, [self.etable])
        self.balgraph.connect()
        self.bargraph.connect()
    
    def _revalidate(self):
        self._refresh_totals()
        self.view.refresh_reconciliation_button()
        self.filter_bar.refresh()
    
    def show(self):
        BaseView.show(self)
        account = self.mainwindow.shown_account
        if account is None:
            return
        if account.is_balance_sheet_account():
            self._shown_graph = self.balgraph
            self.view.show_line_graph()
        else:
            self._shown_graph = self.bargraph
            self.view.show_bar_graph()
        self._shown_graph.show()
    
    def hide(self):
        BaseView.hide(self)
        self.balgraph.hide()
        self.bargraph.hide()
    
    #--- Private
    def _refresh_totals(self):
        account = self.mainwindow.shown_account
        if account is None:
            return
        selected, total, total_debit, total_credit = self.etable.get_totals()
        if account.is_debit_account():
            increase = total_debit
            decrease = total_credit
        else:
            increase = total_credit
            decrease = total_debit
        total_increase_fmt = self.document.format_amount(increase)
        total_decrease_fmt = self.document.format_amount(decrease)
        msg = tr("{0} out of {1} selected. Increase: {2} Decrease: {3}")
        self.status_line = msg.format(selected, total, total_increase_fmt, total_decrease_fmt)
    
    #--- Public
    def delete_item(self):
        self.etable.delete()
    
    def duplicate_item(self):
        self.etable.duplicate_selected()
    
    def edit_item(self):
        self.mainwindow.edit_selected_transactions()
    
    def navigate_back(self):
        """When the entry table is shown, go back to the appropriate report."""
        if self.mainwindow.shown_account.is_balance_sheet_account():
            self.mainwindow.select_balance_sheet()
        else:
            self.mainwindow.select_income_statement()
    
    def move_down(self):
        self.etable.move_down()
    
    def move_up(self):
        self.etable.move_up()
    
    def new_item(self):
        self.etable.add()
    
    def show_account(self):
        self.etable.show_transfer_account()
    
    def toggle_reconciliation_mode(self):
        self._reconciliation_mode = not self._reconciliation_mode
        self.etable.reconciliation_mode = self._reconciliation_mode
        self.view.refresh_reconciliation_button()
    
    #--- Properties
    @property
    def can_toggle_reconciliation_mode(self):
        shown_account = self.mainwindow.shown_account
        return shown_account is not None and shown_account.is_balance_sheet_account()
    
    @property
    def reconciliation_mode(self):
        return self._reconciliation_mode
    
    #--- Event Handlers
    def date_range_changed(self):
        self._refresh_totals()
    
    def document_changed(self):
        self._refresh_totals()
    
    def filter_applied(self):
        self._refresh_totals()
        self.filter_bar.refresh()
    
    def performed_undo_or_redo(self):
        self._refresh_totals()
    
    # If the account view is visible when the message is broadcasted, we won't get automatically
    # invalidated, so we have to do it automatically.
    def shown_account_changed(self):
        self._invalidated = True
    
    def transactions_selected(self):
        self._refresh_totals()
    
    def transaction_changed(self):
        self._refresh_totals()
    
    def transaction_deleted(self):
        self._refresh_totals()
    
    def transactions_imported(self):
        self._refresh_totals()
    
