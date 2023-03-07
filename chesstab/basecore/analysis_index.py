# analysis_index.py
# Copyright 2019 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Interface to chess database for chess engine analysis index."""

from ..core.filespec import (
    VARIATION_FIELD_DEF,
    ENGINE_FIELD_DEF,
)


class AnalysisIndex:
    """Represent chess engine analysis on file that matches a position.

    Notes:
    The find_*() methods should migrate to the database engine modules and the
    get_*() methods should migrate to a ../core/? module.

    """

    def __init__(self, dbhome, dbset, dbname, newrow=None):
        """Delegate the initialize FEN and engine for analysis."""
        super().__init__(dbhome, dbset, dbname, newrow=newrow)

        # FEN and engine used to do analysis.
        self.engine = None
        self.fen = None

    def _find_position_analysis(self, fen):
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

    def _find_engine_analysis(self, engine):
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
                self._find_position_analysis(fen)
            return
        if not fen:
            self._find_engine_analysis(engine)
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
        self.dbhome.start_read_only_transaction()
        self._find_position_analysis(fen)
        analysis = self.newrow().value
        row = self.newrow()
        arv = row.value
        rsc = self.get_cursor()
        try:
            rec = rsc.first()
            while rec:
                row.load_record(rec)
                analysis.scale.update(arv.scale)
                analysis.variations.update(arv.variations)
                rec = rsc.next()
            analysis.position = fen
        finally:
            rsc.close()
            self.dbhome.end_read_only_transaction()
        return analysis

    def get_position_analysis_records(self, fen):
        """Return list of analysis records matching fen position."""
        self.dbhome.start_read_only_transaction()
        self._find_position_analysis(fen)
        records = []
        rsc = self.get_cursor()
        try:
            rec = rsc.first()
            while rec:
                row = self.newrow()
                row.load_record(rec)
                records.append(row)
                rec = rsc.next()
        finally:
            rsc.close()
            self.dbhome.end_read_only_transaction()
        return records
