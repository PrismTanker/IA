import pathlib
import sys
sys.path.append(str(pathlib.Path(__file__).parent.resolve()))

from hypothesis import given, strategies
from data.extended_humaneval.HumanEval import *

#---
CACHED_ID = None
CACHED_FUN = None
# FUN_REGEX = 'def [a-zA-Z_]+\([a-zA-Z:_\[\],]*\)( -> [a-zA-Z[]]+)?:'


def update_cached_fun(id: int) -> None:
    """
    Update cached solution to the given id

    Args:
        id (int): id of solution to use
    """
    # This is awful, but sometimes sacrifices must be made
    global CACHED_ID
    global CACHED_FUN

    CACHED_ID = id

    # Extract executable sample solution
    dummy_locals = {} 
    exec("from typing import *\ndef " + HUMANEVAL[PROMPTS][CACHED_ID].split('def ')[-1].split('"""')[0].rstrip() + "\n" + HUMANEVAL[SOLS][CACHED_ID], {}, dummy_locals) 
    CACHED_FUN = list(dummy_locals.values())[-1] # TODO relies on insertion order


def test_input_output(id: int, input, output) -> bool:
    """
    Test if a given input/output pair should be expected given a task_id

    Args:
        id (int): ID of task for which input and output have been generated
        input (iterable): expected inputs (input name: input)
        output (any): expected output

    Returns:
        bool: Whether or not this input/output pair makes sense.
    """
   
    global CACHED_ID
    global CACHED_FUN

    if not id == CACHED_ID:
        update_cached_fun(id)

    return CACHED_FUN(*input) == output


def test_property(id: int, property_runner: str) -> bool:
    """
    Test if a given property should be expected given a task_id

    May throw uncaught exceptions if property malformed

    Args:
        id (int): ID of task for which property has been generated
        property_runner (str): string containing dummy harnes to generate the 
                               desired hypothesis test

    Returns:
        bool: Whether or not this input/output pair makes sense.
    """

    if not id == CACHED_ID:
        update_cached_fun(id)

    # Generate property
    property_locals = {}
    prop = None
    exec(property_runner, globals(), property_locals)               
    prop = list(property_locals.values())[-1](CACHED_FUN)[0] # Should be appended to end
    
    # Check if the property is to be expected given task
    try:
        prop()
    except AssertionError as e:
        return False
    return True
