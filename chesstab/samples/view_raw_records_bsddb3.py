# view_raw_records_bsddb3.py
# Copyright 2016 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Utility to show key value pairs in chesstab records in Berkeley DB."""


if __name__ == "__main__":

    import os
    import ast

    file_dbname_map = {
        "analysis": "Analysis",
        "analysis__segment": "Analysis__segments",
        "analysis__ebm": "Analysis__exist",
        "games": "Game",
        "games__segment": "Game__segments",
        "games__ebm": "Game__exist",
        "partial": "Partial",
        "partial__segment": "Partial__segments",
        "partial__ebm": "Partial__exist",
        "repertoire": "Repertoire",
        "repertoire__segment": "Repertoire__segments",
        "repertoire__ebm": "Repertoire__exist",
        "selection": "Rulename",
        "selection__segment": "Rulename__segments",
        "selection__ebm": "Rulename__exist",
        "___control": "___control",
        "analysis_engine": "Engine",
        "analysis_variation": "Variation",
        "games_Black": "Black",
        "games_Date": "Date",
        "games_Event": "Event",
        "games_pgndate": "PGNdate",
        "games_partialposition": "PartialPosition",
        "games_piecesquaremove": "PieceSquareMove",
        "games_positions": "Positions",
        "games_Result": "Result",
        "games_Round": "Round",
        "games_Site": "Site",
        "games_source": "Source",
        "games_White": "White",
        "partial_newgames": "NewGames",
        "partial_partialpositionname": "PartialPositionName",
        "repertoire_Opening": "Opening",
        "repertoire_openingerror": "OpeningError",
        "selection_rule": "Rule",
        "engine": "Engine",
        "engine__segment": "Engine__segments",
        "engine__ebm": "Engine__exist",
        "engine_command": "Engine_command",
    }

    # bsddb removed from Python 3.n
    try:
        from bsddb3.db import DB, DBNoSuchFileError
    except ImportError:
        from bsddb.db import DB, DBNoSuchFileError

    import tkinter.filedialog

    directoryname = tkinter.filedialog.askdirectory(title="DB file to view")
    if directoryname:
        filename = os.path.basename(directoryname)
        print(directoryname, filename)
        for bn, tn in sorted(file_dbname_map.items()):
            print(bn, tn)
            db = DB()
            try:
                db.open(os.path.join(directoryname, filename), bn)
            except DBNoSuchFileError:
                print("nosuch file or directory")
                db.close()
                continue
            c = db.cursor()
            # rec = c.first()
            # print(rec)
            for e in range(10):  # 0):#(1):#0):
                rec = c.next()
                if rec is None:
                    break
                print()
                print(rec)
            c.close()
            db.close()
            del db
