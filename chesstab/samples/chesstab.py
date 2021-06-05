# chesstab.py
# Copyright 2008 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Run ChessTab with available database engine highest in preference order.

For existing databases the choice is restricted to database engines able to
open the database.

When allowcreate evaluates not true, databases cannot be created.

"""

if __name__ == "__main__":

    from chesstab.gui.chess import Chess

    app = Chess(allowcreate=True)
    app.root.mainloop()
