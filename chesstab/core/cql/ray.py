# ray.py
# Copyright 2017 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Chess Query Language (ChessQL) ray filter evaluator.

Examples of ray filters are 'ray ( Q n k )' and 'ray ( Q[a4,c3] n kh1-8 )'.

RayFilter expands the list of square descriptions into the particular rays,
horizontal, vertical, and diagonal, which need to be evaluated.

The CQL definition of ray filter allows any set filter, not just piece
designators, in the ray filter.  For example ray ( Q up 1 n k).

The RayFilter class ignores, at best, other set filters: in the example
'up 1 n' is treated as 'n' ignoring the 'up' filter.

"""
from chessql.core import filters

from . import symbol
from . import ray_squares
from . import ray_map
from . import emptydesignator


class Ray(symbol.Symbol):
    """ChessQL ray filter evaluation class."""

    def __init__(self, *args):
        """Initialize to apply filter_ on move key."""
        super().__init__(*args)
        self._verify_token_is(filters.Ray)
        self._map_ray_sets_to_squares = None

    def prepare_to_evaluate_symbol(self):
        """Delegate, then pick rays to be evaluated by 'ray' filter.

        For example 'ray(R b k p)' must evaluate all lines at least four
        squares long in all directions.  Changing 'R' to 'Rc4' restricts
        the lines considered to those starting at 'c4'.

        """
        super().prepare_to_evaluate_symbol()
        children = self.master.children
        minimum_squares = len(children)
        first_set = children[0].node
        last_set = children[-1].node
        internal_sets = [c.node for c in children[1:-1]]
        map_ray_sets_to_squares = []
        ray_square_map = ray_map.RAY_MAP

        # The parameters are available in the text matched by the pattern
        # for the 'ray' filter.
        direction_parameters = [
            ray_squares.get_direction_class(n)
            for n in self._token.match_.group().rstrip("(").split()[1:]
        ]

        get_ray_squares = ray_squares.get_ray_squares
        for first in first_set.designator_squares:
            for last in last_set.designator_squares:
                squares = get_ray_squares(
                    first, last, direction_parameters=direction_parameters
                )
                if len(squares) < minimum_squares:
                    continue
                for item in ray_square_map[minimum_squares, len(squares)]:
                    internal = [squares[i] for i in item]
                    if [
                        i
                        for i, j in zip(internal, internal_sets)
                        if i in j.designator_squares
                    ] != internal:
                        continue
                    set_squares = [squares[0]] + internal + [squares[-1]]
                    map_ray_sets_to_squares.append(
                        (set_squares, set(squares).difference(set_squares))
                    )
        self._map_ray_sets_to_squares = map_ray_sets_to_squares

    def evaluate_symbol(self, cqlfinder, movenumber, cache, constraint=None):
        """Set constraints for child filters and delegate.

        A ray has many sub-rays, one for each possible combination of
        start and end square.  Each sub-ray must be evaluated with the
        relevant constraints.  The answers for each sub-ray are combined
        to give the full answer.

        """
        key = (constraint, self)
        data = cache.get(key)
        if data is not None:
            self._data = data
            return
        empty_designator_class = emptydesignator.EmptyDesignator
        ray_answer = cqlfinder.db.recordlist_nil(cqlfinder.dbset)
        for ray_set, squares in self._map_ray_sets_to_squares:
            if constraint and constraint != ray_set[-1]:
                continue
            subray_answer = cqlfinder.db.recordlist_ebm(cqlfinder.dbset)
            for square, child in zip(ray_set, self.master.children):
                child.node.evaluate_symbol(
                    cqlfinder, movenumber, cache, constraint=square
                )
                subray_answer &= child.node.data
                if not subray_answer:
                    break
            if subray_answer:
                for square in squares:  # The squares which must be empty.
                    empty = empty_designator_class(square, self.master)
                    empty.expand_symbol()
                    empty.evaluate_symbol(cqlfinder, movenumber, cache)
                    subray_answer &= empty.data
                    if not subray_answer:
                        break
                if subray_answer:
                    ray_answer |= subray_answer
        cache[key] = ray_answer
        self._data = ray_answer

    @property
    def designator_set(self):
        """Return the piece designator set for the ray filter."""
        return self.master.children[-1].node.designator_set

    @property
    def designator_squares(self):
        """Return the set of squares represented by the ray filter."""
        return self.master.children[-1].node.designator_squares
