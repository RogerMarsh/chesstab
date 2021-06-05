# chessscoreboard.py
# Copyright 2021 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Demonstrate chess score class and methods to display PGN text and board."""

if __name__ == "__main__":

    import tkinter

    from pgn_read.core.parser import PGN

    from ..gui import fonts
    from ..gui.score import Score
    from ..gui.board import Board
    from .chessscore import DuckUI

    root = tkinter.Tk()
    root.wm_minsize(width=900, height=300)
    f = fonts.make_chess_fonts(root)
    root.wm_title("Demonstrate Score with Board")
    root.pack_propagate(False)

    # Use Board with DuckUI.
    ui = DuckUI(root)
    b = Board(root, ui=ui)
    b.get_top_widget().pack(fill=tkinter.BOTH, expand=tkinter.TRUE)
    b.get_top_widget().pack_propagate(False)
    s = Score(root, b)

    del b, ui, f
    s.collected_game = next(
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

    # This works, but set_and_tag_item_text is the method used normally.
    # The tkinter.Text widget must get configured 'state="disabled"' somewhere
    # because get_keypress_suppression_events is not called anywhere in
    # chesstab.  (Ah! set_and_tag_item_text).
    # s.map_game()
    # s.set_event_bindings_score(s.get_keypress_suppression_events())
    # s.bind_for_move()
    s.set_and_tag_item_text()

    # s.score is not in any container, except root, so use directly for focus
    # and geometry.
    # The get_top_widget method and takefocus_widget attribute are defined in
    # Game class to keep them out of AnalysisScore instances.
    s.score.pack(fill=tkinter.BOTH, expand=tkinter.TRUE)
    s.score.pack_propagate(False)
    s.score.focus_set()
    del s

    root.mainloop()
