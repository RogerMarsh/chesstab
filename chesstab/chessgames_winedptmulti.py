# chessgames_winedptmulti.py
# Copyright 2010 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Import chess games when using DPT on Wine.

"chessgames_winedptmulti" is an obsolete version of "chessgames_winedptchunk".

This module has survived as an example of how to code multi-step in Python.
"""

if __name__ == "__main__":
    from . import APPLICATION_NAME

    APP_NAME = " ".join((APPLICATION_NAME, "(WineDPTMulti)"))
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
                        "".join(
                            (
                                "Unable to import ",
                                "solentware_misc.gui.startstop module",
                            )
                        ),
                        str(error),
                    )
                ),
            )
        except tkinter.TclError:
            pass
        raise SystemExit(
            "Unable to import start application utilities"
        ) from error
    try:
        from .gui.chess import Chess
    except Exception as error:
        start_application_exception(error, appname=APP_NAME, action="import")
        raise SystemExit(" import ".join(("Unable to", APP_NAME))) from error
    try:
        app = Chess(allowcreate=True, dptmultistepdu=True)
    except Exception as error:
        start_application_exception(
            error, appname=APP_NAME, action="initialise"
        )
        raise SystemExit(
            " initialise ".join(("Unable to", APP_NAME))
        ) from error
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
            title=APP_NAME,
            appname=APP_NAME,
        )
        raise SystemExit(
            " reporting exception in ".join(("Exception while", APP_NAME))
        ) from error
