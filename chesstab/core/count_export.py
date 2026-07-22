# count_export.py
# Copyright 2026 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Count items exported in an export action."""

_UPDATE_FREQUENCY = 1000


class _Counter:
    """Count and report records read, sorted, and output."""

    def __init__(self, reportbar):
        """Initialize counts and report strings."""
        self._reportbar = reportbar
        self._items_read = 0
        self._items_output = 0
        self._items_selected = 0
        self.items_database = 0
        self._read_report = ""
        self._output_report = ""

    @property
    def read_report(self):
        """Get report count of records read for sorting."""
        return self._read_report.format(self._items_read)

    @property
    def output_report(self):
        """Get report count of sorted records output."""
        return self._output_report.format(self._items_output)

    @property
    def items_selected(self):
        """Get count of records selected for export."""
        return self._items_selected

    @items_selected.setter
    def items_selected(self, value):
        """Set count of records selected for export."""
        self._items_selected = value
        formatter = str(len(str(value))).join(("{: ", "}"))
        self._read_report = "".join(
            (formatter, " read for sort of ", str(value))
        )
        self._output_report = "".join(
            (formatter, " output sorted of ", str(value))
        )

    def increment_items_output(self):
        """Incremant output count of sorted items and show in reportbar."""
        self._items_output += 1
        if not self._items_output % _UPDATE_FREQUENCY:
            self._reportbar.set_status_text(self.output_report)
            self._reportbar.status.update_idletasks()

    def increment_items_read(self):
        """Incremant read count of items to sort and show in reportbar."""
        self._items_read += 1
        if not self._items_read % _UPDATE_FREQUENCY:
            self._reportbar.set_status_text(self.read_report)
            self._reportbar.status.update_idletasks()

    def completed_report(self):
        """Get record counts report output on completion."""
        return "".join(
            (
                str(self._items_output),
                " output of ",
                str(self._items_selected),
                " selected of ",
                str(self.items_database),
                " on database",
            )
        )


def create_counter(reportbar):
    """Return a _Counter instance."""
    return _Counter(reportbar)
