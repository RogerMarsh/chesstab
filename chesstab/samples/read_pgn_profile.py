# read_pgn_profile.py
# Copyright 2018 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Read a PGN file and display timing profile."""

import cProfile, pstats, io
import tkinter

from pgn_read.samples import _utilities

from ..core.pgn import GameUpdate


class Main(_utilities.Main):
    def process_pgn_file(self, event=None):
        """Process PGN file."""
        pr = cProfile.Profile()
        pr.enable()
        super().process_pgn_file(event=event)
        pr.disable()
        s = io.StringIO()
        ps = pstats.Stats(pr, stream=s).sort_stats("cumulative")
        ps.print_stats()
        self.insert_text("\nProfile report\n\n")
        self.insert_text(s.getvalue())
        self.root.wm_resizable(width=tkinter.TRUE, height=tkinter.TRUE)
        self.root.columnconfigure(0, weight=1)
        self.text.pack(expand=tkinter.TRUE, fill=tkinter.BOTH)


if __name__ == "__main__":

    Main(
        game_class=GameUpdate,
        samples_title="Sample ChessTab Update Profile Report",
    ).root.mainloop()
