# allgrid.py
# Copyright 2022 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Functions, and AllGrid class for methods, used by all *ListGrid classes.

'All' means CQLListGrid, EngineListGrid, GameListGrid, and QueryListGrid.

See cql_gamelist_query.CQLGameListQuery class for methods identical in
these classes except EngineListGrid
"""
import tkinter


class AllGrid:
    """Provide methods with identical implementation for *ListGrid classes.

    The definition is stretched to include the on_configure_canvas and
    create_edit_dialogue methods where one class, different for each method,
    has additional behaviour.
    """

    def create_edit_dialog(
        self, instance, newobject, oldobject, showinitial, modal, title=""
    ):
        """Extend to do chess initialization."""
        for obj in (newobject, oldobject):
            if obj:
                self._set_grid_database(obj)
                obj.load_record((instance.key.pack(), instance.srvalue))
        super().create_edit_dialog(
            instance, newobject, oldobject, showinitial, modal, title=title
        )

    def fill_view(
        self,
        currentkey=None,
        down=True,
        topstart=True,
        exclude=True,
    ):
        """Delegate to superclass if database is open otherwise do nothing."""
        # Intend to put this in superclass but must treat the DataClient
        # objects being scrolled as a database to do this properly.  Do this
        # when these objects have been given a database interface used when
        # the database is not open.  (One problem is how to deal with indexes.)

        # Used to deal with temporary closure of database to do Imports of
        # games from PGN files; which can take many hours.

        if self.get_database() is not None:
            super().fill_view(
                currentkey=currentkey,
                down=down,
                topstart=topstart,
                exclude=exclude,
            )

    def load_new_index(self):
        """Delegate to superclass if database is open otherwise do nothing."""
        # Intend to put this in superclass but must treat the DataClient
        # objects being scrolled as a database to do this properly.  Do this
        # when these objects have been given a database interface used when
        # the database is not open.  (One problem is how to deal with indexes.)

        # Used to deal with temporary closure of database to do Imports of
        # games from PGN files; which can take many hours.

        if self.get_database() is not None:
            super().load_new_index()

    def load_new_partial_key(self, key):
        """Delegate to superclass if database is open otherwise do nothing."""
        # Intend to put this in superclass but must treat the DataClient
        # objects being scrolled as a database to do this properly.  Do this
        # when these objects have been given a database interface used when
        # the database is not open.  (One problem is how to deal with indexes.)

        # Used to deal with temporary closure of database to do Imports of
        # games from PGN files; which can take many hours.

        if self.get_database() is not None:
            super().load_new_partial_key(key)

    def on_configure_canvas(self, event=None):
        """Delegate to superclass if database is open otherwise do nothing."""
        # Intend to put this in superclass but must treat the DataClient
        # objects being scrolled as a database to do this properly.  Do this
        # when these objects have been given a database interface used when
        # the database is not open.  (One problem is how to deal with indexes.)

        # Used to deal with temporary closure of database to do Imports of
        # games from PGN files; which can take many hours.

        if self.get_database() is not None:
            super().on_configure_canvas(event=event)
            self._set_object_panel_item_properties()

    def on_data_change(self, instance):
        """Delegate to superclass if database is open otherwise do nothing."""
        # Intend to put this in superclass but must treat the DataClient
        # objects being scrolled as a database to do this properly.  Do this
        # when these objects have been given a database interface used when
        # the database is not open.  (One problem is how to deal with indexes.)

        # Used to deal with temporary closure of database to do Imports of
        # games from PGN files; which can take many hours.

        if self.get_database() is not None:
            super().on_data_change(instance)
            self._fill_view_from_top_hack()

    def is_payload_available(self):
        """Return True if grid is connected to a database."""
        data_source = self.get_data_source()
        if data_source is None:
            return False
        if data_source.get_database() is None:
            # Avoid exception scrolling visible grid not connected to database.
            # Make still just be hack to cope with user interface activity
            # while importing data.
            self.clear_grid_keys()

            return False
        return True

    def _set_event_bindings_frame(self, bindings=(), switch=True):
        """Set bindings if switch is True or unset the bindings."""
        ste = self.try_event
        frm = self.frame
        for sequence, function in bindings:
            self.bind(
                frm,
                sequence[0],
                function=ste(function) if switch and function else "",
            )

    def _set_grid_database(self, object_):
        """Do nothing: *ListGrid class is expected to override if needed."""

    def _set_object_panel_item_properties(self):
        """Do nothing: *ListGrid class is expected to override if needed."""

    def _fill_view_from_top_hack(self):
        """Do nothing: *ListGrid class is expected to override if needed."""

    def _configure_frame(self):
        self.gcanvas.configure(takefocus=tkinter.FALSE)
        self.data.configure(takefocus=tkinter.FALSE)
        self.frame.configure(takefocus=tkinter.FALSE)
        self.hsbar.configure(takefocus=tkinter.FALSE)
        self.vsbar.configure(takefocus=tkinter.FALSE)
