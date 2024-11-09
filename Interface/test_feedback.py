import pathlib
import sys
sys.path.append(str(pathlib.Path(__file__).parent.resolve()))

from feedback_codes import *
from AutoHarness.auto_feedback import test_input_output, test_property
from concurrent.futures import TimeoutError

def human_json_feedback(tests: dict) -> dict[str, int]:
    """
    Returns feedback codes corresponding to human feedback on each given test

    Args:
        tests (dict): (testname: test) JSON input/output pairs for human to 
                      evaluate

    Returns:
        dict[str, int]: (testname: code) Feedback code provided for each test
    """
    feedback = {}
    # TODO redo with popups
    for test_name in tests:
        test = tests[test_name]

        # Extract paramters/returns
        try:
            gen_in = str(test["in"])[1:-1] # Strip brackets from list
            gen_out = str(test["out"])
        except KeyError as e:
            feedback[test_name] = MALFORMED
            continue

        # Format empty parameters/returns
        gen_in = gen_in if gen_in else "None"
        gen_out = gen_out if gen_out else "None"

        # Get user feedback
        print(f"Should the following input/output pair be expected for your problem? \
               \n Input: {gen_in}, \n Expected Output: {gen_out}")
        response = ""
        while response not in ["y","Y","n","N"]:
            response = input("Please enter y/n: ")
        
        if response.lower() == "y":
            feedback[test_name] = GOOD
        else:
            print("Was there the correct input count/type?")
            response = ""
            while response not in ["y","Y","n","N"]:
                response = input("Please enter y/n: ")
                if response.lower() == "y":
                    feedback[test_name] = BAD_FORMAT
                else:
                    feedback[test_name] = BAD_VALS

    return feedback
def auto_json_feedback(id: int, tests: dict) -> dict[str, int]:
    """
    Returns feedback codes corresponding to automatic feedback on each given test

    Args:
        id (int): ID of HumanEval problem on which to base feedback
        tests (dict): (testname: test) JSON input/output pairs to evaluate

    Returns:
        dict[str, int]: (testname: code) Feedback code provided for each test
    """
    feedback = {}
    for test_name in tests:
        try:
            if test_input_output(id, tests[test_name]["in"].values(), tests[test_name]["out"]):
                feedback[test_name] = GOOD
            else:
                feedback[test_name] = BAD_VALS
        except TimeoutError as e:
            raise e
        except Exception as e:
            feedback[test_name] = BAD_FORMAT
    return feedback


def human_property_feedback(tests: list[str]) -> dict[str, int]:
    """
    Returns feedback codes corresponding to human feedback on each given 
    property test

    Args:
        tests (list[str]): property test hypothesis functions for user to evaluate

    Returns:
        dict[str, int]: (test: code) Feedback code provided for each test
    """
    feedback = {}
    # TODO redo with popups
    for test in tests:


        # Get user feedback
        print(f"Should the following property be expected for your problem? \
               \n {test}")
        response = ""
        while response not in ["y","Y","n","N"]:
            response = input("Please enter y/n: ")
        
        if response.lower() == "y":
            feedback[test] = GOOD
        else:
            print("Was there the correct input count/type?")
            response = ""
            while response not in ["y","Y","n","N"]:
                response = input("Please enter y/n: ")
                if response.lower() == "y":
                    feedback[test] = BAD_FORMAT
                else:
                    feedback[test] = BAD_VALS

    return feedback

def auto_property_feedback(id: int, test_harnesses: list[str]) -> dict[str, int]:
    """
    Returns feedback codes corresponding to automatic feedback on each given 
    property

    Args:
        id (int): ID of HumanEval problem on which to base feedback
        test_harnesses (list[str]): strings containing dummy harnesses to generate 
                                    the desired hypothesis test

    Returns:
        dict[str, int]: (test: code) Feedback code provided for each test
    """
    
    feedback = {}
    for test in test_harnesses:
        # print("\n\n\n******************\nLOOK AT ME!!!!!!!!!!!!!!\n******************")
        try:
            if test_property(id, test):
                feedback[test] = GOOD
            else:
                feedback[test] = BAD_VALS
        except TimeoutError as e:
            raise e
        except Exception as e:
            feedback[test] = BAD_FORMAT
    return feedback

