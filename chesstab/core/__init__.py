"""Data manipulation for chess game data and access to databases.

The data access methods are independent from any particular database engine,
but the design assumes the "key:value" structure used in Berkeley DB.

The sibling packages apsw, db, dpt, and sqlite, use the methods provided by the
solentware_base package interfaces to Berkeley DB, DPT, and Sqlite3, to
implement the "key:value" structure.
"""
