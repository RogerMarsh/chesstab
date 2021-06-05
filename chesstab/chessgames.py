# chessgames.py
# Copyright 2008 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""View a database of chess games created from data in PGN format.

Run "python -m chesstab.chessgames" assuming chesstab is in site-packages and
Python3.3 or later is the system Python.

PGN is "Portable Game Notation", the standard non-proprietary format for files
of chess game scores.

Sqlite3 via the apsw or sqlite packages, Berkeley DB via the db package, or DPT
via the dpt package, can be used as the database engine.

When importing games while running under Wine it will probably be necessary to
use the sibling module "chessgames_winedptchunk".  The only known reason to run
under Wine is to use the DPT database engine on a platform other than Microsoft
Windows.
"""

if __name__ == "__main__":

    from . import APPLICATION_NAME

    try:
        from solentware_misc.gui.startstop import (
            start_application_exception,
            stop_application,
            application_exception,
        )
    except Exception as error:
        import tkinter.messagebox

        try:
            tkinter.messagebox.showerror(
                title="Start Exception",
                message=".\n\nThe reported exception is:\n\n".join(
                    (
                        "Unable to import solentware_misc.gui.startstop module",
                        str(error),
                    )
                ),
            )
        except:
            pass
        raise SystemExit("Unable to import start application utilities")
    try:
        from .gui.chess import Chess
    except Exception as error:
        start_application_exception(
            error, appname=APPLICATION_NAME, action="import"
        )
        raise SystemExit(" import ".join(("Unable to", APPLICATION_NAME)))
    try:
        app = Chess(allowcreate=True)
    except Exception as error:
        start_application_exception(
            error, appname=APPLICATION_NAME, action="initialise"
        )
        raise SystemExit(" initialise ".join(("Unable to", APPLICATION_NAME)))
    try:
        app.root.mainloop()
    except SystemExit:
        stop_application(app, app.root)
        raise
    except Exception as error:
        application_exception(
            error,
            app,
            app.root,
            title=APPLICATION_NAME,
            appname=APPLICATION_NAME,
        )
