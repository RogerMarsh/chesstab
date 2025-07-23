# parameters.py
# Copyright 2025 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Classes to evaluate filter parameters."""

import chessql.core.filters

from . import symbol


class UpParameter(symbol.Symbol):
    """Evaluate UpParameter parameter."""

    def __init__(self, *args):
        """Initialise an UpParameter instance."""
        super().__init__(*args)
        self._verify_token_is(chessql.core.filters.UpParameter)


class DownParameter(symbol.Symbol):
    """Evaluate DownParameter parameter."""

    def __init__(self, *args):
        """Initialise a DownParameter instance."""
        super().__init__(*args)
        self._verify_token_is(chessql.core.filters.DownParameter)


class RightParameter(symbol.Symbol):
    """Evaluate RightParameter parameter."""

    def __init__(self, *args):
        """Initialise a RightParameter instance."""
        super().__init__(*args)
        self._verify_token_is(chessql.core.filters.RightParameter)


class LeftParameter(symbol.Symbol):
    """Evaluate LeftParameter parameter."""

    def __init__(self, *args):
        """Initialise a LeftParameter instance."""
        super().__init__(*args)
        self._verify_token_is(chessql.core.filters.LeftParameter)


class NortheastParameter(symbol.Symbol):
    """Evaluate NortheastParameter parameter."""

    def __init__(self, *args):
        """Initialise a NortheastParameter instance."""
        super().__init__(*args)
        self._verify_token_is(chessql.core.filters.NortheastParameter)


class NorthwestParameter(symbol.Symbol):
    """Evaluate NorthwestParameter parameter."""

    def __init__(self, *args):
        """Initialise a NorthwestParameter instance."""
        super().__init__(*args)
        self._verify_token_is(chessql.core.filters.NorthwestParameter)


class SoutheastParameter(symbol.Symbol):
    """Evaluate SoutheastParameter parameter."""

    def __init__(self, *args):
        """Initialise a SoutheastParameter instance."""
        super().__init__(*args)
        self._verify_token_is(chessql.core.filters.SoutheastParameter)


class SouthwestParameter(symbol.Symbol):
    """Evaluate SouthwestParameter parameter."""

    def __init__(self, *args):
        """Initialise a SouthwestParameter instance."""
        super().__init__(*args)
        self._verify_token_is(chessql.core.filters.SouthwestParameter)


class DiagonalParameter(symbol.Symbol):
    """Evaluate DiagonalParameter parameter."""

    def __init__(self, *args):
        """Initialise a DiagonalParameter instance."""
        super().__init__(*args)
        self._verify_token_is(chessql.core.filters.DiagonalParameter)


class OrthogonalParameter(symbol.Symbol):
    """Evaluate OrthogonalParameter parameter."""

    def __init__(self, *args):
        """Initialise an OrthogonalParameter instance."""
        super().__init__(*args)
        self._verify_token_is(chessql.core.filters.OrthogonalParameter)


class VerticalParameter(symbol.Symbol):
    """Evaluate VerticalParameter parameter."""

    def __init__(self, *args):
        """Initialise a VerticalParameter instance."""
        super().__init__(*args)
        self._verify_token_is(chessql.core.filters.VerticalParameter)


class HorizontalParameter(symbol.Symbol):
    """Evaluate HorizontalParameter parameter."""

    def __init__(self, *args):
        """Initialise a HorizontalParameter instance."""
        super().__init__(*args)
        self._verify_token_is(chessql.core.filters.HorizontalParameter)


class AnyDirectionParameter(symbol.Symbol):
    """Evaluate AnyDirectionParameter parameter."""

    def __init__(self, *args):
        """Initialise an AnyDirectionParameter instance."""
        super().__init__(*args)
        self._verify_token_is(chessql.core.filters.AnyDirectionParameter)


class MainDiagonalParameter(symbol.Symbol):
    """Evaluate MainDiagonalParameter parameter."""

    def __init__(self, *args):
        """Initialise a MainDiagonalParameter instance."""
        super().__init__(*args)
        self._verify_token_is(chessql.core.filters.MainDiagonalParameter)


class OffDiagonalParameter(symbol.Symbol):
    """Evaluate OffDiagonalParameter parameter."""

    def __init__(self, *args):
        """Initialise a OffDiagonalParameter instance."""
        super().__init__(*args)
        self._verify_token_is(chessql.core.filters.OffDiagonalParameter)


class FromParameter(symbol.Symbol):
    """Evaluate FromParameter parameter."""

    def __init__(self, *args):
        """Initialise a FromParameter instance."""
        super().__init__(*args)
        self._verify_token_is(chessql.core.filters.FromParameter)


class ToParameter(symbol.Symbol):
    """Evaluate FromParameter parameter."""

    def __init__(self, *args):
        """Initialise a ToParameter instance."""
        super().__init__(*args)
        self._verify_token_is(chessql.core.filters.ToParameter)


class Through(symbol.Symbol):
    """Evaluate Through parameter."""

    def __init__(self, *args):
        """Initialise a Through instance."""
        super().__init__(*args)
        self._verify_token_is(chessql.core.filters.Through)
