# chessgame.py
# Copyright 2021 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Demonstrate chess game class and methods to display PGN text, board, and
analysis as it appears without an active chess engine."""

if __name__ == "__main__":

    import tkinter

    from pgn_read.core.parser import PGN

    from ..gui import fonts
    from ..gui.game import Game
    from .chessscore import DuckUI

    class DuckStatusbar:
        """Helper to allow Game instances to work without a real UI."""

        def set_status_text(self, *a, **k):
            pass

    class DuckqueueQueue:
        """Helper to allow Game instances to work without a real UI."""

        def put(self, *a):
            pass

    class DuckcoreuciUCI:
        """Helper to allow Game instances to work without a real UI."""

        ui_analysis_queue = DuckqueueQueue()
        position_analysis = {}

    class DuckguiuciUCI:
        """Helper to allow Game instances to work without a real UI."""

        uci = DuckcoreuciUCI()

    class DuckUI(DuckUI):
        """Helper to allow Game instances to work without a real UI."""

        show_analysis = True
        visible_scrollbars = True

        # None is legal but the default analysis does not get shown in the
        # analysis widget.
        database = False

        def make_position_analysis_data_source(self):
            return None

        statusbar = DuckStatusbar()
        uci = DuckguiuciUCI()

    # Maybe the real generate_popup_navigation_maps can be declared somewhere
    # else, even if duplicated, to avoid this.
    # An empty Navigation entry is put in the popup menu.
    class Game(Game):
        binding_labels = ()

        def generate_popup_navigation_maps(self):
            return {}, {}

    root = tkinter.Tk()
    root.wm_minsize(width=900, height=600)
    f = fonts.make_chess_fonts(root)
    root.wm_title("Demonstrate Game")
    root.pack_propagate(False)

    # Use DuckUI.
    g = Game(master=root, ui=DuckUI(root))

    del f
    g.collected_game = next(
        PGN().read_games(
            "".join(
                (
                    '[Event"National Club: Gosport - Wood Green"]',
                    '[Site"Gosport"]',
                    '[Date"1989-05-07"]',
                    '[Round"QFinal"]',
                    '[White"Sowray P J"]',
                    '[Black"Marsh R"]',
                    '[Result"1-0"]',
                    "e4(d4d5c4e6Nc3)c6d4d5exd5cxd5c4Nf6c5e6Nc3b6b4a5Bf4",
                    "axb4Nb5Na6Qa4;comment to eol\nBd7",
                    "Bc7Nxc5Qd1Qc8dxc5bxc5Nf3Qb7Nd6Bxd6Bxd6Qb6Be5Ke7Be2Ne4O-Of6Bb2Nc3",
                    "Bxc3bxc3Qd3(Qb3)Ra3Rfb1Qa7Qc2g6Rb3d4Bc4Rxb3Bxb3Qa6a4Rb8a5e5Bd5",
                    "\n%The escape sequence\nRb2",
                    "Qe4Bf5Qh4Qd3(c2(g5)Nd2Qxa5Rxa5Rb1{Comment\ncontaining newline}Nf1",
                    "(Nxb1c1=Q)Rxf1Kxf1Bd3)g4Rb1",
                    "Rxb1Qxb1Kg2Kd6Qxf6Kxd5<reserved\n\nfor future use>Qxe5",
                    "Kc6gxf5Qxf5Qe8Kc7Qe7Kc8Ne5c2Qxc5Kd8Qxd4",
                    "Ke8Qe3Kf8Kg3Qc8Nd3Kg8f4Qc6Nc1Qa4Qb3",
                    "1-0",
                    "\n",
                )
            )
        )
    )

    g.set_and_tag_item_text()

    # The get_top_widget method and takefocus_widget attribute are defined in
    # Game class to keep them out of AnalysisScore instances.
    g.get_top_widget().pack(fill=tkinter.BOTH, expand=tkinter.TRUE)
    g.score.focus_set()
    del g

    root.mainloop()
