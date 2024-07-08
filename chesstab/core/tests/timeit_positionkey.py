# timeit_positionkey.py
# Copyright 2024 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Timing positionkey generation.

strkey() is fastest of positionkey methods, but it is assumed the cost of a
constant length 64 byte key compared with a (8 + <number pieces>) byte key
when updating large databases is more than saving 3 seconds per million
positionkey calculations.

Noteworthy to say moveset() is fastest of move..() methods at 3.10 and 3.11.

There is a case for not making the changes done in core.pgn module because
the difference is less than a second per million positionkeys while changing
from 3.10 to 3.11 saves 6 seconds per million.

"""
import re

from pgn_read.core import game
from pgn_read.core.piece import Piece
from pgn_read.core.constants import RANK_NAMES, FILE_NAMES

test_game = game.Game()
for sqr, pce in zip(
    (
        "a8", "e8", "h8", "a7", "b7", "c7", "d7", "f7", "g7", "h7",
        "d6", "f6", "d5", "e5", "c4", "e4", "c3", "e3", "f3", "a2",
        "b2", "f2", "h2", "a1", "e1",
    ),
    "rkrpppqpppbnPpQPNBPPPPPRK",
):
    test_game._piece_placement_data[sqr] = Piece(pce, sqr)
test_game._active_color = "w"


def keyold():
    pieces = [""] * 64
    bits = []
    for piece in test_game._piece_placement_data.values():
        piece_square = piece.square
        pieces[piece_square.number] = piece.name
        bits.append(piece_square.bit)
    return "".join(
        (
            sum(bits).to_bytes(8, "big").decode("iso-8859-1"),
            "".join(pieces),
            "w",
            "KQkq",
            "-",
        )
    )


def moveset():
    pieces = [""] * 64
    piecemovekeys = []
    for piece in test_game._piece_placement_data.values():
        pieces[piece.square.number] = piece.name
    for piece_name in set("".join(pieces)):
        piecemovekeys.append("cc" + piece_name)
    return piecemovekeys


pairs = re.compile(r"[KQRBNP]{2}", flags=re.IGNORECASE)


chrnum = 32
pairlookup = {}
piecenames = "KQRBNPkqrbnp"
for one in piecenames:
    for two in piecenames:
        paircode = chr(chrnum)
        while True:
            if paircode in piecenames:
                chrnum += 1
                paircode = chr(chrnum)
                continue
            break
        pairlookup[one + two] = paircode
        chrnum += 1


def replpair(matchobj):
    return pairlookup[matchobj.group()]


def keynew():
    pieces = [""] * 64
    bits = []
    for piece in test_game._piece_placement_data.values():
        piece_square = piece.square
        pieces[piece_square.number] = piece.name
        bits.append(piece_square.bit)
    return "".join(
        (
            sum(bits).to_bytes(8, "big").decode("iso-8859-1"),
            pairs.sub(replpair, "".join(pieces)),
            "w",
            "KQkq",
            "-",
        )
    )


def pairwise(string):
    iternext = iter(string)
    try:
        while True:
            yield pairlookup[next(iternext) + next(iternext)]
    except StopIteration:
        if len(string) % 2 == 1:
            yield string[-1]


def xpairwise(string):
    for pair in zip(*[iter(string)] * 2):
        yield pairlookup["".join(pair)]
    if len(string) % 2 == 1:
        yield string[-1]


def keypair():
    pieces = [""] * 64
    bits = []
    for piece in test_game._piece_placement_data.values():
        piece_square = piece.square
        pieces[piece_square.number] = piece.name
        bits.append(piece_square.bit)
    return "".join(
        (
            sum(bits).to_bytes(8, "big").decode("iso-8859-1"),
            "".join(two for two in pairwise("".join(pieces))),
            "w",
            "KQkq",
            "-",
        )
    )


spaces = re.compile(r"\s+")


def lenspc(matchobj):
    return str(len(matchobj.group()))


def fenkey():
    pieces = [" "] * 64
    for piece in test_game._piece_placement_data.values():
        pieces[piece.square.number] = piece.name
    return "".join(
        (
            spaces.sub(lenspc, "".join(pieces)),
            "w",
            "KQkq",
            "-",
        )
    )


def strkey():
    pieces = [" "] * 64
    for piece in test_game._piece_placement_data.values():
        pieces[piece.square.number] = piece.name
    return "".join(
        (
            "".join(pieces),
            "w",
            "KQkq",
            "-",
        )
    )


def replkey():
    pieces = [" "] * 64
    for piece in test_game._piece_placement_data.values():
        pieces[piece.square.number] = piece.name
    return "".join(
        (
            "".join(pieces),
            "w",
            "KQkq",
            "-",
        )
    ).replace("  ", "a")


def fen():
    rank = 0
    file = -1
    chars = []
    for piece in sorted(test_game._piece_placement_data.values()):
        piece_rank = RANK_NAMES.index(piece.square.rank)
        piece_file = FILE_NAMES.index(piece.square.file)
        if piece_rank != rank:
            if file != 7:
                chars.append(str(7 - file))
            chars.append("/")
            while True:
                rank += 1
                if piece_rank == rank:
                    file = -1
                    break
                chars.append("8/")
            else:
                continue
        if piece_file != file:
            if piece_file - file > 1:
                chars.append(str(piece_file - file - 1))
            chars.append(piece.name)
            file = piece_file
        else:
            chars.append(piece.name)
    if file != 7:
        chars.append(str(7 - file))
    while True:
        if rank == 7:
            break
        chars.append("/8")
        rank += 1
    fen = " ".join(
        (
            "".join(chars),
            "w",
            "KQkq",
            "-",
            "5",
            "14",
        )
    )


def keysort():
    pieces = sorted(test_game._piece_placement_data.values())
    return "".join(
        (
            sum(piece.square.bit for piece in pieces).to_bytes(8, "big").decode("iso-8859-1"),
            "".join(piece.name for piece in pieces),
            "w",
            "KQkq",
            "-",
        )
    )


def keyalt():
    pieces = [""] * 64
    bits = 0
    for piece in test_game._piece_placement_data.values():
        piece_square = piece.square
        pieces[piece_square.number] = piece.name
        bits += piece_square.bit
    return "".join(
        (
            bits.to_bytes(8, "big").decode("iso-8859-1"),
            "".join(pieces),
            "w",
            "KQkq",
            "-",
        )
    )


def movestr():
    pieces = [""] * 64
    piecemovekeys = []
    for piece in test_game._piece_placement_data.values():
        pieces[piece.square.number] = piece.name
    for piece_name in "".join(pieces):
        piecemovekeys.append("cc" + piece_name)
    return piecemovekeys


def movelist():
    pieces = [""] * 64
    piecemovekeys = []
    for piece in test_game._piece_placement_data.values():
        pieces[piece.square.number] = piece.name
    for piece_name in list("".join(pieces)):
        piecemovekeys.append("cc" + piece_name)
    return piecemovekeys


def movetup():
    pieces = [""] * 64
    piecemovekeys = []
    for piece in test_game._piece_placement_data.values():
        pieces[piece.square.number] = piece.name
    for piece_name in tuple("".join(pieces)):
        piecemovekeys.append("cc" + piece_name)
    return piecemovekeys


def moveif():
    pieces = [""] * 64
    for piece in test_game._piece_placement_data.values():
        pieces[piece.square.number] = piece.name
    piecemovekeys = ["cc" + piece_name for piece_name in pieces if piece_name]
    return piecemovekeys


if __name__ == "__main__":

    import timeit
    old = keyold()
    sort = keysort()
    alt = keyalt()
    mold = moveset()
    mstr = movestr()
    mlist = movelist()
    mtup = movetup()
    mif = moveif()
    assert old == sort and sort == alt
    assert set(mold) == set(mstr)
    assert set(mold) == set(mlist)
    assert set(mold) == set(mtup)
    assert set(mold) == set(mif)
    print("key is", repr(old))
    print("keyold")
    print(timeit.timeit("keyold()", setup="from __main__ import keyold"))
    print("keynew")
    print(timeit.timeit("keynew()", setup="from __main__ import keynew"))
    print("keypair")
    print(timeit.timeit("keypair()", setup="from __main__ import keypair"))
    print("fen")
    print(timeit.timeit("fen()", setup="from __main__ import fen"))
    print("fenkey")
    print(timeit.timeit("fenkey()", setup="from __main__ import fenkey"))
    print("strkey")
    print(timeit.timeit("strkey()", setup="from __main__ import strkey"))
    print("replkey")
    print(timeit.timeit("replkey()", setup="from __main__ import replkey"))
    print("keysort")
    print(timeit.timeit("keysort()", setup="from __main__ import keysort"))
    print("keyalt")
    print(timeit.timeit("keyalt()", setup="from __main__ import keyalt"))
    print("moveset")
    print(timeit.timeit("moveset()", setup="from __main__ import moveset"))
    print("movestr")
    print(timeit.timeit("movestr()", setup="from __main__ import movestr"))
    print("movelist")
    print(timeit.timeit("movelist()", setup="from __main__ import movelist"))
    print("movetup")
    print(timeit.timeit("movetup()", setup="from __main__ import movetup"))
    print("moveif")
    print(timeit.timeit("moveif()", setup="from __main__ import moveif"))
