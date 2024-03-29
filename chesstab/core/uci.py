# uci.py
# Copyright 2015 Roger Marsh
# License: See LICENSE.TXT (BSD licence)

"""Collate position analysis from multiple chess engines.

Chess engines must support the UCI (Universal Chess Interface).

The UCI commands relevant to analysing a single position are supported.

The commands related to 'infinite analysis' are not supported because this
module expects the chess engine to finish a command and give a response without
the need to interrupt it.

"""

import multiprocessing
from queue import Empty, Full
import os

from solentware_grid.gui.dataedit import RecordEdit

from uci_net.uci_driver_over_tcp import UCIDriverOverTCP
from uci_net.engine import (
    Engine,
    EngineInterface,
    CommandsFromEngine,
    CommandsToEngine,
    GoSubCommands,
    PositionSubCommands,
    OptionParameters,
    ReservedOptionNames,
    SetoptionSubCommands,
    InfoParameters,
    ScoreInfoValueNames,
)

from .uci_to_pgn import generate_pgn_for_uci_moves_in_position
from .chessrecord import ChessDBrecordAnalysis
from .analysis import Analysis


class UCIStartEngineError(Exception):
    """Raise when attempt to start engine fails."""


class UCI:
    """Control multiple chess engines using the UCI."""

    def __init__(self):
        """Set data stuctures to control multiple UCI chess engines."""
        self.engine_counter = 0
        self.uci_drivers_index = {}

        # Avoid "OSError: [WinError 535] Pipe connected"  at Python3.3 running
        # under Wine on FreeBSD 10.1 by disabling the UCI functions.
        # Assume all later Pythons are affected because they do not install
        # under Wine at time of writing.
        # The OSError stopped happening by wine-2.0_3,1 on FreeBSD 10.1 but
        # get_nowait() fails to 'not wait', so ChessTab never gets going under
        # wine at present.  Leave alone because it looks like the problem is
        # being shifted constructively.
        # At Python3.5 running under Wine on FreeBSD 10.1, get() does not wait
        # when the queue is empty either, and ChessTab does not run under
        # Python3.3 because it uses asyncio: so no point in disabling.
        # try:
        #    self.uci_drivers_reply = multiprocessing.Queue()
        # except OSError:
        #    self.uci_drivers_reply = None
        self.uci_drivers_reply = multiprocessing.Queue()

        self.uci_drivers = {}
        self.uci_drivers_fen = {}
        self.uci_active_engines = {}
        self.ui_analysis_queue = None
        self.position_analysis = {}
        self._use_ucinewgame = True
        self._clear_hash = True
        self._go_depth = 10

        # 0 (zero) means use the default assumed by the engine.
        self._multipv = 0
        self._hash_size = 0

        self.analysis_record = ChessDBrecordAnalysis()
        self.analysis_data_source = None

        # These are new and will replace some of above attributes.
        self.positions_pending = {}
        self.engine_queues = {}
        self.clear_hash_after_bestmove = {}
        self.set_option_on_empty_queues = set()

    def kill_engine(self, number):
        """Attempt to kill engine and return True if successful."""
        ui_name = self.uci_drivers_index[number]
        engine_interface = self.uci_drivers[ui_name]
        try:
            engine_interface.to_driver_queue.put(CommandsToEngine.quit_)
        except (Full, ValueError, AssertionError):
            return False
        engine_interface.driver.join()
        engine_name = engine_interface.parser.name
        if engine_name in self.uci_active_engines:
            # The command 'stockfish argument' starts stockfish but the engine
            # quits immediately citing 'Unknown command: argument'.
            # These engine_name entries do not exist in this case.
            self.uci_active_engines[engine_name].discard(ui_name)
            if not self.uci_active_engines[engine_name]:
                del self.uci_active_engines[engine_name]
                del self.positions_pending[engine_name]
                del self.engine_queues[engine_name]

        del self.clear_hash_after_bestmove[ui_name]
        del self.uci_drivers[ui_name]
        del self.uci_drivers_fen[ui_name]
        del self.uci_drivers_index[number]
        return True

    def quit_all_engines(self):
        """Attempt to kill all engines and return list of those not killed."""
        joiners = []
        non_joiners = []
        for ui_name, engine_interface in self.uci_drivers.items():
            try:
                engine_interface.to_driver_queue.put(CommandsToEngine.quit_)
            except (Full, ValueError, AssertionError):
                non_joiners.append((ui_name, engine_interface.driver.pid))
                continue
            joiners.append(engine_interface.driver)
        for item in joiners:
            item.join()
        self.uci_active_engines.clear()
        self.positions_pending.clear()
        self.engine_queues.clear()
        self.uci_drivers.clear()
        self.uci_drivers_index.clear()
        self.uci_drivers_fen.clear()
        self.clear_hash_after_bestmove.clear()
        return non_joiners

    def run_engine(self, program_file_name, args):
        """Start a process to run an UCI chess engine."""
        # Avoid "OSError: [WinError 535] Pipe connected"  at Python3.3 running
        # under Wine on FreeBSD 10.1 by disabling the UCI functions.
        # Assume all later Pythons are affected because they do not install
        # under Wine at time of writing.
        # The OSError stopped happening by wine-2.0_3,1 on FreeBSD 10.1 but
        # get_nowait() fails to 'not wait', so ChessTab never gets going under
        # wine at present.  Leave alone because it looks like the problem is
        # being shifted constructively.
        # At Python3.5 running under Wine on FreeBSD 10.1, get() does not wait
        # when the queue is empty either, and ChessTab does not run under
        # Python3.3 because it uses asyncio: so no point in disabling.
        # if self.uci_drivers_reply is None:
        #    return

        self.engine_counter += 1
        ui_name = ": ".join(
            (
                str(self.engine_counter),
                os.path.splitext(os.path.basename(program_file_name))[0],
            )
        )
        to_driver_queue = multiprocessing.Queue()
        driver = multiprocessing.Process(
            target=run_driver,
            args=(
                to_driver_queue,
                self.uci_drivers_reply,
                program_file_name,
                args,
                ui_name,
            ),
        )
        try:
            driver.start()
        except UCIStartEngineError:
            return
        self.uci_drivers[ui_name] = EngineInterface(
            driver=driver,
            program_file_name=program_file_name,
            to_driver_queue=to_driver_queue,
            parser=Engine(),
        )
        self.uci_drivers_index[self.engine_counter] = ui_name
        self.uci_drivers_fen[ui_name] = None
        self.clear_hash_after_bestmove[ui_name] = False

        # Send the initial 'uci' command to the engine
        to_driver_queue.put(CommandsToEngine.uci)

    def get_engine_responses(self):
        """Drain the queue of responses and process them.

        Calls of this method are scheduled by tkinter.after().

        """
        while True:
            try:
                item = self.uci_drivers_reply.get_nowait()
            except Empty:
                break
            self._process_commands_from_engines(item)

    def _process_commands_from_engines(self, response):
        """Process responses from UCI chess engines.

        Calls of this method are scheduled by tkinter.after().

        """
        ui_name, commands = response

        # UCI commands are generally ignored if not understood.
        # Follow this principle here.
        try:
            driver = self.uci_drivers[ui_name]
        except KeyError:
            if ui_name in ("start failed", "started"):
                return
            raise
        driver.parser.process_engine_commands(response)

        command = commands[-1].split(None, maxsplit=1)[0]
        if command == CommandsFromEngine.bestmove:
            self.bestmove(ui_name)
        elif command == CommandsFromEngine.readyok:
            self.readyok(ui_name)
        elif command == CommandsFromEngine.uciok:
            self.uciok(ui_name)
        elif command == CommandsFromEngine.registration:
            self.registration(ui_name)
        elif command == CommandsFromEngine.copyprotection:
            self.copyprotection(ui_name)
        else:
            pass

    def get_analysis_requests(self):
        """Add requests for analysis of positions to engine queues."""
        if (
            self.set_option_on_empty_queues
            and self.is_positions_pending_empty()
        ):
            if ReservedOptionNames.Hash in self.set_option_on_empty_queues:
                # Postpone Hash action until all engines ready.
                for engine_interface in self.uci_drivers.values():
                    eip = engine_interface.parser
                    if eip.readyok_expected or eip.uciok_expected is not False:
                        return

                for engine_interface in self.uci_drivers.values():
                    eip = engine_interface.parser
                    eipoh = eip.options.get(ReservedOptionNames.Hash)
                    if eipoh is None:
                        continue
                    if not self.hash_size:
                        newhash = eipoh[1].get(OptionParameters.default)
                        if newhash is None:
                            continue
                    else:
                        min_ = eipoh[1].get(OptionParameters.min_)
                        max_ = eipoh[1].get(OptionParameters.max_)
                        if min_ is None or max_ is None:
                            continue
                        newhash = max(
                            min(self.hash_size, int(max_)), int(min_)
                        )
                    engine_interface.to_driver_queue.put(
                        " ".join(
                            (
                                CommandsToEngine.setoption,
                                SetoptionSubCommands.name,
                                ReservedOptionNames.Hash,
                                SetoptionSubCommands.value,
                                str(newhash),
                            )
                        )
                    )
                    engine_interface.to_driver_queue.put(
                        CommandsToEngine.isready
                    )
                    engine_interface.parser.readyok_expected = True
                self.set_option_on_empty_queues.discard(
                    ReservedOptionNames.Hash
                )
            return

        requests = {}
        engine_queues = self.engine_queues
        positions_pending = self.positions_pending
        while True:
            try:
                item = self.ui_analysis_queue.get_nowait()
            except Empty:
                break
            except Exception:
                if self.ui_analysis_queue is None:
                    break
                raise
            game, position_data = item
            if game is position_data:
                continue
            requests.setdefault(game, []).append(position_data)
            for value in engine_queues.values():
                if game in value:
                    value.append(value.pop(value.index(game)))
                else:
                    value.append(game)
        for value in positions_pending.values():
            value.update({rk: rv.copy() for rk, rv in requests.items()})

        uci_drivers_fen = self.uci_drivers_fen
        for key, engine_interface in self.uci_drivers.items():
            if uci_drivers_fen[key] is not None:
                continue
            eip = engine_interface.parser
            if eip.readyok_expected:
                continue
            if eip.uciok_expected is not False:
                continue
            engq = engine_queues[eip.name]
            epp = positions_pending[eip.name]
            while len(engq):
                if len(epp[engq[-1]]):
                    position_data = epp[engq[-1]].pop()
                    if self._process_analysis_request(
                        engine_interface, position_data
                    ):
                        uci_drivers_fen[key] = position_data.position
                        break
                else:
                    del epp[engq[-1]]
                    del engq[-1]

    def set_analysis_queue(self, queue):
        """Note queue for return of UCI engine analysis to user interface."""
        self.ui_analysis_queue = queue

    def _process_analysis_request(self, engine_interface, position_data):
        """Return True if deeper or wider analysis requested from engine."""
        engine_name = engine_interface.parser.name

        # (0, 0) or value read from database by requestor.
        depth, multipv = position_data.scale.get(engine_name, (0, 0))
        if depth >= self._go_depth and multipv >= self._multipv:
            return False

        # Is analysis available already from non-database store request?
        fen = position_data.position
        position_analysis_fen = self.position_analysis.get(fen)
        if position_analysis_fen:
            if engine_name in position_analysis_fen.scale:
                depth, multipv = position_analysis_fen.scale[engine_name]
                if depth >= self._go_depth and multipv >= self._multipv:
                    return False

        # Can the engine cope with the multiPV option value?
        ronmpv = ReservedOptionNames.MultiPV
        udpo = engine_interface.parser.options
        if multipv < self._multipv:
            if ronmpv not in udpo:
                if depth >= self._go_depth:
                    return False
                multipv = 1
            else:
                mpv = min(
                    max(
                        int(udpo[ronmpv][1][OptionParameters.min_]),
                        self._multipv,
                    ),
                    int(udpo[ronmpv][1][OptionParameters.max_]),
                )
                if depth >= self._go_depth and multipv >= mpv:
                    return False
                if mpv < multipv:
                    multipv = mpv

        # Put commands to do analysis on engine command queue.
        # If analysis already exists do not reduce depth; multipv is already
        # as high as possible given requested value.
        if ronmpv in udpo:
            engine_interface.to_driver_queue.put(
                " ".join(
                    (
                        CommandsToEngine.setoption,
                        SetoptionSubCommands.name,
                        ronmpv,
                        SetoptionSubCommands.value,
                        str(max(multipv, self._multipv)),
                    )
                )
            )
        engine_interface.to_driver_queue.put(
            " ".join((CommandsToEngine.position, PositionSubCommands.fen, fen))
        )
        engine_interface.to_driver_queue.put(
            " ".join(
                (
                    CommandsToEngine.go,
                    GoSubCommands.depth,
                    str(max(self.go_depth, depth)),
                )
            )
        )
        return True

    def uciok(self, ui_name):
        """Process uciok command from UCI chess engine."""
        engine_interface = self.uci_drivers[ui_name]
        eip = engine_interface.parser
        eip.uciok_expected = False
        self.uci_active_engines.setdefault(eip.name, set()).add(ui_name)
        self.positions_pending.setdefault(eip.name, {})
        self.engine_queues.setdefault(eip.name, [])
        if self.use_ucinewgame:
            engine_interface.to_driver_queue.put(CommandsToEngine.ucinewgame)
            engine_interface.to_driver_queue.put(CommandsToEngine.isready)
            eip.readyok_expected = True

    def readyok(self, ui_name):
        """Process readyok command from UCI chess engine."""
        engine_interface = self.uci_drivers[ui_name]
        if self.clear_hash_after_bestmove[ui_name]:
            engine_interface.to_driver_queue.put(CommandsToEngine.isready)

            # Assume all engines have the 'Clear Hash' option.
            # Partly to avoid changing uci package right now to ask.
            engine_interface.to_driver_queue.put(
                " ".join(
                    (
                        CommandsToEngine.setoption,
                        SetoptionSubCommands.name,
                        ReservedOptionNames.clear_hash,
                    )
                )
            )

            self.clear_hash_after_bestmove[ui_name] = False
            return
        engine_interface.parser.readyok_expected = False

    def bestmove(self, ui_name):
        """Extract engine analysis and tidy up engine.

        This is where the analysis snapshots held in the Engine object should
        be pruned if required: after the extraction.

        """
        self._extract_variations_from_engine_bestmove(ui_name)
        self.uci_drivers_fen[ui_name] = None
        if self.use_ucinewgame:
            engine_interface = self.uci_drivers[ui_name]
            engine_interface.to_driver_queue.put(CommandsToEngine.ucinewgame)
            engine_interface.to_driver_queue.put(CommandsToEngine.isready)
            engine_interface.parser.readyok_expected = True
        if self.clear_hash:
            self.clear_hash_after_bestmove[ui_name] = True

    def copyprotection(self, ui_name):
        """Print the copy protection command from the chess engine."""
        print(
            CommandsFromEngine.copyprotection,
            self.uci_drivers[ui_name].parser.copyprotection,
        )

    def registration(self, ui_name):
        """Print the registration command from the chess engine."""
        print(
            CommandsFromEngine.registration,
            self.uci_drivers[ui_name].parser.registration,
        )

    @property
    def use_ucinewgame(self):
        """Return True if ucinewgame command to be used before each move."""
        return self._use_ucinewgame

    @use_ucinewgame.setter
    def use_ucinewgame(self, value):
        """Set to use, or not use, before every position command."""
        self._use_ucinewgame = bool(value)

    @property
    def clear_hash(self):
        """Return True if clear hash command to be used before each move."""
        return self._clear_hash

    @clear_hash.setter
    def clear_hash(self, value):
        """Set to use, or not use, before every position command."""
        self._clear_hash = bool(value)

    @property
    def go_depth(self):
        """Return depth value to use in go depth commands."""
        return self._go_depth

    @go_depth.setter
    def go_depth(self, value):
        """Set to the depth used in all go commands."""
        self._go_depth = value

    @property
    def multipv(self):
        """Return value to use in setoption MultiPV commands."""
        return self._multipv

    @multipv.setter
    def multipv(self, value):
        """Set to the value used in all setoption MultiPV commands."""
        self._multipv = value

    @property
    def hash_size(self):
        """Return value to use in setoption hash commands."""
        return self._hash_size

    @hash_size.setter
    def hash_size(self, value):
        """Set to the value used in all setoption hash commands."""
        self._hash_size = value

    def any_readyok_pending(self):
        """Return True if expected engine readyok commands not yet received."""
        for engine_interface in self.uci_drivers.values():
            if engine_interface.parser.readyok_expected:
                return True
        return False

    def _extract_variations_from_engine_bestmove(self, ui_name):
        """Extract and save on database new wider or deeper analysis."""
        engine_parser = self.uci_drivers[ui_name].parser
        engine_name = engine_parser.name
        snapshot = engine_parser.info[-1][-1]
        multipv = snapshot.multipv
        fen = self.uci_drivers_fen[ui_name]

        # Invert the sorted list comprehension to allow for different content
        # in chess engine 'score' info when mate, or checkmate and stalemate
        # positions, are involved.
        score = InfoParameters.score
        centipawns = ScoreInfoValueNames.cp
        mate = ScoreInfoValueNames.mate
        lines = []
        for key, value in snapshot.pv_group.items():
            lines.append(
                [
                    int(key) if key else 0,
                    None,
                    value[InfoParameters.depth],
                    generate_pgn_for_uci_moves_in_position(
                        value[InfoParameters.pv][0], fen
                    ),
                ]
            )
            if centipawns in value[score]:
                lines[-1][1] = value[score][centipawns]
            elif mate in value[score]:
                lines[-1][1] = value[score][mate] + "0000"
            else:
                lines[-1][1] = 0
        lines = sorted(lines)[: int(multipv) if multipv is not None else 1]

        eng_a = Analysis()
        eng_a.scale = {
            engine_name: (min(int(d[2]) for d in lines), len(lines))
        }
        eng_a.position = fen
        eng_a.variations = {engine_name: [(d[1], d[3]) for d in lines]}

        # The write to analysis file will be done here.
        asd = self.analysis_data_source
        if asd:
            records = asd.get_position_analysis_records(eng_a.position)
            for rec in records:
                if engine_name in rec.value.scale:
                    erc = rec.clone()
                    erc.value.scale.update(eng_a.scale)
                    erc.value.variations.update(eng_a.variations)
                    inserter = RecordEdit(erc, rec)
                    inserter.set_data_source(asd, inserter.on_data_change)
                    inserter.edit()
                    break
            else:
                if records:
                    rec = records[-1]
                    erc = rec.clone()
                    erc.value.scale.update(eng_a.scale)
                    erc.value.variations.update(eng_a.variations)
                    inserter = RecordEdit(erc, rec)
                    inserter.set_data_source(asd, inserter.on_data_change)
                    inserter.edit()
                else:
                    value = self.analysis_record.value
                    value.empty()
                    value.scale = eng_a.scale
                    value.position = eng_a.position
                    value.variations = eng_a.variations
                    inserter = RecordEdit(self.analysis_record, None)
                    inserter.set_data_source(asd, None)
                    self.analysis_record.set_database(
                        inserter.get_data_source().dbhome
                    )
                    self.analysis_record.key.recno = None  # 0
                    inserter.put()
        else:
            pos_a = self.position_analysis.setdefault(eng_a.position, eng_a)
            if pos_a is not eng_a:
                pos_a.scale.update(eng_a.scale)
                pos_a.variations.update(eng_a.variations)

    def set_position_analysis_data_source(self, datasource=None):
        """Link database analysis reader to open database."""
        self.analysis_data_source = datasource
        if datasource is None:
            self.analysis_record.set_database(None)
        else:
            self.analysis_record.set_database(datasource.get_database())

    def is_positions_pending_empty(self):
        """Return True if no positions are in the queue for analysis."""
        for pending in self.positions_pending.values():
            for value in pending.values():
                if len(value):
                    return False
        return True


def run_driver(to_driver_queue, to_ui_queue, path, args, ui_name):
    """Start UCI chess engine and loop sending queued resuests to engine."""
    driver = UCIDriverOverTCP(to_ui_queue, ui_name)
    try:
        driver.start_engine(path, args)
    except Exception as error:
        to_ui_queue.put(("start failed", (ui_name,)))
        raise UCIStartEngineError(
            ui_name.join(("Start ", " failed"))
        ) from error
    to_ui_queue.put(("started", (ui_name,)))
    while True:
        command = to_driver_queue.get()
        if command == CommandsToEngine.quit_:
            break
        driver.send_to_engine(command)
    driver.quit_engine()
