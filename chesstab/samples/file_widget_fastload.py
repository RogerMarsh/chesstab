# file_widget_fastload.py
# Copyright 2023 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""The widget to drive import of a PGN file for DPT Fastload.

This module contains FileWidget, an adaptation of file_widget.FileWidget
which supports the processing required in DPT fastload.

The files written by this module are intended to be read as bytes, not str,
and contain sequences intended to be decoded as utf-8 separated by sequences
intended to be interpreted as delimiters or as numbers (in Python by the
int.from_bytes method).  The intended audience, DPT's Load method, will
understand.

DPT Fastload driven by this module using field codes has been made to work
only by changing the FileSpec to have all field names upper case.
"""

# On the devopment box deferred update for a sample of 233768 games took
# about 90 minutes: fastload took about 55 minutes.  (Modern boxes should
# be significantly quicker for both.)
# Fastload is supposed to be faster than deferred update, but some of the
# difference in run time may be from the ~1G calls, assuming only one call
# per index entry, via the swigged interface for deferred update and the
# 1 (one) call via the swigged interface for fastload.
# When an import of 2 million games was attempted the fastload slowed down
# a lot at around 500,000 games: taking about an hour to do 65280 games
# compared with about 6 or 7 minutes per 65280 games up to about 200,000
# games.  The fastload files need to be merged into one, like what happens
# in a deferred update, to minimise out-of-order, index updates.
# Generating the fastload TAPE files for 65280 games takes just under 8
# minutes compared with just under 10 minutes in deferred update.  This is
# likely because deferred update writes several sets of 'chunk' files
# rather than one set of TAPE files.

import tkinter
import os
import time

import tkinter.messagebox
import tkinter.filedialog

from dptdb.dptapi import FLOAD_DEFAULT

from solentware_base.core.segmentsize import SegmentSize
from solentware_base.core.constants import TABLE_B_SIZE, FILEDESC, BRECPPG

from pgn_read.core.tagpair_parser import PGNTagPair, GameCount

from ..dpt.database_one_step_du import ChessDBrecordGameFastload
from ..core import constants
from ..core import filespec

_RECORD_SEPARATOR = b"\xff\xff"
_SEGMENT_COUNT_UNKNOWN = b"\xff\xff"
_VALUE_TERMINATOR = b"\xff\xff\xff\xff"
_TAPED_DAT = "_TAPED.DAT"
_TAPEF_DAT = "_TAPEF.DAT"
_TAPEI_DAT = ("_TAPEI_", ".DAT")
_STARS = b"*" * 70  # 70 because DPT's Unload method outputs 70 '*'s.
_CRLF = b"\r\n"  # DPT newline sequence.


def _count_games_in_import(file_list):
    """Return count of games in files in file_list, or None.

    This is a trimmed version of method _estimate_games_in_import in the
    ..gui.chessdu.DeferredUpdateEstimateProcess class.

    """
    reader = PGNTagPair(game_class=GameCount)
    gamecount = 0
    for pgnfile in file_list:
        for encoding in constants.ENCODINGS:
            filechars = []
            with open(pgnfile, mode="r", encoding=encoding) as source:
                try:
                    while True:
                        chars = source.read(1024 * 1000)
                        filechars.append(len(chars))
                        if not chars:
                            break
                except UnicodeDecodeError:
                    continue
            with open(pgnfile, mode="r", encoding=encoding) as source:
                for _ in reader.read_games(source):
                    gamecount += 1
            if filechars:
                filechars.clear()
                break
        else:
            return None
    return gamecount


def file_du(database, dbpath, pgnpath, **kwargs):
    """Open database, import games and close database."""
    print(time.ctime(), "start")
    gamecount = _count_games_in_import([pgnpath])
    if gamecount is None:
        print(time.ctime(), "unable to read file - possible encoding problem")
        return
    print(time.ctime(), gamecount, "games found")
    cdb = database(dbpath, allowcreate=True, **kwargs)
    print(
        time.ctime(),
        "create games database in",
        dbpath,
        "if it does not exist",
    )

    # Create database to get codes for field names.
    # Even though these are ignored in some fastload situations.
    cdb.open_database()

    # Not needed while importer is putting all records in TAPED file.
    # cdb.increase_database_size(
    #     files={filespec.GAMES_FILE_DEF: (gamecount, gamecount)}
    # )

    cdb.close_database()

    importer = ChessDBrecordGameFastload()
    fldb = FastloadDatabase(cdb, dbpath, "games", **kwargs)
    fldb.set_defer_update()
    with open(pgnpath, "r", encoding="iso-8859-1") as pgn_file:
        print(
            time.ctime(),
            "get games from PGN file and write TAPED file",
        )
        importer.import_pgn(fldb, pgn_file, os.path.basename(pgnpath))
    recordcount = fldb.table_b_page_count * fldb.brecppg
    cdb.open_database()
    cdb.increase_database_size(
        files={filespec.GAMES_FILE_DEF: (recordcount, recordcount)}
    )
    cdb.close_database()
    print(
        time.ctime(),
        "datasize size is now enough for",
        recordcount,
        "records",
    )
    fldb.do_final_segment_deferred_updates()
    fldb.unset_defer_update()
    print(time.ctime(), "end")


def directory_du(database, dbpath, pgnpath, **kwargs):
    """Open database, import games and close database."""
    pathlist = [os.path.join(pgnpath, p) for p in os.listdir(pgnpath)]
    print(time.ctime(), "start")
    gamecount = _count_games_in_import(pathlist)
    if gamecount is None:
        print(
            time.ctime(),
            "found a file which cannot be read - possible encoding problem",
        )
        return
    print(time.ctime(), gamecount, "games found")
    cdb = database(dbpath, allowcreate=True, **kwargs)
    print(
        time.ctime(),
        "create games database in",
        dbpath,
        "if it does not exist",
    )
    cdb.open_database()
    cdb.increase_database_size(
        files={filespec.GAMES_FILE_DEF: (gamecount, gamecount)}
    )
    cdb.close_database()
    table = cdb.table
    importer = ChessDBrecordGameFastload()
    fldb = FastloadDatabase(cdb, dbpath, "games", **kwargs)
    fldb.set_defer_update()
    print(
        time.ctime(),
        "get games from PGN file and write TAPED file",
    )
    for filepath in pathlist:
        with open(filepath, "r", encoding="iso-8859-1") as pgn_file:
            importer.import_pgn(fldb, pgn_file, os.path.basename(filepath))
    fldb.do_final_segment_deferred_updates()
    fldb.unset_defer_update()
    print(time.ctime(), "end")


class FileWidget:
    """Provide select PGN game file dialogue and import from selected file."""

    def __init__(self, database, engine_name, **kwargs):
        """Import games into database using engine_name database engine."""
        root = tkinter.Tk()
        root.wm_title(string=" - ".join((engine_name, "Import PGN file")))
        root.wm_iconify()
        dbdir = tkinter.filedialog.askdirectory(
            title=" - ".join((engine_name, "Open ChessTab database"))
        )
        if dbdir:
            filename = tkinter.filedialog.askopenfilename(
                title="PGN file of Games",
                defaultextension=".pgn",
                filetypes=(("PGN Chess Games", "*.pgn"),),
            )
            if filename:
                if tkinter.messagebox.askyesno(
                    title="Import Games", message="Proceed with import"
                ):
                    file_du(database, dbdir, filename, **kwargs)
        root.destroy()


class FastloadDatabase:
    """Interface expected by import_pgn() method but output to flat file.

    Format is described in DPTDocs/dbaguide.html at 'Appendix 2. Fast
    load I/O file formats'.

    """

    segment_size_bytes = TABLE_B_SIZE
    deferred_update_points = (segment_size_bytes * 8 - 1,)
    _FLAT_FILE = "___flat_file"

    def __init__(self, database, dbpath, file, **kwargs):
        """Import games into database via DPT fast load format.

        database is expected to exist in dbpath, and temporary flat files
        will be created in subdirectories of dbpath.

        """
        self.target_database = database
        self.target_database_path = dbpath
        self.target_database_kwargs = kwargs

        # Align segment size with DPT segment size so import_pgn method
        # will do the right thing.
        self.set_segment_size()

        # These assume a single DPT file is being loaded.
        # These are the items needed by self.put_instance().
        self.target_database_file = file
        table = database.table[file]
        self.target_table = table
        self.target_database_ddname = table.ddname
        self.target_primary = table.primary
        self.target_field_codes = table._field_codes
        self.target_dpt_field_names = table.dpt_field_names
        self.target_primary_field_code = table._field_codes[
            table.dpt_field_names[table.primary]
        ]
        self.target_safe_length = table.dpt_primary_field_length
        self.brecppg = self.target_database.specification[
            filespec.GAMES_FILE_DEF
        ][FILEDESC][BRECPPG]

        # Two byte pointer per record on Table B page.
        self._usable_space_per_page = TABLE_B_SIZE - self.brecppg * 2

        # These should be dicts keyed by DPT file name.
        # This sample assumes one DPT file is being loaded.
        self.pgn_file_game_number = 0
        self.segment_recno = -1
        self.space_on_current_page = 0
        self.table_b_page_count = 0

        self.flat_file = {name: None for name in self.target_field_codes}

    def start_transaction(self):
        """Start transaction on target database."""
        self.target_database.start_transaction()

    def commit(self):
        """Commit transaction on target database."""
        self.target_database.commit()

    def backout(self):
        """Backout transaction on target database."""
        self.target_database.backout()

    def set_defer_update(self):
        """Create TAPED data file and TAPEF field definitions."""
        print(
            time.ctime(),
            "create TAPED and TAPEF files",
        )
        os.mkdir(os.path.join(self.target_database_path, self._FLAT_FILE))
        self._create_tapef()
        self._create_taped()
        self._write_header(
            self.flat_file[self.target_dpt_field_names[self.target_primary]],
            description=self.target_database_ddname.join(
                ("File ", ", data records")
            ),
        )

    def do_final_segment_deferred_updates(self):
        """Apply TAPED file to DPT database.

        Do DPT Fastload operation for segment.

        The TAPE files are not deleted after, and new ones for the next
        segment are not created.

        There will be less records than in a full segment.

        """
        print(time.ctime(), "processing final segment")
        self._do_segment_fastload()

    def unset_defer_update(self):
        """Delete TAPE files, and the directory containing them if empty."""
        print(
            time.ctime(),
            "delete TAPED and TAPEF files",
        )
        self._delete_tape_files(delete_tapef=True)
        os.rmdir(os.path.join(self.target_database_path, self._FLAT_FILE))

    def put_instance(self, file, instance):
        """Write instance to TAPED file and collect values for TAPEI files."""
        assert file == self.target_database_file
        instance.set_packed_value_and_indexes()
        srv = instance.srvalue
        safe_length = self.target_safe_length
        self.pgn_file_game_number += 1
        self.segment_recno += 1
        if self.segment_recno % self.brecppg == 0:
            self.space_on_current_page = self._usable_space_per_page
            self.table_b_page_count += 1
        recnum = self.segment_recno.to_bytes(4, byteorder="little")
        flat_file = self.flat_file
        field_codes = self.target_field_codes
        dpt_field_names = self.target_dpt_field_names
        fieldname = dpt_field_names[self.target_primary].encode()
        field_values = flat_file[self.target_primary]
        field_values.write(recnum)
        # TAPED files created by DPT Unload() method have two bytes between
        # the recum and first fieldcode bytes.  The DPT Load method in
        # dbf_file.cpp is expecting two bytes with high-bit (integer) set
        # indicating 'block xfer mode' as an alternative to an immediate
        # fieldcode in the range 0 to 4000.  The 'block xfer mode' is not
        # mentioned in the DPT DBA Guide.
        for i in range(0, len(srv), safe_length):
            value = srv[i : i + safe_length].encode()
            self.space_on_current_page -= len(value) + 1
            if self.space_on_current_page < 0:
                self.space_on_current_page = self._usable_space_per_page
                self.table_b_page_count += 1
            field_values.write(self.target_primary_field_code)
            field_values.write(len(value).to_bytes(1))
            field_values.write(value)
        sri = instance.srindex
        sec = self.target_table.secondary
        pcb = instance.putcallbacks
        for indexname in sri:
            if indexname not in pcb:
                fieldcode = field_codes[dpt_field_names[sec[indexname]]]
                for value in sri[indexname]:
                    field_values.write(fieldcode)
                    value = value.encode()
                    field_values.write(len(value).to_bytes(1))
                    field_values.write(value)
        field_values.write(_RECORD_SEPARATOR)
        # Attempting to do this probably makes no sense here.
        if len(pcb):
            instance.load_key(self.segment_recno)
            for indexname in sri:
                if indexname in pcb:
                    pcb[indexname](instance, sri[indexname])

    def set_segment_size(self):
        """Copy the database segment size to the SegmentSize object.

        Follow lead of solentware_base._database.Database though this class
        is not a subclass.

        The SegmentSize object derives various constants from the database
        segment size, initially from a default value.
        """
        SegmentSize.db_segment_size_bytes = self.segment_size_bytes

    def _create_tapef(self):
        """Create the field definition file.

        DPT documentation suggests this is not needed because the fields
        already exist.  But exceptions and the audit trail suggest
        otherwise.

        """
        with open(
            os.path.join(
                self.target_database_path,
                self._FLAT_FILE,
                "".join((self.target_database_ddname, _TAPEF_DAT)),
            ),
            mode="wb",  # could do str but other files are done as bytes.
        ) as tapef:
            self._write_header(
                tapef,
                description=self.target_database_ddname.join(
                    ("File ", ", field definitions")
                ),
            )
            file = self.target_database.table[self.target_database_file]
            for field, code in file._field_codes.items():
                properties = []
                attribute = file._field_attributes[field]

                # Calculate each line as str then encode to write.
                if attribute.IsVisible():
                    properties.append("VISIBLE")
                if attribute.IsInvisible():
                    properties.append("INVISIBLE")
                if attribute.IsString():
                    properties.append("STRING")
                if attribute.IsUpdateAtEnd():
                    properties.append("UPDATE AT END")
                if attribute.IsUpdateInPlace():
                    properties.append("UPDATE IN PLACE")
                if not attribute.IsOrdered():
                    properties.append("NON-ORDERED")
                if attribute.IsOrdNum():
                    properties.append("ORDERED NUMERIC")
                if attribute.IsOrdChar():
                    properties.append("ORDERED CHARACTER")
                splitpct = attribute.Splitpct()
                if splitpct and attribute.IsOrdered():
                    properties.append(" ".join(("SPLITPCT", str(splitpct))))
                define = (
                    "DEFINE FIELD",
                    str(int.from_bytes(code, byteorder="little")),
                    self.target_dpt_field_names[field].join(("'", "'")),
                    ", ".join(properties).join(("(", ")\n")),
                )
                tapef.write(" ".join(define).encode())

    def _write_header(self, tape, description=None):
        """Write header comments to TAPE file including DPT format options.

        Format options are [-+]<option> which turn the option off or on.

        The options used here are the default options for DPT's Unload
        method, as in TAPE files written by Unload.  See DPT documentation
        for descriptions.

        """
        tape.write(_STARS)
        tape.write(_CRLF)
        tape.write(b"* Simulated fast unload output")
        tape.write(_CRLF)
        tape.write(b"* ")
        if description:
            tape.write(description.encode())
        tape.write(_CRLF)
        tape.write(
            b"* Format options -FNAMES -NOFLOAT -EBCDIC -ENDIAN -CRLF -PAI"
        )
        tape.write(_CRLF)
        tape.write(_STARS)
        tape.write(_CRLF)

    def _create_taped(self):
        """Create the data file.

        DPT documentation suggests the index files, tapei for each field,
        are not needed if the field=value pairs are in the taped file.

        This may not be true for invisible fields, following the example
        of their treatment in _dpt.DPTFile.put_instance() method, because
        it did not work when tried.

        """
        for name, code in self.target_field_codes.items():
            if code == self.target_primary_field_code:
                self.flat_file[name] = open(
                    os.path.join(
                        self.target_database_path,
                        self._FLAT_FILE,
                        "".join((self.target_database_ddname, _TAPED_DAT)),
                    ),
                    mode="wb",
                )
                continue

    def _delete_tape_files(self, delete_tapef=False):
        """Delete the 'TAPE' files retaining 'TAPEF' by default."""
        tape_files = []
        if delete_tapef:
            tape_files.append(_TAPEF_DAT)
        for name, code in self.target_field_codes.items():
            if code == self.target_primary_field_code:
                tape_files.append(_TAPED_DAT)
                continue
        for tapef in tape_files:
            os.remove(
                os.path.join(
                    self.target_database_path,
                    self._FLAT_FILE,
                    "".join((self.target_database_ddname, tapef)),
                )
            )

    def _do_segment_fastload(self):
        """Do DPT Fastload.

        Cannot backout after Load() call, if there is an exception such
        as 'File Full' for example, so backups are needed.

        """
        for tape in self.flat_file.values():
            if tape is not None:
                tape.close()
        print(
            time.ctime(),
            "games up to",
            self.pgn_file_game_number,
            "in PGN file will be added to database",
        )
        print(
            time.ctime(),
            "records require",
            self.table_b_page_count,
            "Table B pages in database",
        )
        print(
            time.ctime(),
            "add games to games database from TAPE files",
        )
        cdb = self.target_database
        cdb.open_database()

        # Arguments are defaults except for directory name, the last one,
        # but Load() method takes positional arguments only.
        # (In a DPT file reorganisation all arguments can be the defaults.)
        cdb.table[self.target_database_file].opencontext.Load(
            FLOAD_DEFAULT,
            0,
            None,
            os.path.join(self.target_database_path, self._FLAT_FILE),
        )

        cdb.close_database()
        print(time.ctime(), "games added to database")
