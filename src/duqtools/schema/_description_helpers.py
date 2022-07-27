from textwrap import dedent


def formatter(s):
    """Dedent and remove newlines."""
    s = dedent(s)
    return s.replace('\n', ' ').strip()
