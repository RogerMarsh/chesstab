# merge_merge.py
# Copyright 2024 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Merge sorted index sequential files with heapq.merge.

Compare with .merge_push_pop module.

The Merge.sorter() method is simpler and clearer.

The literal_eval operation is done at least twice, at least once sorting in
heapq.merge (documentation does not say the sortkey function is evaluated
once per item) and once when delivering the item to consumer.  This costs
a lot of time.

The input streams are opened at start of merge and all are kept open until
merge is finished.

The extra time, about 30 seconds for about 1,900 games, cannot be ignored
because this run takes just under 70 seconds.

The segment size is 16 bytes and about 850 games were on the database.

"""

import os
import heapq
from ast import literal_eval
import time
import tkinter.filedialog


class Reader:
    """Yield lines read from dump_file."""

    def __init__(self, dump_file):
        """Set dump file name."""
        self.dump_file = dump_file
        self.file = None

    def open_file(self):
        """Yield line read from file."""
        self.file = open(self.dump_file, mode="r", encoding="utf-8")
        return self.file


class Merge:
    """Merge index files in directories."""

    def __init__(self, table, index, dumps):
        """Set merge file names."""
        self.readers = [
            Reader(os.path.join(table, index, name)) for name in dumps
        ]

    def sortkey(self, item):
        """Return sort key for line."""
        return literal_eval(item)

    def sorter(self):
        """Yield lines in sorted order."""
        readers = [reader.open_file() for reader in self.readers]
        merge = heapq.merge
        try:
            for item in merge(*readers, key=self.sortkey):
                yield item
        finally:
            for reader in self.readers:
                reader.file.close()


def run_merge(merge_games):
    """Run merge on directory merge_games."""
    merge_directories = [
        name
        for name in os.listdir(merge_games)
        if os.path.isdir(os.path.join(merge_games, name))
    ]
    print()
    print("merge_merge")
    print()
    time_start = time.monotonic_ns()
    for directory in merge_directories:
        merge = Merge(
            merge_games,
            directory,
            [
                name
                for name in os.listdir(os.path.join(merge_games, directory))
                if (
                    (name == directory or name.isdigit())
                    and os.path.isfile(
                        os.path.join(merge_games, directory, name)
                    )
                )
            ],
        )
        count = 0
        for item in merge.sorter():
            literal_eval(item)
            count += 1
        print(format(count, ","), directory)
    time_end = time.monotonic_ns()
    print()
    print(format((time_end - time_start) / 1000000000, ",.2f"), "seconds")
    print()


if __name__ == "__main__":
    merge_games = tkinter.filedialog.askdirectory(title="merge_merge")
    if merge_games:
        run_merge(merge_games)
