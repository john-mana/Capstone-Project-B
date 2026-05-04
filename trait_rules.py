"""
Shared logic for deriving working_value and source_code from original_value.
Used by both:
  - generate_junction_sql.py (when adding new data from AusTraits)
  - rebuild_from_original.py (when fixing existing DB rows)

  - Pick 1st value (Dorothy simplified rule for all types)
  - Strip vote markers like (1), (2), (V)
  - For date types, convert Y/n to month letters
  - source_code values:
      'v' = AusTraits highest vote (single winner)
      'v1' = equal votes, took 1st
      'a' = AI result (comma-separated, no votes)
      number = single value with that vote count
      None = single value with no vote info
"""

import pandas as pd
import re

# source codes that should never be touched (derived, not from original_value)
PROTECTED_SOURCES = {'g', 'f', 'm', 'a'}


def convert_date_string(s):
    """
    Convert 12-char Y/n string to month letters.
    Position 1=J(an), 2=F(eb), 3=M(ar), 4=A(pr), 5=M(ay), 6=J(un),
             7=J(ul), 8=A(ug), 9=S(ep), 10=O(ct), 11=N(ov), 12=D(ec).
    Example: "nnnnnnyyynn" -> "nnnnnnJASnn"
    """
    if s is None or pd.isna(s):
        return s
    s = str(s).strip()
    if len(s) != 12:
        return s
    months = ['J', 'F', 'M', 'A', 'M', 'J', 'J', 'A', 'S', 'O', 'N', 'D']
    result = []
    for i, ch in enumerate(s):
        if ch.lower() == 'y':
            result.append(months[i])
        else:
            result.append('n')
    return ''.join(result)


def parse_value_with_vote(piece):
    """
    Parse a piece like 'tree (12)' into (value='tree', vote=12).
    If no vote marker, returns (value, None).
    """
    piece = piece.strip()
    # match: value followed by space + (number)
    match = re.match(r'^(.*?)\s*\((\d+)\)\s*$', piece)
    if match:
        return match.group(1).strip(), int(match.group(2))
    # match: value followed by space + (V)
    match = re.match(r'^(.*?)\s*\(V\)\s*$', piece, re.IGNORECASE)
    if match:
        return match.group(1).strip(), None
    # no vote marker
    return piece, None


def derive_from_original(original_value, trait_type):
    """
    Apply Dorothy's rules to original_value.
    Returns (working_value, source_code).
    Returns (None, None) if cannot derive.

    Examples:
      ("yellow_orange (1)", "cat.") -> ("yellow_orange", "1")
      ("shrub (4); tree (12)", "cat.") -> ("tree", "v")
      ("tree (4); shrub (4)", "cat.") -> ("tree", "v1")
      ("red, scarlet", "cat.") -> ("red", "a")
      ("nnnnnnyyynn", "date") -> ("nnnnnnJASnn", None)
      ("nnnnnyyy (3); nnnnyyyy (1)", "date") -> ("nnnnnJAS", "v")
    """
    if original_value is None or pd.isna(original_value):
        return None, None

    text = str(original_value).strip()
    if not text:
        return None, None

    # split into pieces
    if ';' in text:
        pieces = [p.strip() for p in text.split(';') if p.strip()]
    elif ',' in text and '(' not in text:
        # comma-separated AI case (no votes)
        pieces = [p.strip() for p in text.split(',') if p.strip()]
        if pieces:
            first_value = pieces[0]
            if trait_type == 'date':
                first_value = convert_date_string(first_value)
            return first_value, 'a'
        return None, None
    else:
        pieces = [text]

    # parse each piece into (value, vote)
    parsed = [parse_value_with_vote(p) for p in pieces]

    # single value
    if len(parsed) == 1:
        value, vote = parsed[0]
        working = value
        if trait_type == 'date':
            working = convert_date_string(working)
        source = str(vote) if vote is not None else None
        return working, source

    # multiple values - find highest vote
    votes = [v for _, v in parsed]
    if all(v is None for v in votes):
        # no votes at all - just pick 1st
        value, _ = parsed[0]
        working = value
        if trait_type == 'date':
            working = convert_date_string(working)
        return working, None

    max_vote = max((v for v in votes if v is not None), default=None)
    if max_vote is None:
        value, _ = parsed[0]
        working = value
        if trait_type == 'date':
            working = convert_date_string(working)
        return working, None

    # which pieces have the max vote?
    max_indices = [i for i, (_, v) in enumerate(parsed) if v == max_vote]

    if len(max_indices) == 1:
        # single highest vote
        value, _ = parsed[max_indices[0]]
        working = value
        if trait_type == 'date':
            working = convert_date_string(working)
        return working, 'v'
    else:
        # equal votes - pick 1st
        value, _ = parsed[max_indices[0]]
        working = value
        if trait_type == 'date':
            working = convert_date_string(working)
        return working, 'v1'