# chessgames_winedptmulti.py
# Copyright 2010 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Import chess games when using DPT on Wine.

"chessgames_winedptmulti" is an obsolete version of "chessgames_winedptchunk".

At present it does not work either, because it uses the class definition:

class ClassName(file)

which has not been valid Python for ages.

This module has survived as an example of how to code multi-step in Python.
"""

if __name__ == '__main__':

    from . import APPLICATION_NAME
    
    try:

        from .gui.chess import Chess

        try:
            app = Chess(allowcreate=True, dptmultistepdu=True)
            app.root.mainloop()
        except:

            import tkinter.messagebox

            tkinter.messagebox.showerror(
                title=APPLICATION_NAME,
                message=''.join(
                    ('An error which cannot be handled by ',
                     APPLICATION_NAME,
                     ' has occurred.')),
                )
            try:
                app.root.destroy()
            except:
                pass
            try:
                del app
            except:
                pass
    except:

        import tkinter.messagebox

        tkinter.messagebox.showerror(
            title=APPLICATION_NAME,
            message=''.join(
                ('An error has occurred while attempting to start ',
                 APPLICATION_NAME, '.',
                 )),
            )
