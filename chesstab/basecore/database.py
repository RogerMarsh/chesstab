# database.py
# Copyright 2019 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""ChessTab database methods common to all database engine interfaces."""

import os
import shutil
import ast

from solentware_base.core import wherevalues, segmentsize

from ..core.filespec import (
    GAMES_FILE_DEF,
    CQL_EVALUATE_FIELD_DEF,
    CQL_EVALUATE_FIELD_VALUE,
    PGN_ERROR_FIELD_DEF,
    CQL_QUERY_FIELD_DEF,
    CQL_FILE_DEF,
    QUERY_STATUS_FIELD_DEF,
    STATUS_VALUE_ERROR,
    STATUS_VALUE_NEWGAMES,
    STATUS_VALUE_PENDING,
)
from ..core import export_game
from ..core import cqlstatement
from .. import APPLICATION_NAME, ERROR_LOG

# The *_TEST constants allow report generation for smaller number of games
# likely in test environments.
# Game numbers 0 to *_MAX are written to CQL input file.
_PGN_GAMES_MAX = 99999  # Default maximum games for most segment sizes.
_PGN_GAMES_MAX_TEST = 99  # Smaller maximum for 128 record segment size.
_SEGMENT_SIZE_TEST = 128  # Number of records per segment for tests.


class Database:
    """Define methods which are common to all database engine interfaces."""

    def deferred_update_module_name(self):
        """Return name of deferred update module."""
        return self._deferred_update_module_name

    def open_database(self, files=None):
        """Return True to fit behaviour of dpt version of this method."""
        super().open_database(files=files)
        return True

    # @staticmethod
    def _delete_database_names(self):
        """Return tuple of filenames to delete from database directory.

        Subclasses should override this method to delete the relevant files.

        """
        # return ()

    def delete_database(self):
        """Close and delete the open chess database."""
        listnames = set(n for n in os.listdir(self.home_directory))
        homenames = set(
            n
            for n in self._delete_database_names()
            if os.path.basename(n) in listnames
        )
        if ERROR_LOG in listnames:
            homenames.add(os.path.join(self.home_directory, ERROR_LOG))
        if len(listnames - set(os.path.basename(h) for h in homenames)):
            message = "".join(
                (
                    "There is at least one file or folder in\n\n",
                    self.home_directory,
                    "\n\nwhich may not be part of the database.  These items ",
                    "have not been deleted by ",
                    APPLICATION_NAME,
                    ".",
                )
            )
        else:
            message = None
        self.close_database()
        for pathname in homenames:
            if os.path.isdir(pathname):
                shutil.rmtree(pathname, ignore_errors=True)
            else:
                os.remove(pathname)
        try:
            os.rmdir(self.home_directory)
        except FileNotFoundError as exc:
            message = str(exc)
        except OSError as exc:
            if message:
                message = "\n\n".join((str(exc), message))
            else:
                message = str(exc)
        return message

    def open_after_import(self, files=()):
        """Return True after doing database engine specific open actions.

        For SQLite3 and Berkeley DB just call open_database.

        """
        del files
        super().open_database()

        # Return True to fit behaviour of dpt.database version of method.
        return True

    def save_broken_database_details(self, files=()):
        """Save database engine specific detail of broken files to be restored.

        It is assumed that the Database Services object exists.

        """

    def adjust_database_for_retry_import(self, files):
        """Database engine specific actions done before re-trying an import."""

    def mark_games_evaluated(self, allexceptkey=None, commit=True):
        """Mark all games except allexceptkey as evaluated by CQL.

        When picking the games to be evaluated by a CQL statement any games
        not marked will be evaluated.

        If commit evaluates False caller is responsible for transactions.

        """
        # The number of records marked for no evaluation is expected to be
        # a few less than the number of records on the file.  If it ever
        # gets to zero through edit and delete actions the expected
        # evaluations will not get done.
        if commit:
            self.start_transaction()
        try:
            allexcept = self.recordlist_ebm(GAMES_FILE_DEF)
            if allexceptkey is not None:
                allexcept.remove_record_number(allexceptkey)
            allexcept |= self.recordlist_all(
                GAMES_FILE_DEF, PGN_ERROR_FIELD_DEF
            )
            # The records which do not need evaluation.
            self.file_records_under(
                GAMES_FILE_DEF,
                CQL_EVALUATE_FIELD_DEF,
                allexcept,
                self.encode_record_selector(CQL_EVALUATE_FIELD_VALUE),
            )
            allexcept.close()
            if commit:
                self.commit()
        except:  # Backout for any exception, then re-raise.
            if commit:
                self.backout()
            raise

    def mark_all_games_not_evaluated(self, commit=True):
        """Mark all games as not evaluated by any CQL statements.

        When picking the games to be evaluated by a CQL statement any games
        not marked will be evaluated.

        Any games flagged as having PGN errors are treated as evaluated.

        If commit evaluates False caller is responsible for transactions.

        """
        if commit:
            self.start_transaction()
        try:
            allrecords = self.recordlist_all(
                GAMES_FILE_DEF, PGN_ERROR_FIELD_DEF
            )
            # The records which do not need evaluation.
            self.file_records_under(
                GAMES_FILE_DEF,
                CQL_EVALUATE_FIELD_DEF,
                allrecords,
                self.encode_record_selector(CQL_EVALUATE_FIELD_VALUE),
            )
            allrecords.close()
            if commit:
                self.commit()
        except:  # Backout for any exception, then re-raise.
            if commit:
                self.backout()
            raise

    def mark_cql_statements_evaluated(self, allexceptkey=None, commit=True):
        """Mark all CQL statements except allexceptkey as evaluated.

        When picking the CQL statements to be evaluated any CQL statements
        not marked will be evaluated.

        If commit evaluates False caller is responsible for transactions.

        """
        if commit:
            self.start_transaction()
        try:
            allexcept = self.recordlist_ebm(CQL_FILE_DEF)
            if allexceptkey is not None:
                allexcept.remove_record_number(allexceptkey)
            allexcept |= self.recordlist_key(
                CQL_FILE_DEF,
                QUERY_STATUS_FIELD_DEF,
                key=self.encode_record_selector(STATUS_VALUE_ERROR),
            )
            # The records which do not need evaluation.
            self.file_records_under(
                CQL_FILE_DEF,
                QUERY_STATUS_FIELD_DEF,
                allexcept,
                self.encode_record_selector(STATUS_VALUE_NEWGAMES),
            )
            allexcept.close()
            # The records which do need evaluation.
            if allexceptkey is not None:
                pending = self.recordlist_record_number(
                    CQL_FILE_DEF, key=allexceptkey
                )
                pending.remove_recordset(
                    self.recordlist_key(
                        CQL_FILE_DEF,
                        QUERY_STATUS_FIELD_DEF,
                        key=self.encode_record_selector(STATUS_VALUE_ERROR),
                    )
                )
                if pending.count_records():
                    self.file_records_under(
                        CQL_FILE_DEF,
                        QUERY_STATUS_FIELD_DEF,
                        pending,
                        self.encode_record_selector(STATUS_VALUE_PENDING),
                    )
                pending.close()
            if commit:
                self.commit()
        except:  # Backout for any exception, then re-raise.
            if commit:
                self.backout()
            raise

    def mark_all_cql_statements_not_evaluated(self, commit=True):
        """Mark all CQL statements as not evaluated.

        When picking the CQL statements to be evaluated any CQL statements
        not marked will be evaluated.

        If commit evaluates False caller is responsible for transactions.

        """
        if commit:
            self.start_transaction()
        try:
            allrecords = self.recordlist_key(
                CQL_FILE_DEF,
                QUERY_STATUS_FIELD_DEF,
                key=self.encode_record_selector(STATUS_VALUE_ERROR),
            )
            # The records which do not need evaluation.
            self.file_records_under(
                CQL_FILE_DEF,
                QUERY_STATUS_FIELD_DEF,
                allrecords,
                self.encode_record_selector(STATUS_VALUE_NEWGAMES),
            )
            # The records which do need evaluation.
            self.file_records_under(
                CQL_FILE_DEF,
                QUERY_STATUS_FIELD_DEF,
                allrecords ^ self.recordlist_ebm(CQL_FILE_DEF),
                self.encode_record_selector(STATUS_VALUE_PENDING),
            )
            allrecords.close()
            if commit:
                self.commit()
        except:  # Backout for any exception, then re-raise.
            if commit:
                self.backout()
            raise

    def run_cql_statements_on_games_not_evaluated(
        self, widget, reporter, forget_old
    ):
        """Run CQL statements on games where both are not evaluated.

        Do not call this method when a transaction is active.

        """
        widget.update()
        self.start_read_only_transaction()
        try:
            pending_query = self._get_cql_queries_pending_evaluation()
            nothing_to_do = pending_query.count_records() == 0
            pending_query.close()
        finally:  # end_read_only_transaction() correct for any exception too.
            self.end_read_only_transaction()
        if nothing_to_do:
            reporter.append_text("Nothing to do.")
            return
        widget.update()
        self.start_read_only_transaction()
        try:
            pending = self._get_games_pending_evaluation()
            nothing_to_do = pending.count_records() == 0
            pending.close()
        finally:  # end_read_only_transaction() correct for any exception too.
            self.end_read_only_transaction()
        if nothing_to_do:
            reporter.append_text("Nothing to do.")
            return
        widget.update()
        pgn_file = "".join(
            (
                self.database_file,
                "-",
                os.path.basename(self.database_file),
                ".pgn",
            )
        )
        cql_dir = "".join(
            (
                self.database_file,
                "-",
                os.path.basename(self.database_file),
                "-cql",
            )
        )
        if os.path.exists(cql_dir):
            if os.path.isdir(cql_dir):
                shutil.rmtree(cql_dir)
            else:
                os.remove(cql_dir)
        os.mkdir(cql_dir)
        widget.update()
        self.start_read_only_transaction()
        try:
            cql_query_files = self._write_cql_query_files(cql_dir)
        finally:  # end_read_only_transaction() for any exception too.
            self.end_read_only_transaction()
        if forget_old:
            self.start_transaction()
            try:
                for file in cql_query_files:
                    self.unfile_records_under(
                        GAMES_FILE_DEF,
                        CQL_QUERY_FIELD_DEF,
                        self.encode_record_selector(os.path.basename(file)),
                    )
                self.commit()
            except:  # Backout for any exception, then re-raise.
                self.backout()
                raise

        # pylint comparison-with-callable report is false positive.
        # Perhaps because db_segment_size is a property and the last statement
        # in segmentsize module is 'SegmentSize = SegmentSize()'.
        pgn_games_max = (
            _PGN_GAMES_MAX
            if segmentsize.SegmentSize.db_segment_size != _SEGMENT_SIZE_TEST
            else _PGN_GAMES_MAX_TEST
        )

        while True:
            widget.update()
            self.start_read_only_transaction()
            try:
                pending = self._get_games_pending_evaluation()
                pending_count = pending.count_records()
                if pending_count == 0:
                    pending.close()
                    break
                record_map = export_game.export_games_for_cql_scan(
                    pending, pgn_file, limit=pgn_games_max, commit=False
                )
                pending.close()
            finally:  # end_read_only_transaction() for any exception too.
                self.end_read_only_transaction()
            reporter.append_text(
                "".join(
                    (
                        "Evaluate next ",
                        str(len(record_map)),
                        " games of ",
                        str(pending_count),
                        " by ",
                        str(len(cql_query_files)),
                        " CQL queries",
                    )
                )
            )
            for cql_file in cql_query_files:
                widget.update()
                statement = cqlstatement.CQLStatement()
                statement.set_database(database=self)
                statement.dbset = GAMES_FILE_DEF
                with open(cql_file, "r", encoding="utf-8") as cqlin:
                    statement_text = cqlin.read()
                widget.update()
                statement.prepare_cql_statement(statement_text)
                widget.update()
                statement.query_container.evaluator.run_statement(
                    statement,
                    record_map,
                    reporter,
                    os.path.basename(cql_file),
                    forget_old,
                )
            widget.update()
            self.start_transaction()
            try:
                not_pending = self.recordlist_key(
                    GAMES_FILE_DEF,
                    CQL_EVALUATE_FIELD_DEF,
                    key=self.encode_record_selector(CQL_EVALUATE_FIELD_VALUE),
                )
                for record_number in record_map.values():
                    not_pending.place_record_number(record_number)
                self.file_records_under(
                    GAMES_FILE_DEF,
                    CQL_EVALUATE_FIELD_DEF,
                    not_pending,
                    self.encode_record_selector(CQL_EVALUATE_FIELD_VALUE),
                )
                self.commit()
            except:  # Backout for any exception, then re-raise.
                self.backout()
                raise
        # On reaching here all the unmarked games have been evaluated by all
        # the CQL statements.
        widget.update()
        self.start_transaction()
        try:
            self.unfile_records_under(
                GAMES_FILE_DEF,
                CQL_EVALUATE_FIELD_DEF,
                self.encode_record_selector(CQL_EVALUATE_FIELD_VALUE),
            )
            self.unfile_records_under(
                CQL_FILE_DEF,
                QUERY_STATUS_FIELD_DEF,
                self.encode_record_selector(STATUS_VALUE_NEWGAMES),
            )
            self.commit()
        except:  # Backout for any exception, then re-raise.
            self.backout()
            raise
        widget.update()
        shutil.rmtree(cql_dir)
        os.remove(pgn_file)
        reporter.append_text_only("")
        reporter.append_text("Database update completed.")
        reporter.append_text_only("")

    def _write_cql_query_files(self, cql_dir):
        """White CQL queries to files for running by CQL and return paths."""
        paths = []
        statement = cqlstatement.CQLStatement()
        literal_eval = ast.literal_eval
        pending_query = self._get_cql_queries_pending_evaluation()
        try:
            cursor = pending_query.dbhome.database_cursor(
                CQL_FILE_DEF, QUERY_STATUS_FIELD_DEF, recordset=pending_query
            )
            try:
                while True:
                    query_record = cursor.next()
                    if query_record is None:
                        break
                    cql_file = os.path.join(cql_dir, str(query_record[0]))
                    statement.split_statement(literal_eval(query_record[1]))
                    with open(cql_file, "w", encoding="utf-8") as cqlout:
                        cqlout.write(statement.get_name_statement_text())
                    paths.append(cql_file)
            finally:
                cursor.close()
        finally:
            pending_query.close()
        return paths

    def _get_games_pending_evaluation(self):
        """Return recordset of games pending CQL evaluation.

        Any games flagged as having PGN errors are treated as evaluated.

        """
        pending = self.recordlist_ebm(GAMES_FILE_DEF)

        # Should not be needed if mark_all_games_not_evaluated() was called.
        pending.remove_recordset(
            self.recordlist_all(GAMES_FILE_DEF, PGN_ERROR_FIELD_DEF)
        )

        pending.remove_recordset(
            self.recordlist_key(
                GAMES_FILE_DEF,
                CQL_EVALUATE_FIELD_DEF,
                key=self.encode_record_selector(CQL_EVALUATE_FIELD_VALUE),
            )
        )
        return pending

    def any_games_pending_evaluation(self):
        """Return True if any games are pending evaluation."""
        self.start_read_only_transaction()
        try:
            games = self._get_games_pending_evaluation()
            try:
                return games.count_records() > 0
            finally:
                games.close()
        finally:  # end_read_only_transaction() for any exception too.
            self.end_read_only_transaction()

    def _get_cql_queries_pending_evaluation(self):
        """Return recordset of CQL queries pending evaluation.

        Any CQL statements flagged as having CQL errors are treated as
        evaluated.

        """
        pending = self.recordlist_ebm(CQL_FILE_DEF)

        # Should not be needed if mark_all_cql_statements_not_evaluated()
        # was called.
        pending.remove_recordset(
            self.recordlist_key(
                CQL_FILE_DEF,
                QUERY_STATUS_FIELD_DEF,
                key=self.encode_record_selector(STATUS_VALUE_ERROR),
            )
        )

        pending.remove_recordset(
            self.recordlist_key(
                CQL_FILE_DEF,
                QUERY_STATUS_FIELD_DEF,
                key=self.encode_record_selector(STATUS_VALUE_NEWGAMES),
            )
        )
        return pending

    def any_cql_queries_pending_evaluation(self):
        """Return True if any CQL queries are pending evaluation."""
        self.start_read_only_transaction()
        try:
            queries = self.recordlist_key(
                CQL_FILE_DEF,
                QUERY_STATUS_FIELD_DEF,
                key=self.encode_record_selector(STATUS_VALUE_PENDING),
            )
            try:
                return queries.count_records() > 0
            finally:
                queries.close()
        finally:  # end_read_only_transaction() for any exception too.
            self.end_read_only_transaction()

    def valid_cql_statements_exist(self):
        """Return True if CQL queries without parse errors exist."""
        self.start_read_only_transaction()
        try:
            queries = self.recordlist_ebm(CQL_FILE_DEF)
            try:
                queries.remove_recordset(
                    self.recordlist_key(
                        CQL_FILE_DEF,
                        QUERY_STATUS_FIELD_DEF,
                        key=self.encode_record_selector(STATUS_VALUE_ERROR),
                    )
                )
                return queries.count_records() != 0
            finally:
                queries.close()
        finally:  # end_read_only_transaction() for any exception too.
            self.end_read_only_transaction()

    def clear_cql_queries_pending_evaluation(self, commit=True):
        """Clear the CQL query needs evaluation list.

        If commit evaluates False caller is responsible for transactions.

        """
        if commit:
            self.start_transaction()
        try:
            self.unfile_records_under(
                CQL_FILE_DEF,
                QUERY_STATUS_FIELD_DEF,
                key=self.encode_record_selector(STATUS_VALUE_PENDING),
            )
            if commit:
                self.commit()
        except:  # Backout for any exception, then re-raise.
            if commit:
                self.backout()
            raise

    def all_games_and_queries_evaluated(self):
        """Return True if all games and CQL queries are evaluated."""
        self.start_read_only_transaction()
        try:
            pending_games = self.recordlist_key(
                GAMES_FILE_DEF,
                CQL_EVALUATE_FIELD_DEF,
                self.encode_record_selector(CQL_EVALUATE_FIELD_VALUE),
            )
            pending_queries = self.recordlist_key(
                CQL_FILE_DEF,
                QUERY_STATUS_FIELD_DEF,
                self.encode_record_selector(STATUS_VALUE_NEWGAMES),
            )
            return (
                pending_games.count_records() == 0
                and pending_queries.count_records() == 0
            )
        finally:  # end_read_only_transaction() for any exception too.
            self.end_read_only_transaction()

    def remove_game_key_from_all_cql_query_match_lists(self, gamekey):
        """Remove gamekey from all recordsets in CQL_QUERY_FIELD_DEF table.

        This method must not be called if a transaction is active.

        """
        valuespec = wherevalues.ValuesClause()
        valuespec.field = CQL_QUERY_FIELD_DEF
        self.start_transaction()
        try:
            for key in self.find_values(valuespec, GAMES_FILE_DEF):
                recordset = self.recordlist_key(
                    GAMES_FILE_DEF,
                    CQL_QUERY_FIELD_DEF,
                    key=self.encode_record_selector(key),
                )
                recordset.remove_record_number(gamekey)
                self.file_records_under(
                    GAMES_FILE_DEF,
                    CQL_QUERY_FIELD_DEF,
                    recordset,
                    self.encode_record_selector(key),
                )
            self.commit()
        except:  # Backout for any exception, then re-raise.
            self.backout()
            raise

    def remove_cql_query_match_list_for_query_key(self, querykey):
        """Remove recordset in CQL_QUERY_FIELD_DEF table for querykey.

        This method must not be called if a transaction is active.

        """
        self.start_transaction()
        try:
            self.unfile_records_under(
                GAMES_FILE_DEF,
                CQL_QUERY_FIELD_DEF,
                self.encode_record_number(querykey),
            )
            self.commit()
        except:  # Backout for any exception, then re-raise.
            self.backout()
            raise
