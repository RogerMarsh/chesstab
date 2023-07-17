# dptcompatdu.py
# Copyright 2022 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Provide PGN import size estimating for non-DPT interface modules.

These other modules, except Symas LMMD, take space as needed so methods
which 'do nothing' are provided.

For Symas LMMD it is possible to set an arbitrarly large size and then
reclaim any unused space by setting an arbitrarly low size.  The size
determines how large the database can get before giving a 'full' error.
"""


class DptCompatdu:
    """Provide do nothing methods for compatibility with DPT interface."""

    # pylint no-self-use message.
    # Why this method and not the other two?
    # Does it imply 'self' should not be removed given purpose of methods?
    @staticmethod
    def get_file_sizes():
        """Return an empty dictionary.

        No sizes needed.  Method exists for DPT compatibility.

        """
        return {}

    def report_plans_for_estimate(self, estimates, reporter, increases):
        """Remind user to check estimated time to do import.

        No planning needed.  Method exists for DPT compatibility.

        """
        del estimates, increases
        reporter.append_text_only("")
        reporter.append_text("Ready to start import.")
