# Copyright 2019 Virgil Dupras
#
# This software is licensed under the "GPLv3" License as described in the "LICENSE" file,
# which should be included with this package. The terms are also available at
# http://www.gnu.org/licenses/gpl-3.0.html

from datetime import date

from core.model.recurrence import get_repeat_type_desc
from core.util import first
from core.trans import tr

from ..exception import OperationAborted
from ..model.recurrence import Recurrence, RepeatType
from ..model.transaction import Transaction
from .selectable_list import LinkedSelectableList
from .transaction_panel import PanelWithTransaction

REPEAT_OPTIONS_ORDER = [
    RepeatType.Daily, RepeatType.Weekly, RepeatType.Monthly, RepeatType.Yearly,
    RepeatType.Weekday, RepeatType.WeekdayLast
]

REPEAT_EVERY_DESCS = {
    RepeatType.Daily: tr('day'),
    RepeatType.Weekly: tr('week'),
    RepeatType.Monthly: tr('month'),
    RepeatType.Yearly: tr('year'),
    RepeatType.Weekday: tr('month'),
    RepeatType.WeekdayLast: tr('month'),
}

REPEAT_EVERY_DESCS_PLURAL = {
    RepeatType.Daily: tr('days'),
    RepeatType.Weekly: tr('weeks'),
    RepeatType.Monthly: tr('months'),
    RepeatType.Yearly: tr('years'),
    RepeatType.Weekday: tr('months'),
    RepeatType.WeekdayLast: tr('months'),
}

class WithScheduleMixIn:
    def _refresh_repeat_types(self):
        descs = (
            get_repeat_type_desc(rtype, self.schedule.start_date)
            for rtype in REPEAT_OPTIONS_ORDER)
        # remove empty descs
        descs = [desc for desc in descs if desc]
        self.repeat_type_list[:] = descs

    def _update_repeat_type_selection(self, index):
        repeat_type = REPEAT_OPTIONS_ORDER[index]
        self.repeat_type = repeat_type

    @property
    def start_date(self):
        return self.app.format_date(self.schedule.start_date)

    @start_date.setter
    def start_date(self, value):
        parsed = self.app.parse_date(value)
        if parsed == self.schedule.start_date:
            return
        self.schedule.change(start_date=parsed)
        self._refresh_repeat_types()

    @property
    def repeat_every(self):
        return self.schedule.repeat_every

    @repeat_every.setter
    def repeat_every(self, value):
        value = max(1, value)
        self.schedule.change(repeat_every=value)
        self.view.refresh_repeat_every()

    @property
    def repeat_every_desc(self):
        if self.schedule.repeat_every > 1:
            return REPEAT_EVERY_DESCS_PLURAL[self.schedule.repeat_type]
        else:
            return REPEAT_EVERY_DESCS[self.schedule.repeat_type]

    @property
    def repeat_type(self):
        return self.schedule.repeat_type

    @repeat_type.setter
    def repeat_type(self, value):
        if value == self.schedule.repeat_type:
            return
        self.schedule.change(repeat_type=value)
        self.view.refresh_repeat_every()

    def create_repeat_type_list(self):
        self.repeat_type_list = LinkedSelectableList(setfunc=self._update_repeat_type_selection)

class SchedulePanel(PanelWithTransaction, WithScheduleMixIn):
    def __init__(self, mainwindow):
        PanelWithTransaction.__init__(self, mainwindow)
        self.create_repeat_type_list()

    # --- Override
    def _load(self):
        schedule = first(self.mainwindow.selected_schedules)
        self._load_schedule(schedule)

    def _new(self):
        self._load_schedule(Recurrence(Transaction(date.today(), amount=0), RepeatType.Monthly, 1))

    def _save(self):
        repeat_type = self.schedule.repeat_type
        repeat_every = self.schedule.repeat_every
        stop_date = self.schedule.stop_date
        self.document.change_schedule(
            self.original, self.transaction, repeat_type=repeat_type, repeat_every=repeat_every,
            stop_date=stop_date
        )
        self.mainwindow.revalidate()

    # --- Private
    def _load_schedule(self, schedule):
        if schedule is None:
            raise OperationAborted()
        self.original = schedule
        self.schedule = schedule.replicate()
        self.transaction = self.schedule.ref
        self._refresh_repeat_types()
        self.repeat_type_list.select(REPEAT_OPTIONS_ORDER.index(schedule.repeat_type))
        self.view.refresh_repeat_every()
        self.split_table.refresh_initial()

    # --- Properties
    @property
    def stop_date(self):
        if self.schedule.stop_date is None:
            return ''
        return self.app.format_date(self.schedule.stop_date)

    @stop_date.setter
    def stop_date(self, value):
        try:
            stop_date = self.app.parse_date(value)
        except (ValueError, TypeError):
            stop_date = None
        self.schedule.change(stop_date=stop_date)

