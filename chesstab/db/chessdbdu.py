# chessdbdu.py
# Copyright 2008 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Chess database update using custom deferred update for Berkeley DB.
"""

import os
import bz2
import zipfile

from bsddb3.db import (
    DB_CREATE,
    DB_RECOVER,
    DB_INIT_MPOOL,
    DB_INIT_LOCK,
    DB_INIT_LOG,
    DB_INIT_TXN,
    DB_PRIVATE,
)

from solentware_base import bsddb3du_database

# from solentware_base.core.constants import FILEDESC
from solentware_base.core.constants import (
    FILEDESC,
    SUBFILE_DELIMITER,
    EXISTENCE_BITMAP_SUFFIX,
    SEGMENT_SUFFIX,
)
from solentware_base.core.segmentsize import SegmentSize

from ..core.filespec import (
    FileSpec,
    GAMES_FILE_DEF,
    DB_ENVIRONMENT_GIGABYTES,
    DB_ENVIRONMENT_BYTES,
    DB_ENVIRONMENT_MAXLOCKS,
    SECONDARY,
)
from ..core.chessrecord import ChessDBrecordGameImport


class Chessbsddb3duError(Exception):
    pass


def chess_dbdu(
    dbpath, pgnpaths, file_records, reporter=lambda text, timestamp=True: None
):
    """Open database, import games and close database."""
    cdb = ChessDatabase(dbpath, allowcreate=True)
    importer = ChessDBrecordGameImport()
    cdb.open_database()
    cdb.set_defer_update()
    for pp in pgnpaths:
        s = open(pp, "r", encoding="iso-8859-1")
        importer.import_pgn(cdb, s, pp, reporter=reporter)
        s.close()
    if reporter is not None:
        reporter("Finishing import: please wait.")
        reporter("", timestamp=False)
    cdb.do_final_segment_deferred_updates()
    cdb.unset_defer_update()
    cdb.close_database()

    # There are no recoverable file full conditions for Berkeley DB (see DPT).
    return True


class ChessDatabase(bsddb3du_database.Database):

    """Provide custom deferred update for a database of games of chess."""

    # The optimum chunk size is the segment size.
    # Assuming 2Gb memory:
    # A default FreeBSD user process will not cause a MemoryError exception for
    # segment sizes up to 65536 records, so the optimum chunk size defined in
    # the superclass will be selected.
    # A MS Windows XP process will cause the MemoryError exeption which selects
    # the 32768 game chunk size.
    # A default OpenBSD user process will cause the MemoryError exception which
    # selects the 16384 game chunk size.
    # The error log problem fixed at chesstab-0.41.9 obscured what was actually
    # happening: OpenBSD gives a MemoryError exception but MS Windows XP heads
    # for thrashing swap space in some runs with a 65536 chunk size (depending
    # on order of processing indexes I think). Windows 10 Task Manager display
    # made this obvious.
    # The MemoryError exception or swap space thrashing will likely not occur
    # for a default OpenBSD user process or a MS Windows XP process with segment
    # sizes up to 32768 records. Monitoring with Top and Task Manager suggests
    # it gets close with OpenBSD.
    if SegmentSize.db_segment_size > 32768:
        for f, m in ((4, 700000000), (2, 1400000000)):
            try:
                b" " * m
            except MemoryError:

                # Override the value in the superclass.
                deferred_update_points = frozenset(
                    [
                        i
                        for i in range(
                            65536 // f - 1,
                            SegmentSize.db_segment_size,
                            65536 // f,
                        )
                    ]
                )

                break
        del f, m

    def __init__(self, DBfile, **kargs):
        """Define chess database.

        **kargs
        allowcreate == False - remove file descriptions from FileSpec so
        that superclass cannot create them.
        Other arguments are passed through to superclass __init__.

        """
        names = FileSpec(**kargs)
        environment = {
            "flags": (
                DB_CREATE
                | DB_RECOVER
                | DB_INIT_MPOOL
                | DB_INIT_LOCK
                | DB_INIT_LOG
                | DB_INIT_TXN
                | DB_PRIVATE
            ),
            "gbytes": DB_ENVIRONMENT_GIGABYTES,
            "bytes": DB_ENVIRONMENT_BYTES,
            "maxlocks": DB_ENVIRONMENT_MAXLOCKS,
        }
        # Deferred update for games file only
        # for t in list(names.keys()):
        #    if t != GAMES_FILE_DEF:
        #        del names[t]

        if not kargs.get("allowcreate", False):
            try:
                for t in names:
                    if FILEDESC in names[t]:
                        del names[t][FILEDESC]
            except:
                if __name__ == "__main__":
                    raise
                else:
                    raise Chessbsddb3duError("DB description invalid")

        try:
            super(ChessDatabase, self).__init__(names, DBfile, environment)
        except Chessbsddb3duError:
            if __name__ == "__main__":
                raise
            else:
                raise Chessbsddb3duError("DB description invalid")

    def open_context_prepare_import(self):
        """Return True

        No preparation actions thet need database open for Berkeley DB.

        """
        return True

    def get_archive_names(self, files=()):
        """Return specified files and existing operating system files"""
        if self.home_directory is None:
            return None, []
        if self._file_per_database:
            names = dict()
            for k in self.specification:
                if k not in files:
                    continue
                ns = []
                names[os.path.join(self.home_directory, k)] = ns
                for i in self.specification[k][SECONDARY]:
                    ns.append(
                        os.path.join(
                            self.home_directory, SUBFILE_DELIMITER.join((k, i))
                        )
                    )
                ns.append(
                    os.path.join(
                        self.home_directory,
                        SUBFILE_DELIMITER.join((k, EXISTENCE_BITMAP_SUFFIX)),
                    )
                )
                ns.append(
                    os.path.join(
                        self.home_directory,
                        SUBFILE_DELIMITER.join((k, SEGMENT_SUFFIX)),
                    )
                )
            exists = [
                os.path.basename(n)
                for n in names
                if os.path.exists(".".join((n, "zip")))
            ]
            return names, exists
        else:
            names = [self.database_file]
            exists = [
                os.path.basename(n)
                for n in names
                if os.path.exists(".".join((n, "bz2")))
            ]
            return names, exists

    def archive(self, flag=None, names=None):
        """Write a bz2 or zip backup of files containing games.

        Intended to be a backup in case import fails.

        """
        if self.home_directory is None:
            return
        if names is None:
            return False
        if not self.delete_archive(flag=flag, names=names):
            return
        if flag:
            if self._file_per_database:
                for n in names:
                    archiveguard = ".".join((n, "grd"))
                    archivename = ".".join((n, "zip"))
                    c = zipfile.ZipFile(
                        archivename,
                        mode="w",
                        compression=zipfile.ZIP_DEFLATED,
                        allowZip64=True,
                    )
                    for s in names[n]:
                        c.write(s, arcname=os.path.basename(s))
                    c.close()
                    c = open(archiveguard, "wb")
                    c.close()
            else:
                for n in names:
                    c = bz2.BZ2Compressor()
                    archiveguard = ".".join((n, "grd"))
                    archivename = ".".join((n, "bz2"))
                    fi = open(n, "rb")
                    fo = open(archivename, "wb")
                    inp = fi.read(10000000)
                    while inp:
                        co = c.compress(inp)
                        if co:
                            fo.write(co)
                        inp = fi.read(10000000)
                    co = c.flush()
                    if co:
                        fo.write(co)
                    fo.close()
                    fi.close()
                    c = open(archiveguard, "wb")
                    c.close()
        return True

    def delete_archive(self, flag=None, names=None):
        """Delete a zip backup of files containing games."""
        if self.home_directory is None:
            return
        if names is None:
            return False
        if flag:
            if self._file_per_database:
                not_backups = []
                for n in names:
                    archiveguard = ".".join((n, "grd"))
                    archivename = ".".join((n, "zip"))
                    if not os.path.exists(archivename):
                        try:
                            os.remove(archiveguard)
                        except:
                            pass
                        continue
                    c = zipfile.ZipFile(
                        archivename,
                        mode="r",
                        compression=zipfile.ZIP_DEFLATED,
                        allowZip64=True,
                    )
                    namelist = c.namelist()
                    extract = [
                        e
                        for e in namelist
                        if os.path.join(self.home_directory, e) in names[n]
                    ]
                    if len(extract) != len(namelist):
                        not_backups.append(os.path.basename(archivename))
                        c.close()
                        continue
                    c.close()
                    try:
                        os.remove(archiveguard)
                    except:
                        pass
                    try:
                        os.remove(archivename)
                    except:
                        pass
                if not_backups:
                    return
            else:
                for n in names:
                    archiveguard = ".".join((n, "grd"))
                    archivename = ".".join((n, "bz2"))
                    try:
                        os.remove(archiveguard)
                    except:
                        pass
                    try:
                        os.remove(archivename)
                    except:
                        pass
        return True

    def add_import_buttons(self, *a):
        """Add button actions for Berkeley DB to Import dialogue.

        None required.  Method exists for DPT compatibility.

        """
        pass

    def get_file_sizes(self):
        """Return an empty dictionary.

        No sizes needed.  Method exists for DPT compatibility.

        """
        return dict()

    def report_plans_for_estimate(self, estimates, reporter):
        """Remind user to check estimated time to do import.

        No planning needed.  Method exists for DPT compatibility.

        """
        # See comment near end of class definition Chess in relative module
        # ..gui.chess for explanation of this change.
        # reporter.append_text_only(''.join(
        #    ('The expected duration of the import may make starting ',
        #     'it now inconvenient.',
        #     )))
        # reporter.append_text_only('')
