# chessexception.py
# Copyright 2011 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Intercept exceptions in methods called from Tkinter or threading
"""

import os.path

from solentware_grid.gui.callbackexception import CallbackException

from .. import APPLICATION_NAME, ERROR_LOG


class ChessException(CallbackException):
    """Tkinter callback and threaded activity exception handler wrappers.

    Override methods provided by CallbackException class.
    """
    error_file = None

    def get_error_file_name(self):
        """Return the exception report file name."""
        return self.error_file

    def set_error_file_name(self, directory=None):
        """Set the exception report file name to filename."""
        if directory is None:
            ChessException.error_file = None
        else:
            ChessException.error_file = os.path.join(directory, ERROR_LOG)

    def report_exception(self, root=None, title=None, message=None):
        """Extend to write exception to errorlog if available.

        root - usually the application toplevel widget
        title - usually the application name
        message - custom errorlog dialogue message if errorlog not available

        """
        import traceback
        import datetime

        if self.get_error_file_name() is not None:
            try:
                f = open(self.get_error_file_name(), 'ab')
                try:
                    f.write(
                        ''.join(
                            ('\n\n\n',
                             ' '.join(
                                 (APPLICATION_NAME,
                                  'exception report at',
                                  datetime.datetime.isoformat(
                                      datetime.datetime.today())
                                  )),
                             '\n\n',
                             traceback.format_exc(),
                             '\n\n',
                             )).encode('iso-8859-1')
                        )
                finally:
                    f.close()
                    message = ''.join(
                    ('An exception has occured.\n\nThe exception report ',
                     'has been appended to the error file.\n\nClick "Yes" ',
                     'to see the detail\nor "No" to quit the application.',
                     ))
            except:
                message = ''.join(
                    ('An exception has occured.\n\nThe attempt to append ',
                     'the exception report to the error file was not ',
                     'completed.\n\nClick "Yes" to see the detail\nor ',
                     '"No" to quit the application.',
                 ))
        super(ChessException, self).report_exception(
            root=root, title=title, message=message)

    def try_command(self, method, widget):
        """Return the method wrapped to write exception trace to error log.

        method - the command callback to be wrapped
        widget - usually the application toplevel widget

        Copied and adapted from Tkinter.

        """
        def wrapped_command_method(*a, **k):
            try:
                return method(*a, **k)
            except SystemExit as message:
                raise SystemExit(message)
            except:
                # If an unexpected exception occurs in report_exception let
                # Tkinter deal with it (better than just killing application
                # when Microsoft Windows User Access Control gets involved in
                # py2exe generated executables).
                self.report_exception(
                    root=widget.winfo_toplevel(),
                    title=APPLICATION_NAME)
        return wrapped_command_method

    def try_event(self, method):
        """Return the method wrapped to write exception trace to error log.

        method - the event callback to be wrapped

        Copied and adapted from Tkinter.

        """
        def wrapped_event_method(e):
            try:
                return method(e)
            except SystemExit as message:
                raise SystemExit(message)
            except:
                # If an unexpected exception occurs in report_exception let
                # Tkinter deal with it (better than just killing application
                # when Microsoft Windows User Access Control gets involved in
                # py2exe generated executables).
                self.report_exception(
                    root=e.widget.winfo_toplevel(),
                    title=APPLICATION_NAME)
        return wrapped_event_method

    def try_thread(self, method, widget):
        """Return the method wrapped to write exception trace to error log.

        method - the threaded activity to be wrapped
        widget - usually the application toplevel widget

        Copied and adapted from Tkinter.

        """
        def wrapped_thread_method(*a, **k):
            try:
                return method(*a, **k)
            except SystemExit as message:
                raise SystemExit(message)
            except:
                # If an unexpected exception occurs in report_exception let
                # Tkinter deal with it (better than just killing application
                # when Microsoft Windows User Access Control gets involved in
                # py2exe generated executables).
                self.report_exception(
                    root=widget.winfo_toplevel(),
                    title=APPLICATION_NAME)
        return wrapped_thread_method
