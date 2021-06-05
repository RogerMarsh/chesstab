# chessgames_winedptchunk.py
# Copyright 2010 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Import chess games when using DPT on Wine.

If games are not being imported, use sibling module "chessgames" instead.

Run "python -m chesstab.chessgames_winedptchunk" assuming chesstab is in
site-packages and Python3.3 or later is the system Python.

This module works around an 'out of memory' situation which arises when running
under Wine on FreeBSD using the DPT database engine to import games from a PGN
file containing more than about 5000 normal-size game scores on a system with
1Gb memory.

At least one version of Wine from before 2010 is not affected, and maybe some
other more recent versions are not affected.  It is not known whether other
systems capable of running Wine are affected.

"chessgames_winedptchunk" on Wine takes 12 times longer than "chessgames" on
Microsoft Windows, both using DPT, to complete an import of a large number of
games. Two million games is large: but 10,000 games is not large.

"""

if __name__ == "__main__":

    from . import APPLICATION_NAME

    application_name = " ".join((APPLICATION_NAME, "(WineDPTChunk)"))
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
            error, appname=application_name, action="import"
        )
        raise SystemExit(" import ".join(("Unable to", application_name)))
    try:
        app = Chess(allowcreate=True, dptchunksize=5000)
    except Exception as error:
        start_application_exception(
            error, appname=application_name, action="initialise"
        )
        raise SystemExit(" initialise ".join(("Unable to", application_name)))
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
            title=application_name,
            appname=application_name,
        )
