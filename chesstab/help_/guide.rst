=====================================
ChessTab - a database for chess games
=====================================

.. contents::


Introduction
============

A ChessTab database can contain games and repertoires.

Games and repertoires can be imported from files, or typed in using the editing functions.

When playing through a game or repertoire, a list of all games containing the current position is displayed.

Games repertoires in the database can be edited or deleted.

Selection and chessql queries, and instructions to run chess engines, can be typed in using the editing functions, and be edited or deleted later.

Chess engines which support the Universal Chess Interface (`UCI`_) can be used to analysis positions in games and repertoires.  The analysis can be played through like a game or repertoire.

When a chessql statement is displayed, the list of games matching the query is also displayed.

Games can be output to Portable Game Notation (`PGN`_) files in `Export Format`_, `Reduced Export Format`_, or an `import format`_ excluding comments and glyphs.

Repertoires and chessql statements can be exported too.


Getting started
===============

Start the program.

Open a game window using 'Game | New Game' and click with the pointer over the board or the adjacent empty PGN-like score.  Clicking on the analysis below the board has no effect at this point.

The 'Tools' menu allows the appearance of the game window to be changed.  All game, repertoire, and partial position windows are affected by changes.

Type some moves.  'e4e5nf3nc6lb5' for example (lower case el is a short cut for 'shift-B' for bishop).

Mistakes such as 'e4e5nf3nc5lb5' will produce a green cursor covering 'Nc5Bb5', for example.  Keyboard actions have their usual meanings within the green cursor, allowing mistakes to be corrected.  This one is fixed by deleting '5Bb5' and typing '6lb5'; editing the mistyped '5' to '6' is not sufficient.

Left and right button clicks on the board move the green cursor through the game score.  'drag and drop' on board does not move pieces (or do anything in fact).

Left click on the game score moves the green cursor and adjusts the position on the board to fit it's new location.  The green cursor disappears if the click does not fit a game position and the initial position is put on the board,

Right click on the game score displays a popup menu of actions with their keyboard equivalents.  The actions available depend on click location but may not be obvious at the top level popup menu.

Chess engine analysis is added to the analysis by engines started using the dialogue presented by 'Engines | Start Engine'.  Click 'Open' on the dialogue with the chess engine program file selected; then press 'Return' in the command line dialogue presented to start the engine.  See chess engine documentation for details of any options required in the command line dialogue.

The response from the chess engine will appear in analysis after an interval, short if the default depth (10) and number of variations (1) are being used.

'Commands | Depth' and 'Commands | MultiPV' can be used to change the depth of analysis and the number of variations shown, assuming the chess engine allows these values to be changed.  New analysis from the chess engine will be displayed, when available, if these values are increased.

'Alt + F8' toggles between navigating the analysis and the game score for the active game.  The pointer equivalent is on the popup menu.  Left and right button clicks on the board switch to fit.

Create a database using 'Database | New'.

Add plausible values to the PGN tags in the game and insert the game in the database.  Use 'Shift Left' and 'Shift Right' to get to the PGN tag data entry areas; but add the result using 'Ctrl +', 'Ctrl -', 'Ctrl =', or 'Ctrl \*', to keep the PGN tag and the game end marker in step.

Add the game to the database using the 'Insert' key or 'right button click | Database | Insert'.

Import some games, from a PGN file, using 'Database | Import | Games'.  Click 'Open' on the dialogue with the PGN file selected.  Lines like 'Ready to proceed ...' or 'Finished ...' will appear in the following import dialogue when ChessTab is waiting for instructions (meaning click one of the buttons).

Two lists of games are displayed when the import dialogue is dismissed.  The upper one is the list of all games in the database.  The lower is the list of games containing the position on the board: except that no games are listed if the green cursor is absent, usually because the start of game is displayed.  The lower list changes as the green cursor is moved.

Select one or more games for display using 'right button click | Display' on the list of games.  The original game keeps the large board.

Left click on one of the smaller boards or game scores to make that game get the large board. 'F7' and 'F8' will cycle round the displayed games.  The lower list changes to fit the position on the large board.

This is a convenient place to stop the detailed description: otherwise everything would get described.

The Position and Repertoire menus work a lot like the Game menu.

The Selection menu allows the top list, of all games in the database, to be sorted and filtered by values of the `PGN Seven Tag Roster`_.

The Selection menu also allows selection rules to be stored on the database and used to choose the list of games displayed.  The rule "White eq Body, Any" is similar to "Select | Index | White" and giving "Body, Any" as the Filter; but "White eq Body, Any or Black eq Body, Any" selects all games played by "Body, Any".


Top-level Navigation
====================

Left click over an item, when it is not the active item, makes it the active item.  The keyboard equivalents are described here.

