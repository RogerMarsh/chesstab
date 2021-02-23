# analysis.py
# Copyright 2015 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Chess engine analysis for a position.
"""

import sys

from pgn_read.core.constants import (
    FEN_WHITE_ACTIVE,
    FEN_BLACK_ACTIVE,
    )

from .constants import (
    UNKNOWN_RESULT,
    START_RAV,
    END_RAV,
    START_COMMENT,
    END_COMMENT,
    START_EOL_COMMENT,
    FEN_CONTEXT,
    )

_EOL_COMMENT_CONTEXT = (START_EOL_COMMENT, '\n')


class Analysis(object):
    """Chess engine analysis for FEN position.

    Store variations generated by chess engines for a position.

    """

    def __init__(self, position=None):
        """Note position to be analysed."""
        super().__init__()

        # Position encoded as index value for position index.
        self.position = position

        # Variations generated by chess engines:
        # key is engine name reported by chess engine when started,
        # value is ((evaluation, PGN of variation), ...) sorted by evaluation.
        # len(value) is multiPV option value used to do analysis.
        self.variations = {}

        # Depth and width of analysis by chess engine
        # key is engine name reported by chess engine when started,
        # value is (depth, multiPV) option values used to do analysis.
        self.scale = {}

    def set_variations_empty(self):
        """Set all variations to None.

        len(variations[engine] is the multiPV value used when analysis done.
        Set variations to None to preserve the multiPV information when a new
        analysis request is done, while noting any analysis deemed necessary
        is not yet done.

        """
        var = self.variations
        for k, v in var.items():
            var[k] = [None] * len(v)

    # Rewrite of pgn_read in 2020 forced inclusion of SetUp tag in analysis
    # PGN text: probably best to find a way of avoiding this.
    def translate_analysis_to_pgn(self, move_played=''):
        """Translate UCI chess engine variation output to PGN."""

        # Addition of this code tips balance in favour of a class to deal with
        # FEN representation of positions.
        to_move = self.position.split()[1]
        
        if move_played:
            move_played = ''.join(
                (move_played,
                 ' ;Move played',
                 ' by white' if to_move == FEN_WHITE_ACTIVE else
                 ' by black' if to_move == FEN_BLACK_ACTIVE else
                 '',
                 '\n'))
        variations = self.variations
        scale = self.scale
        new_text = []
        for engine_name in sorted(variations):

            # The following stopped happening after the test database was
            # deleted and re-created, so maybe everything is sound and the
            # problem is left-over from earlier testing.
            #
            # This may happen if communication with a remote engine is lost
            # and then re-established by 'quit engine' and 'start engine' menu
            # actions, or perhaps if the process driving a local engine fails
            # too.  It has been seen only for the position on display in the
            # active window at the time these actions are done while the
            # database is open.
            # The sequence of actions is:
            # Start a remote UCI server and open a database in either order.
            # Use the Engine menu to start a UCI client for the UCI server.
            # Close the database (so no analysis get written to database).
            # Use the Game menu to start a new game and see analysis appear.
            # Stop the remote UCI server (action on the remote host).
            # Start a remote UCI server.
            # Open a database.
            # Use the Engine menu to start a UCI client for the UCI server.
            # Now closing and opening the database switches it off and on.
            #if engine_name is None:
            #    sys.stderr.write(
            #        'Name of engine: ' + str(engine_name) + ' ' + str(len(variations)) + '\n')
            #    continue

            analysis = variations[engine_name]

            # Keep going as normal for non-str engine_name (should not happen).
            #new_text.append(engine_name.join((';', '\n')))
            new_text.append(str(engine_name).join(_EOL_COMMENT_CONTEXT))

            depth, multipv = [str(s) for s in scale[engine_name]]
            lines = [''.join((' '.join((START_COMMENT,
                                        self._evalution_score(a[0], to_move),
                                        depth,
                                        str(e + 1),
                                        ' '.join((END_COMMENT, START_RAV)))),
                              a[1],
                              END_RAV,
                              '\n'))
                     for e, a in enumerate(analysis)]
            new_text.extend(lines)
            if not move_played:
                move_played = ''.join(
                    (analysis[0][1].split()[0],
                     ' ',
                     ''.join((
                         'First variation',
                         ', white to move' if to_move == FEN_WHITE_ACTIVE else
                         ', black to move' if to_move == FEN_BLACK_ACTIVE else
                         '')).join(_EOL_COMMENT_CONTEXT),
                     ))
        new_text.append(UNKNOWN_RESULT)
        if move_played:
            new_text.insert(0, move_played)
            new_text.insert(0, self.position.join(FEN_CONTEXT))
        return ''.join(new_text)

    def _evalution_score(self, val, to_move):
        """Normalize to white advantage is positive and black negative."""
        try:
            return '{:+.2f}'.format(
                (int(val) if to_move != FEN_BLACK_ACTIVE else -int(val)) / 100)
        except:
            return '?.??'
