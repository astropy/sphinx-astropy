"""This module demonstrates using the ``example`` directive in docstrings.
"""

__all__ = ('example_func',)


def example_func():
    """A function with an example in its docstring.

    Examples
    --------

    .. example:: Using example_func
       :tags: tag-a

       An example marked up with the ``example`` directive.

       >>> example_func()
       True
    """
    return True