F2		List of partial positions
Alt + F2		Active partial position
Shift + F2		List of games containing active partial position
F3		List of game selection rules
Alt + F3		Active game selection rule
F6		List of repertoires
Alt + F6		Active repertoire
Shift + F6		List of games containing current position of active repertoire
F7		Previous item like active item
F8		Next item like active item
F9		List of games in database
Alt + F9		Active game
Shift + F9		List of games containing current position of active game

Alt + Fn and Shift + Fn act as Fn on their targets above: so Alt + F9 on the active game makes the list of games in database active (F9) for example.


Keyboard Actions
================

All keyboard actions are available as menu actions, either the menu bar at top
of application or a popup menu activated by right click, except for typing text such as moves or comments.


Popup Menus
===========

Right mouse click displays a popup menu of actions if appropriate.

'Shift F10' and 'Ctrl F10' display a popup menu of actions for the item with keyboard focus if appropriate.  'Shift F10' posts the menu at top left corner of item. 'Ctrl F10' posts the menu at pointer position, which may be over another item.

Over a game or repertoire board right mouse click displays the next position unless variations are available, when these are highlighted in the game score.


Playing through a game
======================

The Up and Down arrow keys are used to move backward and forward through a game score.  The equivalent pointer actions on the board are left click and right click.  Left click on a move in the game or analysis score makes the position after the move has been played appear on the board.

If necessary the first left click makes the game active: clicking on one of the games with a smaller board will first make it the game with the big board as well.  Subsequent clicks move through the game.


Editing a game
==============

Call up the game with 'Ctrl F11' rather than 'F11'.

Play through the game to the point where editing is to be done.

For deletion of moves this means go to the last move of a variation or the game and repeat use of the Backspace key until the moves to be deleted have gone.

For insertion of variations this means go to the move which shows the position at which the variation occurs and start typing moves.

For comments this means go to the comment, position the cursor at the point in the comment to be edited, and start editing: the editing functions are quite limited, just delete and insert but no cut and paste and so forth.

To insert a new comment, type 'Ctrl {' at the comment should appear after.

To insert a new PGN Tag, type 'Ctrl [' at the PGN Tag the new tag should appear after.

The full range of editing commands are listed under PGN in the popup menu seen by right click on the game or analysis.


Repertoires
===========

Repertoires are like games except they are associated with different lists of games; and the PGN Tag technique is used to name them but not the ones defined by the PGN standard.


ChessQL statements
==================

ChessQL statements can be stored by using the 'Position | Partial' menu item.  The editor is the simplest available.  But navigation is as close as possible to the way used in games and repertoires.

ChessQL statements use the syntax of `CQL version 5.1`_ but ChessTab does not emulate the behaviour of CQL.  It is simply a much better way of expressing partial position searches than used previously in ChessTab.  CQL's piece designators are sufficient to replace the old partial positions; and currently only piece designators are implemented and other CQL constructs are ignored.

All ChessQL statements must start cql(...), and an example simplest one that does anything is 'cql() Pd5' meaning find all games containing a position with a white pawn on d5.


Selection Rules
===============

The 'Select' menu allows the list of games on the database to by sorted by an index.  The 'Filter' option is then available and can be used to pick the range of games listed.

Selection rules can be stored by using the 'Select | Rule' menu item.  The editor is the simplest available.  But navigation is as close as possible to the way used in games and repertoires.


Chess Engines
=============

Chess engines can be started and stopped from the 'Engines' menu.

Depth of analysis and number of variations reported are controlled using the 'Commands' menu.  Analysis stored on a database is never replaced by analysis to less depth or with less variations reported.

The number of positions queued for analysis can be displayed by the 'Position Queues' menu item.  When the numbers reach 0 (zero) after analysis of a game or games has been requested, the analysis has been completed.

The 'Engines | Start Engine' menu item opens a dialogue best described as "similar to the 'Run...' option off the Start button on Microsoft Windows XP".

The 'Engines | Show Engines' menu item displays a list of 'run chess engine' commands which have been stored on the database.

Use the popup menu for an engine in the list displayed by 'Engines | Show Engines', or the 'Run Chess Engine' dialogue, to start the chess engine and have it talk to ChessTab.

Currently Stockfish runs by browsing to the stockfish program file and set it going.  For others you may need to find out what options to add to the command line presented when the file is 'Open'ed in the 'Run Chess Engine' dialogue, or added to the list of engines displayed by 'Engines | Show Engines'.

The engine must support the Universal Chess Interface (UCI) protocol.

The interface is intended to get positions analyzed, not play games against an engine.




.. _`import format`: http://www6.chessclub/help/PGN-spec
.. _`PGN`: http://www6.chessclub/help/PGN-spec
.. _`Export Format`: http://www6.chessclub/help/PGN-spec
.. _`Reduced Export Format`: http://www6.chessclub/help/PGN-spec
.. _`UCI`: http://www.shredderchess.com/div/uci.zip
.. _`PGN Seven Tag Roster`: http://www6.chessclub/help/PGN-spec
.. _`CQL version 5.1`: http://www.gadycosteff.com/
