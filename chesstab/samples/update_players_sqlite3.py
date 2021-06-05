# update_players_sqlite3.py
# Copyright 2016 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Update names in games_Black and games_White records where the name with
',' and '.' ripped out is not the name in the record."""


if __name__ == "__main__":

    import os
    import ast
    import re
    import sqlite3

    re_normalize_player_name = re.compile("([^,\.\s]+(?:,|\.)?)(?:\s*)")

    table_names = "games_Black", "games_White"

    import tkinter.filedialog

    directoryname = tkinter.filedialog.askopenfilename(title="DB file to view")
    if directoryname:
        bn = os.path.basename(directoryname)
        sq = sqlite3.connect(directoryname)
        for t in table_names:
            print(t)
            select_statement = " ".join(("select", "*", "from", t))
            insert_statement = " ".join(
                (
                    "insert into",
                    t,
                    "(",
                    t,
                    ",",
                    "Segment",
                    ",",
                    "RecordCount",
                    ",",
                    "Game",
                    ")",
                    "values ( ? , ? , ? , ? )",
                )
            )
            delete_statement = " ".join(
                (
                    "delete from",
                    t,
                    "where",
                    t,
                    "== ? and",
                    "Segment",
                    "== ?",
                )
            )
            c = sq.cursor()
            d = sq.cursor()
            e = sq.cursor()
            c.execute(select_statement)
            while True:
                r = c.fetchone()
                if r is None:
                    break
                ks = r[0]
                nks = " ".join(re_normalize_player_name.findall(ks))
                if ks != nks:
                    # print(r)
                    try:
                        e.execute(insert_statement, (nks, r[1], r[2], r[3]))
                        d.execute(delete_statement, (ks, r[1]))
                    except sqlite3.IntegrityError:
                        print(r, nks)
                # print(r)
            c.close()
            d.close()
            e.close()
        sq.close()
        del sq
