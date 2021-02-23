==========================
ChessTab - Selection Rules
==========================

.. contents::


Introduction
============

Selection rules can be created for the list of games on a database.

The rule "White eq Green, John or Black eq Green, John" would list just the games on the database played by "Green, John" rather than all the games on the databsae.

"White" and "Black" are two of the seven tag names in the Seven Tag Roster defined by the PGN standard.  The tag names in the Seven Tag Roster are the ones which can be used in selection rules.

"Green, John" is a plausible value of a "White" or "Black" tag pair.

"eq" is one of the conditions that the tag value should meet for the game to be included in the list.

"or" is one of the operators used to say how conditions are combined to build the list of games.


Conditions
==========

These conditions are written "<tag name> <condition> <tag value>": an example is "Black eq Green, John".

eq
ne
lt
le
gt
ge
after
before

These conditions are used to specify ranges of values:

from
below
to
above

The combinations are illustrated using the "Date" tag:

"Date from 2012.04.15 to 2016.02.21"
"Date above 2012.04.15 to 2016.02.21"
"Date from 2012.04.15 below 2016.02.21"
"Date above 2012.04.15 below 2016.02.21"

"from" and "to" include games with the value in the list, "above" and "below" exclude them.

These conditions are mentioned to complete the list of conditions.

is
like
present

"like" is similar to the Filter button in action, except the value is seen as a regular expression rather than the characters at the start of the values of interest.  "Date like .{4}\.11\..{2}" will list games played in any November.

"result is 1-0" and "result present" illustrate the use of "is" and "present".

"not" can be added to a condition to select records which do not meet the condition.

"is" is different from the other conditions because the expression using "not" is "result is not 1-0".  All the other conditions put the "not" before the condition: "Black not eq Green, John" for example.


Operators
=========

In decreasing priority order (nor done first):

nor
and
or

The operators "and", "or", and "nor", are used to combine conditions: "White eq Green, John and Black eq Green, John" will list all games where both players are named "Green, John".

"not" can be added after an operator to combine the records which neet the preceding condition with those which do not match the following condition:
"White eq Green, John and not Black eq Green, John" for example.

"not" is applied to a condition before "nor", "and", and "or".

Parentheses, "(" and ")", can be placed around a sequence of conditions to override the normal priority order of the operators connecting them.  The conditions within the parentheses are evaluated first.


Keywords in values
==================

The conditions and operators can occur in values, or field names in fact: for example 'meal eq fish and chips'.

The 'and' would be seen as an operator, leaving 'chips' as nonsense.

Write the condition as "meal eq fish' and 'chips" to see the value as 'fish and chips'.

The apostrophies are as close as can be to the "and": the value is seen as 'fishandchips' when written as "meal eq fish 'and' chips".

The apostrophies can be further away: in "meal eq 'fish and chips'" they are as far as possible from the "and" yet still see the value as 'fish and chips'.

A single apostrophy is fine: in "name eq O'Neill" value is seen as "O'Neill".


Sorting
=======

Two keywords are defined for sorting:

alpha
num

They are not implemented but have to be mentioned in case they get used as part of a field name or value.  These need to be hidden by apostrophies too.
