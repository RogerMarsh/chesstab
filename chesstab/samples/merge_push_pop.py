# merge_push_pop.py
# Copyright 2024 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Merge sorted index sequential files with heapq.heappush and heapq.heappop.

Compare with .merge_merge module.

The Merge.sorter() method is more complicated.

The literal_eval operation is done once per item.  This saves a lot of time.

The input streams are opened at start of merge and each is closed as soon
as it signals it has no more items.

The saved time, about 30 seconds for about 1,900 games, cannot be ignored
because this run takes just under 40 seconds.

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


class Merge:
    """Merge index files in directories."""

    def __init__(self, table, index, dumps):
        """Set merge file names."""
        self.readers = {
            name: Reader(os.path.join(table, index, name)) for name in dumps
        }

    def sorter(self):
        """Yield lines in sorted order."""
        heappush = heapq.heappush
        heappop = heapq.heappop
        empty = set()
        items = []
        for name, reader in self.readers.items():
            reader.open_file()
            line = reader.file.readline()
            if not line:
                reader.file.close()
                empty.add(name)
                continue
            heappush(items, (literal_eval(line), name))
        for name in empty:
            del self.readers[name]
        readers = self.readers
        while True:
            try:
                item, name = heappop(items)
            except IndexError:
                break
            yield item
            line = readers[name].file.readline()
            if not line:
                readers[name].file.close()
                del self.readers[name]
                continue
            heappush(items, (literal_eval(line), name))


def run_merge(merge_games):
    """Run merge on directory merge_games."""
    merge_directories = [
        name
        for name in os.listdir(merge_games)
        if os.path.isdir(os.path.join(merge_games, name))
    ]
    print()
    print("merge_push_pop")
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
            count += 1
        print(format(count, ","), directory)
    time_end = time.monotonic_ns()
    print()
    print(format((time_end - time_start) / 1000000000, ",.2f"), "seconds")
    print()


if __name__ == "__main__":
    merge_games = tkinter.filedialog.askdirectory(title="merge_push_pop")
    if merge_games:
        run_merge(merge_games)
