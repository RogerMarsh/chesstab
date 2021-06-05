# colourscheme.py
# Copyright 2009 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""A chess board colour scheme chooser.
"""

import tkinter
import tkinter.font

from solentware_misc.gui.colourslider import ColourSlider
from solentware_misc.gui.exceptionhandler import ExceptionHandler

from pgn_read.core.parser import PGN

from . import constants, fonts, options
from . import game, board


class _ColourScheme(ExceptionHandler):

    """Widgets to select fonts and colours for chess board and game score.

    Use the subclasses defined in this module depending on what fits on
    the screen.

    """

    def __init__(self, ui=None, height=500, title="Style", **kargs):
        """Create Toplevel and fonts to be modified.

        ui is the ChessUI instance
        height - passed to Tkinter.Toplevel.
        title - use is w.wm_title(title).

        """
        self.ui = ui
        tags = ui.tags_variations_comments_font
        moves = ui.moves_played_in_game_font
        pieces = ui.boardfont
        self.ok = False
        if tags:
            self.tags_variations_comments_font = tags.copy()
        else:
            self.tags_variations_comments_font = tkinter.font.nametofont(
                constants.TAGS_VARIATIONS_COMMENTS_FONT
            ).copy()
        if moves:
            self.moves_played_in_game_font = moves.copy()
        else:
            self.moves_played_in_game_font = tkinter.font.nametofont(
                constants.MOVES_PLAYED_IN_GAME_FONT
            ).copy()
        if pieces:
            self.boardfont = pieces.copy()
        else:
            self.boardfont = tkinter.font.nametofont(
                constants.PIECES_ON_BOARD_FONT
            ).copy()
        # Wildpieces font is based on moves font but managed like boardfont
        if moves:
            self.wildpiecesfont = moves.copy()
        else:
            self.wildpiecesfont = tkinter.font.nametofont(
                constants.WILDPIECES_ON_BOARD_FONT
            ).copy()
        self.chooser = tkinter.Toplevel(height=height, width=700)
        self.chooser.wm_resizable(False, False)
        self.chooser.wm_title(title)
        self.chooser.pack_propagate(False)

    def apply_modified_font(self, modifiedfont, font):
        """Copy modifiedfont attributes to font."""
        if self.is_ok():
            fonts.copy_font_attributes(modifiedfont.actual(), font)

    def apply_modified_board_font(self, modifiedfont, font):
        """Copy modifiedfont attributes to board font."""
        if self.is_ok():
            fonts.copy_board_font_attributes(modifiedfont.actual(), font)

    def apply_pieces_on_board_font_to_font(self, font):
        """Copy self.boardfont attributes to board font."""
        self.apply_modified_board_font(self.boardfont, font)

    def apply_to_named_fonts(self):
        """Apply modified fonts to all displayed games."""
        self.apply_to_named_font_moves_played_in_game()
        self.apply_to_named_font_pieces_on_board()
        self.apply_to_named_font_wildpieces_on_board()
        self.apply_to_named_font_tags_variations_comments()

    def apply_to_named_font_moves_played_in_game(self):
        """Apply moves played font to all displayed games."""
        self.apply_modified_font(
            self.moves_played_in_game_font,
            tkinter.font.nametofont(constants.MOVES_PLAYED_IN_GAME_FONT),
        )

    def apply_to_named_font_pieces_on_board(self):
        """Apply pieces font to all displayed games."""
        self.apply_modified_board_font(
            self.boardfont,
            tkinter.font.nametofont(constants.PIECES_ON_BOARD_FONT),
        )

    def apply_to_named_font_tags_variations_comments(self):
        """Apply variations and comments font to all displayed games."""
        self.apply_modified_font(
            self.tags_variations_comments_font,
            tkinter.font.nametofont(constants.TAGS_VARIATIONS_COMMENTS_FONT),
        )

    def apply_to_named_font_wildpieces_on_board(self):
        """Apply wildpieces font to all displayed games."""
        self.apply_modified_board_font(
            self.wildpiecesfont,
            tkinter.font.nametofont(constants.WILDPIECES_ON_BOARD_FONT),
        )

    def get_button_definitions(self):
        """Return button definitions."""
        return (
            ("OK", "OK button Tooltip.", True, -1, self.on_ok),
            ("Cancel", "Cancel button Tooltip.", True, 2, self.on_cancel),
        )

    def create_buttons(self, buttons):
        """Create buttons."""
        self.buttons_frame = tkinter.Frame(master=self.chooser)
        self.buttons_frame.pack(side=tkinter.BOTTOM, fill=tkinter.X)
        buttonrow = self.buttons_frame.pack_info()["side"] in ("top", "bottom")
        for i, b in enumerate(buttons):
            button = tkinter.Button(
                master=self.buttons_frame,
                text=buttons[i][0],
                underline=buttons[i][3],
                command=self.try_command(buttons[i][4], self.buttons_frame),
            )
            if buttonrow:
                self.buttons_frame.grid_columnconfigure(i * 2, weight=1)
                button.grid_configure(column=i * 2 + 1, row=0)
            else:
                self.buttons_frame.grid_rowconfigure(i * 2, weight=1)
                button.grid_configure(row=i * 2 + 1, column=0)
        if buttonrow:
            self.buttons_frame.grid_columnconfigure(len(buttons * 2), weight=1)
        else:
            self.buttons_frame.grid_rowconfigure(len(buttons * 2), weight=1)

    def create_colour_frame(self):
        """Create colour selector widgets."""
        colour_frame = tkinter.Frame(master=self.chooser)
        colour_frame.pack(fill=tkinter.X)
        gs = self.game.score
        gb = self.game.board
        for row, label, color, setter in (
            (0, "Light squares", gb.litecolor, self.set_lite_square_bgcolour),
            (1, "Dark squares", gb.darkcolor, self.set_dark_square_bgcolour),
            (2, "White pieces", gb.whitecolor, self.set_white_piece_fgcolour),
            (3, "Black pieces", gb.blackcolor, self.set_black_piece_fgcolour),
            (4, "Rest of line", self.game.l_color, self.set_tag_rest_of_line),
            (5, "Move", self.game.m_color, self.set_tag_move),
            (6, "Alternatives", self.game.am_color, self.set_tag_alternatives),
            (
                7,
                "Start of line",
                self.game.v_color,
                self.set_tag_start_of_line,
            ),
        ):
            ChessColourSlider(
                colour_frame,
                row=row,
                colour=color,
                label=label,
                TagConfigureBGcolour=setter,
            )

    def create_font_frame(self):
        """Create font selection widget."""

        def focus(w):
            def fs(e=None):
                w.focus_set()

            return fs

        font_frame = tkinter.Frame(master=self.chooser)
        font_frame.pack(fill=tkinter.X)
        # font chooser for board
        font_frame.columnconfigure(0, weight=1, uniform="fontpanels")
        tkinter.Label(master=font_frame, text="Pieces").grid_configure(
            row=0, column=0
        )
        fontfr = tkinter.Frame(master=font_frame, padx=5)
        fr = tkinter.Frame(master=fontfr)
        self.b_families = tkinter.Listbox(fr)
        scrollfont = tkinter.Scrollbar(fr)
        scrollfont.configure(
            command=self.try_command(self.b_families.yview, scrollfont)
        )
        self.b_families.configure(yscrollcommand=scrollfont.set)
        for f in sorted(tkinter.font.families()):
            self.b_families.insert(tkinter.END, f)
        self.b_families.pack(
            side=tkinter.LEFT, expand=tkinter.TRUE, fill=tkinter.Y
        )
        scrollfont.pack(side=tkinter.LEFT, fill=tkinter.Y)
        fr.pack(fill=tkinter.Y, expand=tkinter.TRUE)
        wssf = tkinter.Frame(master=fontfr)
        self.b_family = tkinter.Label(
            master=wssf, text=self.boardfont["family"]
        )
        self.b_family.grid_configure(column=0, row=1, sticky=tkinter.EW)
        self.b_weight = tkinter.IntVar()
        cb = tkinter.Checkbutton(
            master=wssf,
            text="Bold",
            variable=self.b_weight,
            command=self.try_command(self.set_board_font_weight, wssf),
            indicatoron=tkinter.FALSE,
        )
        cb.grid_configure(column=0, row=3, sticky=tkinter.EW)
        cb.bind("<ButtonPress>", self.try_event(focus(cb)))
        self.b_weight.set(tkinter.TRUE)
        wssf.grid_columnconfigure(0, weight=1)
        wssf.grid_rowconfigure(0, minsize=5)
        wssf.grid_rowconfigure(2, minsize=5)
        wssf.grid_rowconfigure(4, minsize=5)
        wssf.pack(fill=tkinter.X)
        fontfr.grid_configure(row=1, column=0, sticky=tkinter.NS)
        self.b_families.bind(
            "<<ListboxSelect>>", self.try_event(self.set_board_font_family)
        )
        # font chooser for score
        font_frame.columnconfigure(1, weight=2, uniform="fontpanels")
        tkinter.Label(master=font_frame, text="Score").grid_configure(
            row=0, column=1
        )
        fontfr = tkinter.Frame(master=font_frame, padx=5)
        fr = tkinter.Frame(master=fontfr)
        self.s_families = tkinter.Listbox(fr)
        scrollfont = tkinter.Scrollbar(fr)
        scrollfont.configure(
            command=self.try_command(self.s_families.yview, scrollfont)
        )
        self.s_families.configure(yscrollcommand=scrollfont.set)
        for f in sorted(tkinter.font.families()):
            self.s_families.insert(tkinter.END, f)
        self.s_families.pack(
            side=tkinter.LEFT, expand=tkinter.TRUE, fill=tkinter.X
        )
        scrollfont.pack(side=tkinter.LEFT, fill=tkinter.Y)
        fr.pack()
        wssf = tkinter.Frame(master=fontfr)
        self.s_family = tkinter.Label(
            master=wssf, text=self.tags_variations_comments_font["family"]
        )
        self.s_family.grid_configure(
            column=1, row=1, sticky=tkinter.EW, columnspan=3
        )
        self.s_weight = tkinter.IntVar()
        self._make_font_selector(
            wssf, "Bold:", self.s_weight, 3, self.set_score_font_weight
        )
        self.s_weight.set(self.get_combination("weight", tkinter.font.BOLD))
        self.s_slant = tkinter.IntVar()
        self._make_font_selector(
            wssf, "Italic:", self.s_slant, 6, self.set_score_font_slant
        )
        self.s_slant.set(self.get_combination("slant", tkinter.font.ITALIC))
        wssf.grid_rowconfigure(0, minsize=5)
        wssf.grid_rowconfigure(2, minsize=5)
        wssf.grid_rowconfigure(5, minsize=5)
        wssf.grid_rowconfigure(8, minsize=5)
        wssf.grid_rowconfigure(10, minsize=5)
        wssf.grid_columnconfigure(1, weight=1, uniform="swght")
        wssf.grid_columnconfigure(2, weight=1, uniform="swght")
        wssf.grid_columnconfigure(3, weight=1, uniform="swght")
        self.s_size = tkinter.IntVar()
        tkinter.Label(master=wssf, text="Size:").grid_configure(
            column=0, row=9
        )
        sf = tkinter.Frame(master=wssf)
        fsize = self.tags_variations_comments_font.cget("size")
        sf.grid_configure(column=1, row=9, columnspan=3, sticky=tkinter.EW)
        for i, s in enumerate((7, 8, 9, 10, 11, 12, 13, 14, 16, 18, 20)):
            sb = tkinter.Radiobutton(
                master=sf,
                text=str(s),
                variable=self.s_size,
                value=s,
                indicatoron=tkinter.FALSE,
                command=self.try_command(self.set_score_font_size, sf),
            )
            if s == abs(fsize):
                self.s_size.set(s)
            sb.grid_configure(column=i + 1, row=0, sticky=tkinter.EW)
            sf.grid_columnconfigure(i + 1, weight=1, uniform="fsb")
            sb.bind("<ButtonPress>", self.try_event(focus(sb)))
        wssf.pack(fill=tkinter.X)
        fontfr.grid_configure(row=1, column=1)
        self.s_families.bind(
            "<<ListboxSelect>>", self.try_event(self.set_score_font_family)
        )

    def create_game_frame(self):
        """Create sample game for demostrating fonts and colours."""
        self.game = game.Game(
            self.chooser,
            ui=self.ui,
            boardfont=self.boardfont,
            tags_variations_comments_font=self.tags_variations_comments_font,
            moves_played_in_game_font=self.moves_played_in_game_font,
        )

        def focus(event=None):
            self.game.score.focus_set()

        self.game.score.bind("<ButtonPress>", self.try_event(focus))
        gs = "".join(
            (
                '[Event"National Club: Gosport - Wood Green"]',
                '[Site"Gosport"]',
                '[Date"1989-05-07"]',
                '[Round"QFinal"]',
                '[White"Sowray P J"]',
                '[Black"Marsh R"]',
                '[Result"1-0"]',
                "e4c6d4d5exd5cxd5c4Nf6c5(Nf3)(Nc3)e6Nc3b6b4a5Bf4axb4Nb5Na6Qa4Bd7",
                "Bc7Nxc5Qd1Qc8dxc5bxc5Nf3Qb7Nd6Bxd6Bxd6Qb6Be5Ke7Be2Ne4O-Of6Bb2Nc3",
                "{A comment\non two lines}",
                "Bxc3bxc3Qd3(Qb3)Ra3Rfb1Qa7Qc2g6Rb3d4Bc4Rxb3Bxb3Qa6a4Rb8a5e5Bd5Rb2",
                "Qe4Bf5Qh4Qd3(c2(g5)Nd2Qxa5Rxa5Rb1Nf1Rxf1Kxf1Bd3)g4Rb1Rxb1Qxb1Kg2",
                "Kd6Qxf6Kxd5Qxe5Kc6gxf5Qxf5Qe8Kc7Qe7Kc8Ne5c2Qxc5Kd8Qxd4Ke8Qe3Kf8",
                "Kg3Qc8Nd3Kg8f4Qc6Nc1Qa4Qb31-0",
                "\n",
            )
        )
        self.game.collected_game = next(PGN().read_games(gs))
        self.game.set_and_tag_item_text()
        self.game.get_top_widget().pack(fill=tkinter.BOTH, expand=1)
        self.game.get_top_widget().pack_propagate(False)

    def get_options(self):
        """Return (olddefaults, newdefaults) colours."""
        cg = game.Game
        cb = board.Board
        olddefaults = {
            constants.LITECOLOR_NAME: cb.litecolor,
            constants.DARKCOLOR_NAME: cb.darkcolor,
            constants.WHITECOLOR_NAME: cb.whitecolor,
            constants.BLACKCOLOR_NAME: cb.blackcolor,
            constants.LINE_COLOR_NAME: cg.l_color,
            constants.MOVE_COLOR_NAME: cg.m_color,
            constants.ALTERNATIVE_MOVE_COLOR_NAME: cg.am_color,
            constants.VARIATION_COLOR_NAME: cg.v_color,
        }
        for fn in options.font_names:
            olddefaults[fn] = dict()
        fonts.copy_font_attributes(
            tkinter.font.nametofont(
                constants.MOVES_PLAYED_IN_GAME_FONT
            ).actual(),
            olddefaults[constants.MOVES_PLAYED_IN_GAME_FONT],
        )
        fonts.copy_font_attributes(
            tkinter.font.nametofont(
                constants.TAGS_VARIATIONS_COMMENTS_FONT
            ).actual(),
            olddefaults[constants.TAGS_VARIATIONS_COMMENTS_FONT],
        )
        fonts.copy_board_font_attributes(
            tkinter.font.nametofont(constants.PIECES_ON_BOARD_FONT).actual(),
            olddefaults[constants.PIECES_ON_BOARD_FONT],
        )
        fonts.copy_board_font_attributes(
            tkinter.font.nametofont(
                constants.WILDPIECES_ON_BOARD_FONT
            ).actual(),
            olddefaults[constants.WILDPIECES_ON_BOARD_FONT],
        )
        newdefaults = {
            constants.LITECOLOR_NAME: self.game.board.litecolor,
            constants.DARKCOLOR_NAME: self.game.board.darkcolor,
            constants.WHITECOLOR_NAME: self.game.board.whitecolor,
            constants.BLACKCOLOR_NAME: self.game.board.blackcolor,
            constants.LINE_COLOR_NAME: self.game.l_color,
            constants.MOVE_COLOR_NAME: self.game.m_color,
            constants.ALTERNATIVE_MOVE_COLOR_NAME: self.game.am_color,
            constants.VARIATION_COLOR_NAME: self.game.v_color,
        }
        for fn in options.font_names:
            newdefaults[fn] = dict()
        fonts.copy_font_attributes(
            self.tags_variations_comments_font.actual(),
            newdefaults[constants.TAGS_VARIATIONS_COMMENTS_FONT],
        )
        fonts.copy_font_attributes(
            self.moves_played_in_game_font.actual(),
            newdefaults[constants.MOVES_PLAYED_IN_GAME_FONT],
        )
        fonts.copy_board_font_attributes(
            self.boardfont.actual(),
            newdefaults[constants.PIECES_ON_BOARD_FONT],
        )
        fonts.copy_board_font_attributes(
            self.wildpiecesfont.actual(),
            newdefaults[constants.WILDPIECES_ON_BOARD_FONT],
        )
        return olddefaults, newdefaults

    def get_combination(self, option, value):
        tvc = self.tags_variations_comments_font[option] == value
        m = self.moves_played_in_game_font[option] == value
        if tvc:
            if m:
                return 2
            else:
                return 4
        elif m:
            return 1
        else:
            return 3

    def is_ok(self):
        """Returns True if dialogue closed using Ok button."""
        return self.ok

    def on_cancel(self, event=None):
        """Process Cancel button event."""
        self.ok = False
        self.restore_focus.focus_set()
        self.chooser.destroy()

    def on_ok(self, event=None):
        """Process Ok button event."""
        self.ok = True
        self.restore_focus.focus_set()
        self.chooser.destroy()

    def modal_dialogue(self):
        """Display widget as a modal dialogue.

        Activate game navigation so fonts and colours can be seen in game
        context.

        """
        self.restore_focus = self.chooser.focus_get()
        self.chooser.wait_visibility()
        self.chooser.grab_set()
        self.chooser.wait_window()

    def set_board_font_family(self, event=None):
        """Set sample game board family."""
        f = self.b_families
        self.boardfont["family"] = f.get(f.curselection()[0])
        self.game.board.font["family"] = f.get(f.curselection()[0])
        self.b_family["text"] = f.get(f.curselection()[0])

    def set_board_font_weight(self):
        """Set sample game board pieces font."""
        w = {0: "normal", 1: "bold"}
        bfweight = w[self.b_weight.get()]
        self.boardfont["weight"] = bfweight
        self.game.board.font["weight"] = bfweight

    def set_lite_square_bgcolour(self, colour):
        """Set light squares to colour."""
        self.game.board.litecolor = colour
        self.game.board.set_color_scheme()

    def set_dark_square_bgcolour(self, colour):
        """Set dark squares to colour."""
        self.game.board.darkcolor = colour
        self.game.board.set_color_scheme()

    def set_white_piece_fgcolour(self, colour):
        """Set white pieces to colour."""
        self.game.board.whitecolor = colour
        self.game.board.draw_board()

    def set_black_piece_fgcolour(self, colour):
        """Set black pieces to colour."""
        self.game.board.blackcolor = colour
        self.game.board.draw_board()

    def set_tag_rest_of_line(self, colour):
        """Set moves following current move in line to colour."""
        self.game.l_color = colour
        self.game.score.tag_configure("l_color", background=colour)

    def set_tag_move(self, colour):
        """Set current move to colour."""
        self.game.m_color = colour
        self.game.score.tag_configure("m_color", background=colour)

    def set_tag_alternatives(self, colour):
        """Set alternatives to selected next move to colour."""
        self.game.am_color = colour
        self.game.score.tag_configure("am_color", background=colour)

    def set_tag_start_of_line(self, colour):
        """Set moves preceeding current move in line to colour."""
        self.game.v_color = colour
        self.game.score.tag_configure("v_color", background=colour)

    def set_score_font_family(self, event=None):
        """Set game score and variation font family."""
        f = self.s_families
        self.tags_variations_comments_font["family"] = f.get(
            f.curselection()[0]
        )
        self.moves_played_in_game_font["family"] = f.get(f.curselection()[0])
        self.wildpiecesfont["family"] = f.get(f.curselection()[0])
        self.s_family["text"] = f.get(f.curselection()[0])

    def set_score_font_size(self):
        """Set game score and variation font size to selected size."""
        self.tags_variations_comments_font["size"] = -self.s_size.get()
        self.moves_played_in_game_font["size"] = -self.s_size.get()

    def set_score_font_slant(self):
        """Set game score and variation font slants to selected slants."""
        s = {
            4: ("italic", "roman"),
            2: ("italic", "italic"),
            3: ("roman", "roman"),
            1: ("roman", "italic"),
        }
        tvcfslant, mfslant = s[self.s_slant.get()]
        self.tags_variations_comments_font["slant"] = tvcfslant
        self.moves_played_in_game_font["slant"] = mfslant

    def set_score_font_weight(self):
        """Set game score and variation font weights to selected weights."""
        w = {
            4: ("bold", "normal"),
            2: ("bold", "bold"),
            3: ("normal", "normal"),
            1: ("normal", "bold"),
        }
        tvcfweight, mfweight = w[self.s_weight.get()]
        self.tags_variations_comments_font["weight"] = tvcfweight
        self.moves_played_in_game_font["weight"] = mfweight

    def __del__(self):
        """Force IsOk to return False after destructor call."""
        self.ok = False

    def _make_font_selector(self, frame, title, variable, baserow, command):
        """Create a font selector."""
        tkinter.Label(master=frame, text=title).grid_configure(
            column=0, row=baserow
        )

        def focus(w):
            def fs(e=None):
                w.focus_set()

            return fs

        for i, t in (
            (1, "Moves Played"),
            (2, "All"),
            (3, "None"),
        ):
            rb = tkinter.Radiobutton(
                master=frame,
                text=t,
                variable=variable,
                value=i,
                command=self.try_command(command, frame),
                indicatoron=tkinter.FALSE,
            )
            rb.grid_configure(column=i, row=baserow, sticky=tkinter.EW)
            rb.bind("<ButtonPress>", self.try_event(focus(rb)))
        rb = tkinter.Radiobutton(
            master=frame,
            text="Tags Variations Comments",
            variable=variable,
            value=4,
            command=self.try_command(command, frame),
            indicatoron=tkinter.FALSE,
        )
        rb.grid_configure(
            column=1, row=baserow + 1, columnspan=3, sticky=tkinter.EW
        )
        rb.bind("<ButtonPress>", self.try_event(focus(rb)))


class ColourChooser(_ColourScheme):

    """Create a colour selection widget.

    Use this widget on screens up to 950 pixels high.

    """

    def __init__(self, **ka):
        """Extend to create a widget containing just the colour selectors.

        **ka
        ui is the ChessUI instance
        moves tags and pieces are fonts to be used as basis for modified fonts.

        """
        super(ColourChooser, self).__init__(
            height=660, title="Chessboard colour chooser", **ka
        )
        self.create_game_frame()
        self.create_colour_frame()
        self.create_buttons(self.get_button_definitions())
        self.modal_dialogue()


class FontChooser(_ColourScheme):

    """Create a font selection widget.

    Use this widget on screens up to 950 pixels high.

    """

    def __init__(self, **ka):
        """Extend to create a widget containing just the font selectors.

        **ka
        ui is the ChessUI instance
        moves tags and pieces are fonts to be used as basis for modified fonts.

        """
        super(FontChooser, self).__init__(
            height=680, title="Chessboard font chooser", **ka
        )
        self.create_font_frame()
        self.create_game_frame()
        self.create_buttons(self.get_button_definitions())
        self.modal_dialogue()


class FontColourChooser(_ColourScheme):

    """Create a font and colour selection widget.

    Use this widget on screens over 950 pixels high.

    """

    def __init__(self, **ka):
        """Extend to create a widget containing font and colour selectors.

        **ka
        ui is the ChessUI instance
        moves tags and pieces are fonts to be used as basis for modified fonts.

        """
        super(FontColourChooser, self).__init__(
            height=950, title="Chessboard style chooser", **ka
        )
        self.create_font_frame()
        self.create_game_frame()
        self.create_colour_frame()
        self.create_buttons(self.get_button_definitions())
        self.modal_dialogue()


class ChessColourSlider(ColourSlider):

    """Create colour selection widget containing Red Green and Blue sliders."""

    def __init__(
        self,
        master=None,
        row=None,
        label="",
        resolution=2,
        colour="grey",
        TagConfigureBGcolour=None,
    ):
        """Extend with callback to attach a colour to a Text tag."""
        super(ChessColourSlider, self).__init__(
            master=master,
            row=row,
            label=label,
            resolution=resolution,
            colour=colour,
        )
        self.TagConfigureBGcolour = TagConfigureBGcolour

    def delta_red_colour(self, event=None):
        """Extend to attach colour to Text tag after change to Red."""
        super(ChessColourSlider, self).delta_red_colour(event=event)
        self.TagConfigureBGcolour(self.get_colour())

    def set_red_colour(self, event=None):
        """Extend to attach colour to Text tag after setting Red."""
        super(ChessColourSlider, self).set_red_colour(event=event)
        self.TagConfigureBGcolour(self.get_colour())

    def delta_green_colour(self, event=None):
        """Extend to attach colour to Text tag after change to Green."""
        super(ChessColourSlider, self).delta_green_colour(event=event)
        self.TagConfigureBGcolour(self.get_colour())

    def set_green_colour(self, event=None):
        """Extend to attach colour to Text tag after setting Green."""
        super(ChessColourSlider, self).set_green_colour(event=event)
        self.TagConfigureBGcolour(self.get_colour())

    def delta_blue_colour(self, event=None):
        """Extend to attach colour to Text tag after change to Blue."""
        super(ChessColourSlider, self).delta_blue_colour(event=event)
        self.TagConfigureBGcolour(self.get_colour())

    def set_blue_colour(self, event=None):
        """Extend to attach colour to Text tag after setting Blue."""
        super(ChessColourSlider, self).set_blue_colour(event=event)
        self.TagConfigureBGcolour(self.get_colour())
