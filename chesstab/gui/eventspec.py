# eventspec.py
# Copyright 2015 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Map ChessTab event names to tk(inter) event detail values."""

# Some cases need an object with a widget attribute, but the source of the
# event does not provide an event object, let alone the relevant widget.
# Fortunately the required widget is always known in these cases.
import collections

DummyEvent = collections.namedtuple("DummyEvent", "widget")
del collections

# Mapped to widget focus setters and initialisers in all panels.
# Menu item label is same in all cases.
GAMES_PARTIAL_POSITION = "Games Partial Position"
ACTIVE_PARTIAL_POSITION = "Active Partial Position"
PARTIAL_POSITION_LIST = "Partial Position List"
GAMES_REPERTOIRE = "Games Repertoire"
ACTIVE_REPERTOIRE = "Active Repertoire"
REPERTOIRE_GAME_LIST = "Repertoire Game List"
GAMES_DATABASE = "Games Database"
POSITION_GAME_LIST = "Position Game List"
ACTIVE_GAME = "Active Game"
SELECTION_RULE_LIST = "Selection Rule List"
ACTIVE_SELECTION_RULE = "Active Selection Rule"

# Mapped to widget focus setters and initialisers in relevant panels.
# Menu item label is same in all cases.
PREVIOUS_REPERTOIRE = "Previous Repertoire"
NEXT_REPERTOIRE = "Next Repertoire"
REPERTOIRE = "Repertoire"
PREVIOUS_GAME = "Previous Game"
NEXT_GAME = "Next Game"
PREVIOUS_PARTIAL_POSITION = "Previous Partial Position"
NEXT_PARTIAL_POSITION = "Next Partial Position"
PREVIOUS_SELECTION_RULE = "Previous Selection Rule"
NEXT_SELECTION_RULE = "Next Selection Rule"


