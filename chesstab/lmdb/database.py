# database.py
# Copyright 2023 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Chess database using Symas LMMD."""

from solentware_base import lmdb_database
from solentware_base.core import wherevalues
from solentware_base.core import constants

from ..core import filespec
from ..basecore import database


class Database(database.Database, lmdb_database.Database):
    """Provide access to a lmdb database of games of chess."""

    _deferred_update_module_name = "chesstab.lmdb.database_du"

    def __init__(
        self,
        DBfile,
        use_specification_items=None,
        dpt_records=None,
        **kargs,
    ):
        """Define chess database.

        **kargs
        Arguments are passed through to superclass __init__.

        """
        dbnames = filespec.make_filespec(
            use_specification_items=use_specification_items,
            dpt_records=dpt_records,
        )

        super().__init__(
            dbnames,
            folder=DBfile,
            use_specification_items=use_specification_items,
            **kargs,
        )

        # Allow space for lots of chess engine analysis.
        self._set_map_blocks_above_used_pages(200)

    def _delete_database_names(self):
        """Override and return tuple of filenames to delete."""
        return (self.database_file, self.database_file + "-lock")

    def checkpoint_before_close_dbenv(self):
        """Override.  Hijack method to set map size to file size.

        Reverse, to the extent possible, the increase in map size done
        when the database was opened.

        """
        self._set_map_size_above_used_pages_between_transactions(0)

    # def remove_game_key_from_all_cql_query_match_lists(self, gamekey):
    #    """Remove gamekey from all recordsets in CQL_QUERY_FIELD_DEF table.

    #    Overrides basecore.database.Database method for the Symas LMDB
    #    database engine.  This method copes with databases which have
    #    exactly one CQL query record.

    #    This method must not be called if a transaction is active.

    #    """
    #    valuespec = wherevalues.ValuesClause()
    #    valuespec.field = filespec.CQL_QUERY_FIELD_DEF
    #    self.start_transaction()
    #    try:
    #        # prev_key is needed when deleting a game from a lmdb
    #        # database with exactly one CQL query record.
    #        # An infinite loop on the single key available occurs
    #        # otherwise.
    #        # Not doing the file_records_under call prevents the
    #        # infinite loop at the expense of crashing ChessTab when
    #        # the list of games matching the CQL query is displayed.
    #        prev_key = None
    #        for key in self.find_values(valuespec, filespec.GAMES_FILE_DEF):
    #            if prev_key == key:
    #                break
    #            prev_key = key
    #            recordset = self.recordlist_key(
    #                filespec.GAMES_FILE_DEF,
    #                filespec.CQL_QUERY_FIELD_DEF,
    #                key=self.encode_record_selector(key),
    #            )
    #            recordset.remove_record_number(gamekey)
    #            self.file_records_under(
    #                filespec.GAMES_FILE_DEF,
    #                filespec.CQL_QUERY_FIELD_DEF,
    #                recordset,
    #                self.encode_record_selector(key),
    #            )
    #        self.commit()
    #    except:  # Backout for any exception, then re-raise.
    #        self.backout()
    #        raise

    # The 'prev_key' technique in the commented version above seems to
    # work, but prefer to detect the special case and handle it alone
    # specially.
    # See Github jnwatson/py-lmdb Issue 388.
    def remove_game_key_from_all_cql_query_match_lists(self, gamekey):
        """Remove gamekey from all recordsets in CQL_QUERY_FIELD_DEF table.

        Overrides basecore.database.Database method for the Symas LMDB
        database engine.  This method copes with databases which have
        exactly one CQL query record when a game is deleted.

        This method must not be called if a transaction is active.

        """
        valuespec = wherevalues.ValuesClause()
        valuespec.field = filespec.CQL_QUERY_FIELD_DEF
        single_key = False
        self.start_transaction()
        try:
            with self.dbtxn.transaction.cursor(
                self.table[
                    constants.SUBFILE_DELIMITER.join(
                        (filespec.GAMES_FILE_DEF, valuespec.field)
                    )
                ].datastore
            ) as cursor:
                if cursor.first():
                    if not cursor.next_nodup():
                        single_key = True
            # Database with zero, or more than one, keys is handled normally
            # by a copy of the code in the superclass method.
            if not single_key:
                for key in self.find_values(
                    valuespec, filespec.GAMES_FILE_DEF
                ):
                    recordset = self.recordlist_key(
                        filespec.GAMES_FILE_DEF,
                        filespec.CQL_QUERY_FIELD_DEF,
                        key=self.encode_record_selector(key),
                    )
                    recordset.remove_record_number(gamekey)
                    self.file_records_under(
                        filespec.GAMES_FILE_DEF,
                        filespec.CQL_QUERY_FIELD_DEF,
                        recordset,
                        self.encode_record_selector(key),
                    )
                self.commit()
                return
            # Database with exactly one key is a special case.
            with self.dbtxn.transaction.cursor(
                self.table[
                    constants.SUBFILE_DELIMITER.join(
                        (filespec.GAMES_FILE_DEF, valuespec.field)
                    )
                ].datastore
            ) as cursor:
                if cursor.first():
                    key = cursor.item()[0]  # Bare lmdb cursor returns bytes.
                    recordset = self.recordlist_key(
                        filespec.GAMES_FILE_DEF,
                        filespec.CQL_QUERY_FIELD_DEF,
                        key=key,  # key is already encoded.
                    )
                    recordset.remove_record_number(gamekey)
                    self.file_records_under(
                        filespec.GAMES_FILE_DEF,
                        filespec.CQL_QUERY_FIELD_DEF,
                        recordset,
                        key,  # key is already encoded.
                    )
            self.commit()
        except:  # Backout for any exception, then re-raise.
            self.backout()
            raise
