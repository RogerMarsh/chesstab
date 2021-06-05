# analysis.py
# Copyright 2019 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Interface to chess database for chess engine analysis index.
"""

from ..core.filespec import (
    VARIATION_FIELD_DEF,
    ENGINE_FIELD_DEF,
    ANALYSIS_FILE_DEF,
)


class Analysis:

    """Represent chess engine analysis on file that matches a postion.

    Notes:

    The find_*() methods should migrate to the database engine modules and the
    get_*() methods should migrate to a ../core/? module.

    """

    def __init__(self, dbhome, dbset, dbname, newrow=None):
        super().__init__(dbhome, dbset, dbname, newrow=newrow)

        # FEN and engine used to do analysis.
        self.engine = None
        self.fen = None

    def find_position_analysis(self, fen):
        """Find analysis records matching fen position."""
        self.engine = None
        self.fen = None
        if not fen:
            self.set_recordset(self.dbhome.recordlist_nil(self.dbset))
            return

        fen = self.dbhome.encode_record_selector(fen)

        recordset = self.dbhome.recordlist_key(
            self.dbset, VARIATION_FIELD_DEF, fen
        )

        self.set_recordset(recordset)
        self.fen = fen

    def find_engine_analysis(self, engine):
        """Find analysis records matching chess engine."""
        self.engine = None
        self.fen = None
        if not engine:
            self.set_recordset(self.dbhome.recordlist_nil(self.dbset))
            return

        engine = self.dbhome.encode_record_selector(engine)

        recordset = self.dbhome.recordlist_key(
            self.dbset, ENGINE_FIELD_DEF, engine
        )

        self.set_recordset(recordset)
        self.engine = engine

    def find_engine_position_analysis(self, engine=None, fen=None):
        """Find analysis records matching chess engine and fen."""
        self.engine = None
        self.fen = None
        if not engine:
            if not fen:
                self.set_recordset(self.dbhome.recordlist_nil(self.dbset))
            else:
                self.find_position_analysis(fen)
            return
        elif not fen:
            self.find_engine_analysis(engine)
            return

        engine = self.dbhome.encode_record_selector(engine)
        fen = self.dbhome.encode_record_selector(fen)

        fenset = self.dbhome.recordlist_key(
            self.dbset, VARIATION_FIELD_DEF, fen
        )
        engineset = self.dbhome.recordlist_key(
            self.dbset, ENGINE_FIELD_DEF, engine
        )
        self.set_recordset(engineset & fenset)

        self.engine = engine
        self.fen = fen

    def get_position_analysis(self, fen):
        """Get analysis matching fen position.

        It is assumed merging data from all records matching fen makes sense.

        """
        self.find_position_analysis(fen)
        analysis = self.newrow().value
        ar = self.newrow()
        arv = ar.value
        rsc = self.get_cursor()
        try:
            r = rsc.first()
            while r:
                ar.load_record(r)
                analysis.scale.update(arv.scale)
                analysis.variations.update(arv.variations)
                r = rsc.next()
            else:
                analysis.position = fen
        finally:
            rsc.close()
        return analysis

    def get_position_analysis_records(self, fen):
        """Return list of analysis records matching fen position."""
        self.find_position_analysis(fen)
        records = []
        rsc = self.get_cursor()
        try:
            r = rsc.first()
            while r:
                ar = self.newrow()
                ar.load_record(r)
                records.append(ar)
                r = rsc.next()
        finally:
            rsc.close()
        return records