class EventSpec(object):
    """Event detail values for ChessTab keyboard and pointer actions."""

    # Navigate to another specific widget event specifications.  (Not next
    # widget in tab order or similar.)
    # When this class was introduced it was convenient name the events like
    # 'position_grid_to_partial_grid' and 'partial_game_grid_to_partial_grid',
    # though both were "('<KeyPress-F2>', PARTIAL_POSITION_LIST, 'F2')", to
    # avoid making mistakes.  Opportunity taken, when adding export events,
    # to replace these with 'navigate_to_partial_grid' names.
    navigate_to_active_game = ("<Alt-KeyPress-F9>", ACTIVE_GAME, "Alt F9")
    navigate_to_active_partial = (
        "<Alt-KeyPress-F2>",
        ACTIVE_PARTIAL_POSITION,
        "Alt F2",
    )
    navigate_to_active_repertoire = (
        "<Alt-KeyPress-F6>",
        ACTIVE_REPERTOIRE,
        "Alt F6",
    )
    navigate_to_active_selection_rule = (
        "<Alt-KeyPress-F3>",
        ACTIVE_SELECTION_RULE,
        "Alt F3",
    )
    navigate_to_game_grid = ("<KeyPress-F9>", GAMES_DATABASE, "F9")
    navigate_to_partial_game_grid = (
        "<Shift-KeyPress-F2>",
        GAMES_PARTIAL_POSITION,
        "Shift F2",
    )
    navigate_to_partial_grid = ("<KeyPress-F2>", PARTIAL_POSITION_LIST, "F2")
    navigate_to_position_grid = (
        "<Shift-KeyPress-F9>",
        POSITION_GAME_LIST,
        "Shift F9",
    )
    navigate_to_repertoire_game_grid = (
        "<Shift-KeyPress-F6>",
        GAMES_REPERTOIRE,
        "Shift F6",
    )
    navigate_to_repertoire_grid = ("<KeyPress-F6>", REPERTOIRE_GAME_LIST, "F6")
    navigate_to_selection_rule_grid = (
        "<KeyPress-F3>",
        SELECTION_RULE_LIST,
        "F3",
    )

    # All the grids have Display and Display allow edit options, with the same
    # prompt and keystrokes no matter the type of data.  The grids are
    # PartialPositionGames, GamePositionGames, TagRosterGrid, RepertoireGrid,
    # RepertoirePositionGames, PartialGrid, and SelectionGrid.
    display_record_from_grid = ("<KeyPress-F11>", "Display", "F11")
    edit_record_from_grid = (
        "<Control-KeyPress-F11>",
        "Display allow edit",
        "Ctrl F11",
    )

    # PartialGrid
    export_from_partial_grid = (
        "<Control-Alt-KeyPress-Home>",
        "Export",
        "Ctrl Alt Home",
    )

    # All the display, and edit, widgets have Insert, Delete, Update, and Make
    # Active options.  These event definitions replace those named for the
    # widget using them.
    # The Dismiss option is a plausible renaming of the Close options named
    # after the data in the widget.
    # Some have a List Games option.
    display_insert = ("<KeyPress-Insert>", "Insert", "Insert")
    display_delete = ("<KeyPress-Delete>", "Delete", "Delete")
    display_update = ("<Alt-KeyPress-Insert>", "Edit", "Alt Insert")
    display_dismiss = ("<Alt-KeyPress-F12>", "Close Item", "Alt F12")
    display_make_active = ("", "Make Active", "Left Click")
    display_dismiss_inactive = ("", "Close Item", "")
    display_list = ("<Control-KeyPress-Return>", "List Games", "Ctrl Enter")

    # Score widget, common to Game and Repertoire widgets.
    # Default lambda in Score.__init__ ignored.
    score_show_previous_in_variation = (
        "<Shift-KeyPress-Up>",
        "Previous Move Variation",
        "Shift Up",
    )
    score_show_previous_in_line = ("<KeyPress-Up>", "Previous Move", "Up")
    score_show_next_in_line = (
        "<Shift-KeyPress-Down>",
        "Next Move",
        "Shift Down",
    )
    score_show_next_in_variation = (
        "<KeyPress-Down>",
        "Next Move Select Variation",
        "Down",
    )
    score_show_first_in_line = (
        "<KeyPress-Prior>",
        "Start of Variation",
        "PageUp",
    )
    score_show_last_in_line = ("<KeyPress-Next>", "End of Variation", "PageDn")
    score_show_first_in_game = (
        "<Shift-KeyPress-Prior>",
        "Start of Game",
        "Shift PageUp",
    )
    score_show_last_in_game = (
        "<Shift-KeyPress-Next>",
        "End of Game",
        "Shift PageDn",
    )
    score_show_selected_variation = (
        "<Shift-KeyPress-Down>",
        "Enter Variation",
        "Shift Down",
    )
    score_cycle_selection_to_next_variation = (
        "<KeyPress-Down>",
        "Next Variation",
        "Down",
    )
    score_cancel_selection_of_variation = (
        "<KeyPress-Up>",
        "Cancel Variation",
        "Up",
    )
    score_disable_keypress = (
        "<KeyPress>",
        "",
        "",
    )  # No menu entry for this initialisation event.
    score_enable_F10_menubar = ("<KeyPress-F10>", "", "F10")
    score_enable_F10_popupmenu_at_top_left = (
        "<Shift-KeyPress-F10>",
        "Popup Menu at Top Left",
        "Shift F10",
    )
    score_enable_F10_popupmenu_at_pointer = (
        "<Control-KeyPress-F10>",
        "Popup Menu at Pointer",
        "Ctrl F10",
    )

    # Game widget analyse events.
    # Inherited by Repertoire, GameEdit, and RepertoireEdit, widgets.
    analyse_game = ("<Alt-KeyPress-a>", "Analyse", "Alt a")

    # GameEdit widget editing events.
    # Inherited by RepertoireEdit widget.
    gameedit_insert_rav = (
        "<KeyPress>",
        "Insert RAV: move move (<char>)",
        "<char>",
    )
    gameedit_insert_rav_after_rav_end = (
        "<KeyPress>",
        "Insert RAV: (...)(<char>)",
        "<char>",
    )
    gameedit_insert_rav_after_rav_start_move_or_rav = (
        "<Shift-KeyPress>",
        "Insert RAV: ( move (<char>)",
        "Shift <char>",
    )
    gameedit_insert_rav_after_rav_start = (
        "<Alt-KeyPress>",
        "Insert RAV: ((<char>) move",
        "Alt <char>",
    )
    gameedit_insert_castle_queenside = (
        "<Control-KeyPress-o>",
        "O-O-O",
        "Ctrl o",
    )
    gameedit_insert_comment = (
        "<Control-KeyPress-braceleft>",
        "Insert Comment",
        "Ctrl {",
    )
    gameedit_insert_reserved = (
        "<Control-KeyPress-less>",
        "Insert Reserved",
        "Ctrl <",
    )
    gameedit_insert_comment_to_eol = (
        "<Control-KeyPress-semicolon>",
        "Insert Comment to EOL",
        "Ctrl ;",
    )
    gameedit_insert_escape_to_eol = (
        "<Control-KeyPress-percent>",
        "Insert Escape to EOL",
        "Ctrl %",
    )
    gameedit_insert_glyph = (
        "<Control-KeyPress-dollar>",
        "Insert Glyph",
        "Ctrl $",
    )
    gameedit_insert_pgn_tag = (
        "<Control-KeyPress-bracketleft>",
        "Insert PGN Tag",
        "Ctrl [",
    )
    gameedit_insert_pgn_seven_tag_roster = (
        "<Control-KeyPress-bracketright>",
        "Insert PGN Seven Tag Roster",
        "Ctrl ]",
    )
    gameedit_insert_white_win = ("<Control-KeyPress-plus>", "1-0", "Ctrl +")
    gameedit_insert_draw = ("<Control-KeyPress-equal>", "1/2-1/2", "Ctrl =")
    gameedit_insert_black_win = ("<Control-KeyPress-minus>", "0-1", "Ctrl -")
    gameedit_insert_other_result = (
        "<Control-KeyPress-asterisk>",
        "Other Result",
        "Ctrl *",
    )
    gameedit_show_previous_token = (
        "<Shift-KeyPress-Left>",
        "Previous Item",
        "Shift Left",
    )
    gameedit_show_next_token = (
        "<Shift-KeyPress-Right>",
        "Next Item",
        "Shift Right",
    )
    gameedit_show_first_token = (
        "<Shift-KeyPress-Prior>",
        "First Item",
        "Shift PageUp",
    )
    gameedit_show_last_token = (
        "<Shift-KeyPress-Next>",
        "Last Item",
        "Shift PageDn",
    )
    gameedit_show_first_comment = (
        "<Control-KeyPress-Prior>",
        "First Comment",
        "Ctrl PageUp",
    )
    gameedit_show_last_comment = (
        "<Control-KeyPress-Next>",
        "Last Comment",
        "Ctrl PageDn",
    )
    gameedit_show_previous_comment = (
        "<Control-KeyPress-Up>",
        "Previous Comment",
        "Ctrl Up",
    )
    gameedit_show_next_comment = (
        "<Control-KeyPress-Down>",
        "Next Comment",
        "Ctrl Down",
    )
    gameedit_show_previous_rav_start = (
        "<Alt-KeyPress-Prior>",
        "Previous RAV Start",
        "Alt PageUp",
    )
    gameedit_show_next_rav_start = (
        "<Alt-KeyPress-Next>",
        "Next RAV Start",
        "Alt PageDn",
    )
    gameedit_to_previous_pgn_tag = (
        "<Control-KeyPress-Left>",
        "Previous PGN Tag",
        "Ctrl Left",
    )
    gameedit_to_next_pgn_tag = (
        "<Control-KeyPress-Right>",
        "Next PGN Tag",
        "Ctrl Right",
    )
    gameedit_delete_empty_pgn_tag = (
        "<Control-KeyPress-Delete>",
        "Delete empty PGN Tag",
        "Ctrl Delete",
    )
    gameedit_bind_and_show_previous_in_line = (
        "<KeyPress-Up>",
        "Previous Move",
        "Up",
    )
    gameedit_bind_and_show_previous_in_variation = (
        "<Shift-KeyPress-Up>",
        "Previous Move Variation",
        "Shift Up",
    )
    gameedit_bind_and_show_next_in_line = (
        "<Shift-KeyPress-Down>",
        "Next Move",
        "Shift Down",
    )
    gameedit_bind_and_show_next_in_variation = (
        "<KeyPress-Down>",
        "Next Move Select Variation",
        "Down",
    )
    gameedit_bind_and_show_first_in_line = (
        "<KeyPress-Prior>",
        "Start of Variation",
        "PageUp",
    )
    gameedit_bind_and_show_last_in_line = (
        "<KeyPress-Next>",
        "End of Variation",
        "PageDn",
    )
    gameedit_bind_and_show_first_in_game = (
        "<Shift-KeyPress-Prior>",
        "Start of Game",
        "Shift PageUp",
    )
    gameedit_bind_and_show_last_in_game = (
        "<Shift-KeyPress-Next>",
        "End of Game",
        "Shift PageDn",
    )
    gameedit_bind_and_to_previous_pgn_tag = (
        "<Control-KeyPress-Left>",
        "Previous PGN Tag",
        "Ctrl Left",
    )
    gameedit_bind_and_to_next_pgn_tag = (
        "<Control-KeyPress-Right>",
        "Next PGN Tag",
        "Ctrl Right",
    )
    gameedit_delete_token_char_left = (
        "<Shift-KeyPress-BackSpace>",
        "",
        "",
    )  # A menu entry would make sense.
    gameedit_delete_token_char_right = (
        "<Shift-KeyPress-Delete>",
        "",
        "",
    )  # A menu entry would make sense.
    gameedit_delete_char_left = (
        "<KeyPress-BackSpace>",
        "",
        "",
    )  # A menu entry would make sense.
    gameedit_delete_char_right = (
        "<KeyPress-Delete>",
        "",
        "",
    )  # A menu entry would make sense.
    gameedit_set_insert_previous_line_in_token = (
        "<Alt-KeyPress-Up>",
        "",
        "",
    )  # A menu entry would make sense.
    gameedit_set_insert_previous_char_in_token = (
        "<KeyPress-Left>",
        "",
        "",
    )  # A menu entry would make sense.
    gameedit_set_insert_next_char_in_token = (
        "<KeyPress-Right>",
        "",
        "",
    )  # A menu entry would make sense.
    gameedit_set_insert_next_line_in_token = (
        "<Alt-KeyPress-Down>",
        "",
        "",
    )  # A menu entry would make sense.
    gameedit_set_insert_first_char_in_token = (
        "<KeyPress-Home>",
        "",
        "",
    )  # A menu entry would make sense.
    gameedit_set_insert_last_char_in_token = (
        "<KeyPress-End>",
        "",
        "",
    )  # A menu entry would make sense.
    gameedit_add_char_to_token = (
        "<KeyPress>",
        "",
        "",
    )  # A menu entry would say type text to insert.
    gameedit_non_move_show_previous_in_variation = (
        "<Shift-KeyPress-Up>",
        "Previous Move Variation",
        "Shift Up",
    )
    gameedit_non_move_show_previous_in_line = (
        "<KeyPress-Up>",
        "Previous Move",
        "Up",
    )
    gameedit_non_move_show_next_in_line = (
        "<Shift-KeyPress-Down>",
        "Next Move",
        "Shift Down",
    )
    gameedit_non_move_show_next_in_variation = (
        "<KeyPress-Down>",
        "Next Move Select Variation",
        "Down",
    )
    gameedit_non_move_show_first_in_line = (
        "<KeyPress-Prior>",
        "Start of Variation",
        "PageUp",
    )
    gameedit_non_move_show_last_in_line = (
        "<KeyPress-Next>",
        "End of Variation",
        "PageDn",
    )
    gameedit_non_move_show_first_in_game = (
        "<Shift-KeyPress-Prior>",
        "Start of Game",
        "Shift PageUp",
    )
    gameedit_non_move_show_last_in_game = (
        "<Shift-KeyPress-Next>",
        "End of Game",
        "Shift PageDn",
    )

    # Why specific shift versions?
    gameedit_delete_move_char_left_shift = (
        "<Shift-KeyPress-BackSpace>",
        "",
        "",
    )  # A menu entry would make sense.
    gameedit_delete_move_char_right_shift = (
        "<Shift-KeyPress-Delete>",
        "",
        "",
    )  # A menu entry would make sense.
    gameedit_delete_move_char_left = (
        "<KeyPress-BackSpace>",
        "",
        "",
    )  # A menu entry would make sense.
    gameedit_delete_move_char_right = (
        "<KeyPress-Delete>",
        "",
        "",
    )  # A menu entry would make sense.

    gameedit_add_move_char_to_token = (
        "<KeyPress>",
        "",
        "",
    )  # A menu entry would say type moves to insert.
    gameedit_insert_move = (
        "<KeyPress>",
        "",
        "",
    )  # A menu entry would say type moves to insert.
    gameedit_edit_move = (
        "<KeyPress-BackSpace>",
        "",
        "",
    )  # A menu entry would make sense.

    # GameDisplay
    gamedisplay_to_previous_game = ("<KeyPress-F7>", PREVIOUS_GAME, "F7")
    gamedisplay_to_next_game = ("<KeyPress-F8>", NEXT_GAME, "F8")

    # Switch between scoresheet and analysis in game or repertoire.
    scoresheet_to_analysis = ("<Alt-KeyPress-F8>", "Analysis", "Alt F8")
    analysis_to_scoresheet = ("<Alt-KeyPress-F8>", "Scoresheet", "Alt F8")

    # PartialDisplay
    partialdisplay_to_previous_partial = (
        "<KeyPress-F7>",
        PREVIOUS_PARTIAL_POSITION,
        "F7",
    )
    partialdisplay_to_next_partial = (
        "<KeyPress-F8>",
        NEXT_PARTIAL_POSITION,
        "F8",
    )
    export_from_partialdisplay = (
        "<Control-Alt-KeyPress-Home>",
        "Export",
        "Ctrl Alt Home",
    )

    # PartialEdit
    partialedit_insert_char_or_token = (
        "<KeyPress>",
        "",
        "",
    )  # No menu entry because character required.
    partialedit_delete_char_left = (
        "<KeyPress-BackSpace>",
        "",
        "",
    )  # A menu entry would make sense.
    partialedit_delete_char_right = (
        "<KeyPress-Delete>",
        "",
        "",
    )  # A menu entry would make sense.
    partialedit_show_previous_token = ("<KeyPress-Up>", "Previous Piece", "Up")
    partialedit_show_next_token = ("<KeyPress-Down>", "Next Piece", "Down")
    partialedit_show_first_token = (
        "<KeyPress-Prior>",
        "First Piece",
        "PageUp",
    )
    partialedit_show_last_token = ("<KeyPress-Next>", "Last Piece", "PageDn")
    partialedit_insert_partial_name_left = (
        "<Control-KeyPress-bracketleft>",
        "Name",
        "Ctrl [",
    )
    partialedit_insert_partial_name_right = (
        "<Control-KeyPress-bracketright>",
        "Name",
        "Ctrl ]",
    )
    partialedit_set_insert_previous_char_in_token = (
        "<KeyPress-Left>",
        "",
        "",
    )  # A menu entry would make sense.
    partialedit_set_insert_next_char_in_token = (
        "<KeyPress-Right>",
        "",
        "",
    )  # A menu entry would make sense.
    partialedit_set_insert_first_char_in_token = (
        "<KeyPress-Home>",
        "",
        "",
    )  # A menu entry would make sense.
    partialedit_set_insert_last_char_in_token = (
        "<KeyPress-End>",
        "",
        "",
    )  # A menu entry would make sense.

    # RepertoireDisplay
    repertoiredisplay_to_previous_repertoire = (
        "<KeyPress-F7>",
        PREVIOUS_REPERTOIRE,
        "F7",
    )
    repertoiredisplay_to_next_repertoire = (
        "<KeyPress-F8>",
        NEXT_REPERTOIRE,
        "F8",
    )

    # PartialScore
    partialscore_disable_keypress = (
        "<KeyPress>",
        "",
        "",
    )  # No menu entry because character required.

    # Partial widget partial position export events.
    # Inherited by PartialEdit widget.
    text_from_partial = (
        "<Control-Alt-KeyPress-Home>",
        "Text",
        "Ctrl Alt Home",
    )

    # Keyboard traversal events (Control-F8 Control-F7): all relevant widgets.
    # tab_traverse_backward bindings behave differently to expectation given
    # tab_traverse_forward behaviour at Python3.3 with Tk8.6, although I do not
    # know what happens with Tk8.5 an so forth.  Similarely <Shift-Tab>.
    tab_traverse_forward = ("<Control-KeyPress-F8>", "Focus Next", "Ctrl F8")
    tab_traverse_backward = (
        "<Control-KeyPress-F7>",
        "Focus Previous",
        "Ctrl F7",
    )
    tab_traverse_round = ("<Alt-KeyPress-F8>", "Focus Round", "Alt F8")

    # SelectionDisplay
    selectiondisplay_to_previous_selection = (
        "<KeyPress-F7>",
        PREVIOUS_SELECTION_RULE,
        "F7",
    )
    selectiondisplay_to_next_selection = (
        "<KeyPress-F8>",
        NEXT_SELECTION_RULE,
        "F8",
    )

    # SelectionText
    selectiontext_disable_keypress = (
        "<KeyPress>",
        "",
        "",
    )  # Keyboard actions do nothing by default.

    # EngineGrid
    engine_grid_run = ("<Alt-KeyPress-r>", "Run Engine", "Alt r")

    # EngineText
    enginetext_disable_keypress = (
        "<KeyPress>",
        "",
        "",
    )  # Keyboard actions do nothing by default.

    # DatabaseEngineDisplay
    databaseenginedisplay_run = ("<Alt-KeyPress-r>", "Run Engine", "Alt r")

    # DatabaseEngineEdit
    databaseengineedit_browse = ("<Alt-KeyPress-b>", "Browse Engines", "Alt b")

    # Export PGN options.
    # These are put in the 'Export' submenu available on all widgets based on
    # subclasses of Score or GameListGrid; and in the main Database menu.
    # Attempt with <Alt-Shift-KeyPress-Home> for reduced export format failed.
    # Shift-Home is already taken by the bindings defined for DataGrids in the
    # solentware_misc.gui.datagrid module: hence Shift-Escape below.
    pgn_reduced_export_format = (
        "<Alt-KeyPress-End>",
        "PGN reduced",
        "Alt End",
        4,
    )
    pgn_export_format_no_comments_no_ravs = (
        "<Control-KeyPress-Home>",
        "PGN all tags moves played",
        "Ctrl Home",
        4,
    )
    pgn_export_format_no_comments = (
        "<Control-Shift-KeyPress-Home>",
        "PGN no comments",
        "Ctrl Shift Home",
        4,
    )
    pgn_export_format = (
        "<Control-Alt-KeyPress-Home>",
        "PGN",
        "Ctrl Alt Home",
        0,
    )
    pgn_import_format = (
        "<Shift-KeyPress-Escape>",
        "PGN import",
        "Shift Escape",
        4,
    )
    text_internal_format = ("<Alt-KeyPress-Home>", "Text", "Alt Home", 0)

    # ButtonPress event definitions.
    control_buttonpress_1 = ("<Control-ButtonPress-1>", "", "")
    control_buttonpress_3 = ("<Control-ButtonPress-3>", "", "")
    shift_buttonpress_1 = ("<Shift-ButtonPress-1>", "", "")
    shift_buttonpress_3 = ("<Shift-ButtonPress-3>", "", "")
    alt_buttonpress_1 = ("<Alt-ButtonPress-1>", "", "")
    alt_buttonpress_3 = ("<Alt-ButtonPress-3>", "", "")
    buttonpress_1 = ("<ButtonPress-1>", "", "")
    buttonpress_3 = ("<ButtonPress-3>", "", "")

    # Menubar event definitions.
    # F10 in any window invokes the first menu (probably Database).
    # Alt-x invokes the corresponding menu in the menubar, where x is the
    # underlined character.
    menu_database_open = ("", "Open", "", 0)
    menu_database_new = ("", "New", "", 0)
    menu_database_close = ("", "Close", "", 0)
    menu_database_import = ("", "Import", "", 0)
    menu_database_export = ("", "Export", "", 0)
    menu_database_delete = ("", "Delete", "", 0)
    menu_database_quit = ("", "Quit", "", 0)
    menu_database_export_all_text = ("", "All (text)", "", 0)

    # Games, Repertoires, and Positions, are used in the Import and Export
    # submenus of the Database menu.
    menu_database_games = ("", "Games", "", 0)
    menu_database_repertoires = ("", "Repertoires", "", 0)
    menu_database_positions = ("", "Positions", "", 0)

    # Show and hide are used in the Select, Position, and Repertoire menus.
    menu_show = ("", "Show", "", 0)
    menu_hide = ("", "Hide", "", 0)

    menu_select_rule = ("", "Rule", "", 0)
    menu_select_game = ("", "Game", "", 0)
    menu_select_index = ("", "Index", "", 0)
    menu_select_error = ("", "Error", "", 0)

    # Submenu for menu_select_index.
    menu_select_index_black = ("", "Black", "", 0)
    menu_select_index_white = ("", "White", "", 0)
    menu_select_index_event = ("", "Event", "", 0)
    menu_select_index_date = ("", "Date", "", 0)
    menu_select_index_result = ("", "Result", "", 0)
    menu_select_index_site = ("", "Site", "", 0)
    menu_select_index_round = ("", "Round", "", 4)

    menu_game_new_game = ("", "New Game", "", 0)
    menu_position_partial = ("", "Partial", "", 0)
    menu_repertoire_opening = ("", "Opening", "", 0)
    menu_tools_board_style = ("", "Board Style", "", 6)
    menu_tools_board_fonts = ("", "Board Fonts", "", 6)
    menu_tools_board_colours = ("", "Board Colours", "", 6)
    menu_tools_hide_game_analysis = ("", "Hide Game Analysis", "", 0)
    menu_tools_show_game_analysis = ("", "Show Game Analysis", "", 5)
    menu_tools_hide_game_scrollbars = ("", "Hide Game Scrollbars", "", 1)
    menu_tools_show_game_scrollbars = ("", "Show Game Scrollbars", "", 2)
    menu_tools_toggle_game_move_numbers = (
        "",
        "Toggle Game Move Numbers",
        "",
        12,
    )
    menu_tools_toggle__analysis_fen = ("", "Toggle Analysis Fen", "", 7)
    menu_tools_toggle_single_view = ("", "Toggle Single View", "", 14)
    menu_engines_position_queues = ("", "Position Queues", "", 0)
    menu_engines_show_engines = ("", "Show Engines", "", 5)
    menu_engines_start_engine = ("", "Start Engine", "", 0)
    menu_engines_quit_all_engines = ("", "Quit All Engines", "", 0)
    menu_commands_multipv = ("", "MultiPV", "", 6)
    menu_commands_depth = ("", "Depth", "", 0)
    menu_commands_hash = ("", "Hash", "", 0)
    menu_help_guide = ("", "Guide", "", 0)
    menu_help_selection_rules = ("", "Selection rules", "", 0)
    menu_help_file_size = ("", "File size", "", 0)
    menu_help_notes = ("", "Notes", "", 0)
    menu_help_about = ("", "About", "", 0)
