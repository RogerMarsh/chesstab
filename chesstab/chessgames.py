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

if __name__ == '__main__':

    from . import APPLICATION_NAME
    
    try:

        from .gui.chess import Chess

        app = Chess(allowcreate=True)
        try:
            app.root.mainloop()
        except SystemExit:
            try:
                app.root.destroy()
            except:
                pass
            try:
                del app
            except:
                pass
        except:
            try:

                import tkinter.messagebox

                try:
                    tkinter.messagebox.showerror(
                        master=app.root,
                        title=APPLICATION_NAME,
                        message=''.join(
                            ('An error which cannot be handled by ',
                             APPLICATION_NAME,
                             ' has occurred.')),
                        )
                except:

                    import tkinter

                    ser = tkinter.Tk()
                    ser.wm_title(APPLICATION_NAME)
                    tkinter.messagebox.showerror(
                        master=ser,
                        title=APPLICATION_NAME,
                        message=''.join(
                            ('An error which cannot be handled by ',
                             APPLICATION_NAME,
                             ' has occurred.')),
                        )
                    ser.destroy()
                    del ser
                try:
                    app.root.destroy()
                except:
                    pass
                try:
                    del app
                except:
                    pass
            except:
                pass
    except:

        import tkinter, tkinter.messagebox

        ser = tkinter.Tk()
        ser.wm_title(APPLICATION_NAME)
        tkinter.messagebox.showerror(
            master=ser,
            title=APPLICATION_NAME,
            message=''.join(
                ('An error has occurred while attempting to start ',
                 APPLICATION_NAME, '.',
                 )),
            )
        ser.destroy()
        del ser
