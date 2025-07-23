# directions.py
# Copyright 2025 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Classes to evaluate direction filters."""

import chessql.core.filters

from . import symbol


class Up(symbol.Symbol):
    """Evaluate Up filter."""

    def __init__(self, *args):
        """Initialise an Up instance."""
        super().__init__(*args)
        self._verify_token_is(chessql.core.filters.Up)


class Down(symbol.Symbol):
    """Evaluate Down filter."""

    def __init__(self, *args):
        """Initialise a Down instance."""
        super().__init__(*args)
        self._verify_token_is(chessql.core.filters.Down)


class Right(symbol.Symbol):
    """Evaluate Right filter."""

    def __init__(self, *args):
        """Initialise a Right instance."""
        super().__init__(*args)
        self._verify_token_is(chessql.core.filters.Right)


class Left(symbol.Symbol):
    """Evaluate Left filter."""

    def __init__(self, *args):
        """Initialise a Left instance."""
        super().__init__(*args)
        self._verify_token_is(chessql.core.filters.Left)


class Northeast(symbol.Symbol):
    """Evaluate Northeast filter."""

    def __init__(self, *args):
        """Initialise a Northeast instance."""
        super().__init__(*args)
        self._verify_token_is(chessql.core.filters.Northeast)


class Northwest(symbol.Symbol):
    """Evaluate Northwest filter."""

    def __init__(self, *args):
        """Initialise a Northwest instance."""
        super().__init__(*args)
        self._verify_token_is(chessql.core.filters.Northwest)


class Southeast(symbol.Symbol):
    """Evaluate Southeast filter."""

    def __init__(self, *args):
        """Initialise a Southeast instance."""
        super().__init__(*args)
        self._verify_token_is(chessql.core.filters.Southeast)


class Southwest(symbol.Symbol):
    """Evaluate Southwest filter."""

    def __init__(self, *args):
        """Initialise a Southwest instance."""
        super().__init__(*args)
        self._verify_token_is(chessql.core.filters.Southwest)


class Diagonal(symbol.Symbol):
    """Evaluate Diagonal filter."""

    def __init__(self, *args):
        """Initialise a Diagonal instance."""
        super().__init__(*args)
        self._verify_token_is(chessql.core.filters.Diagonal)


class Orthogonal(symbol.Symbol):
    """Evaluate Orthogonal filter."""

    def __init__(self, *args):
        """Initialise an Orthogonal instance."""
        super().__init__(*args)
        self._verify_token_is(chessql.core.filters.Orthogonal)


class Vertical(symbol.Symbol):
    """Evaluate Vertical filter."""

    def __init__(self, *args):
        """Initialise a Vertical instance."""
        super().__init__(*args)
        self._verify_token_is(chessql.core.filters.Vertical)


class Horizontal(symbol.Symbol):
    """Evaluate Horizontal filter."""

    def __init__(self, *args):
        """Initialise a Horizontal instance."""
        super().__init__(*args)
        self._verify_token_is(chessql.core.filters.Horizontal)


class AnyDirection(symbol.Symbol):
    """Evaluate AnyDirection filter."""

    def __init__(self, *args):
        """Initialise an AnyDirection instance."""
        super().__init__(*args)
        self._verify_token_is(chessql.core.filters.AnyDirection)


class MainDiagonal(symbol.Symbol):
    """Evaluate MainDiagonal filter."""

    def __init__(self, *args):
        """Initialise a MainDiagonal instance."""
        super().__init__(*args)
        self._verify_token_is(chessql.core.filters.MainDiagonal)


class OffDiagonal(symbol.Symbol):
    """Evaluate OffDiagonal filter."""

    def __init__(self, *args):
        """Initialise a OffDiagonal instance."""
        super().__init__(*args)
        self._verify_token_is(chessql.core.filters.OffDiagonal)
