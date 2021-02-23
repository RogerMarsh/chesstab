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

if __name__ == '__main__':

    from . import APPLICATION_NAME
    
    try:

        from .gui.chess import Chess

        app = Chess(allowcreate=True, dptchunksize=5000)
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
