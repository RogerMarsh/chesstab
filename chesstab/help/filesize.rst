===================
ChessTab - Filesize
===================


Some points on data storage that depend on the database engine in use are described.

 The database engines which can be used are:
  - Berkeley DB
  - dptdb
  - apsw
  - sqlite3

 ChessTab will use sqlite3 (supplied with Python) unless any or all bsddb3 (the Berkeley DB interface), apsw (an alternative sqlite3 interface), and dptdb (the dptdb interface) are installed.

 Berkeley DB, apsw, and sqlite3 will look after themselves.

 dptdb is built from part of DPT.  DPT is no longer available, but the part used in dptdb was available as a separate source download until DPT expired.


A dptdb database for a sample 1.5 million games occupies about 11 Gbytes and the Berkeley DB database containing the same games occupies about 30 Gbytes.  It is not known how much space is required by a sqlite3 database.  These figures were obtained using a ChessTab built for Python2.7.

The figure for Berkeley DB using a ChessTab built on Python3.3, or later, will probably be significantly lower.

The 1.5 million game database referred to, as an example, was built from the Enormous PGN database downloaded from ftp://ftp.cis.uab.edu/pub/hyatt/pgn.


The rest of this document is about dptdb file sizes.

 The dptdb database engine uses files that have a definite size which does not depend on the number of records that exist on the file.  In other words files are created big enough to hold a specific number of records given a typical size for a record.  The file can be increased in size later if necessary but adding, deleting, or editing records does not change the size of the file.

 Space on a dptdb file is dedicated to data or indexes.

 ChessTab will check if data or index space is getting low when it opens a file and increase either, or both, the data and index areas if necessary.

 ChessTab will estimate the data and index space needed for an import of a PGN file and increase either, or both, the data and index areas if necessary before doing the import.  The import dialogue will give details of what will be done.

 The import dialogue provides the ability to increase the data or index space (by clicking the appropriate button).  Each use doubles the amount of free space, unless the free space exceeds the amount estimated to be needed for the import when the free space is increased by the estimated amount needed.

 The DPT database engine has a large, but finite, number of slots for recording increases in data or index size.  If, say, the last slot used describes an increase in data size and an increase in data size is requested that slot is reused and the two increases are merged.  The possibility of reusing a slot is the reason you may be asked to consider doing the other kind of increase first if you intend to do such an increase shortly.

 For chess databases containing over 20000 typical game scores without comments or variations about 8 pages of index are needed for every 1 page of data (1 page is 8k bytes).  A maximum of 10 games (1 record per game) is allowed on each data page.

 The index to data ratio gets larger below 20000 games, reaching 17 to 1 at about 500 games, and it may be wrong to make general statements like this for small databases.

 ChessTab creates a database sized to hold 10000 games. 800 pages of index are thrown in to compensate for the 8 to 1 ratio, incorrect at this size, used for estimating space requirements.
