# view_players_bsddb3.py
# Copyright 2016 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Print names in games_Black and games_White records where the name with
',' and '.' ripped out is not the name in the record."""


if __name__ == "__main__":

    import os
    import ast
    import re

    re_normalize_player_name = re.compile("([^,\.\s]+(?:,|\.)?)(?:\s*)")

    file_dbname_map = {
        "games_Black": "Black",
        "games_White": "White",
    }

    # bsddb removed from Python 3.n
    try:
        from bsddb3.db import DB
    except ImportError:
        from bsddb.db import DB

    import tkinter.filedialog

    directoryname = tkinter.filedialog.askdirectory(title="DB file to view")
    if directoryname:
        for bn, tn in file_dbname_map.items():
            db = DB()
            db.open(
                os.path.join(directoryname, os.path.basename(directoryname)),
                bn,
            )
            c = db.cursor()
            rec = c.first()
            print(tn)
            while rec:
                k, v = rec
                ks = k.decode("iso-8859-1")
                nks = " ".join(re_normalize_player_name.findall(ks))
                if ks != nks:
                    print(ks)
                rec = c.next()
                if rec is None:
                    break
                # print(rec)
            c.close()
            db.close()
            del db
