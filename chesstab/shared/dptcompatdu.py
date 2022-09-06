# dptcompatdu.py
# Copyright 2022 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""The DptCompatdu class for methods shared by non-DPT interface modules."""


class DptCompatdu:
    """Provide do nothing methods for compatibility with DPT interface."""

    def add_import_buttons(self, *a):
        """Add button actions for Berkeley DB to Import dialogue.

        None required.  Method exists for DPT compatibility.

        """

    def get_file_sizes(self):
        """Return an empty dictionary.

        No sizes needed.  Method exists for DPT compatibility.

        """
        return dict()

    def report_plans_for_estimate(self, estimates, reporter):
        """Remind user to check estimated time to do import.

        No planning needed.  Method exists for DPT compatibility.

        """
        # See comment near end of class definition Chess in relative module
        # ..gui.chess for explanation of this change.
        # reporter.append_text_only(''.join(
        #    ('The expected duration of the import may make starting ',
        #     'it now inconvenient.',
        #     )))
        # reporter.append_text_only('')