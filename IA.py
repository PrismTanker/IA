from Interface.test_feedback import auto_json_feedback, human_json_feedback, auto_property_feedback, human_property_feedback
from Interface.feedback_codes import *
from typing import Optional, Union
from copy import deepcopy
import re, json
# from time_out import add_timeout
from pebble import concurrent
from concurrent.futures import TimeoutError
from hypothesis import given, strategies


# Mode Flags
LOG = True

# Tuneable paramaters
MAX_ITERATION = 10
MAX_TRY = 20
TIMEOUT = 3600 # Seconds

# Constants
WRAPPER = '```|\[PYTHON\]|\[/PYTHON\]'
DUP_TAG = "_new"

# Kwarg names
OUTPUT = "Output"
NUM_SAMPLES = "Num_samples"
INTERESTING_BOUNDS = "Interesting_Bounds"
THESIS = "Not_Control"
JSON = "Use_Unit_Tests"


# TODO Docstrings
def extract_code(response: str) -> Optional[str]:
    # Assume blocks were wrapped correctly (will try except an eval later)
    blocks = re.split(WRAPPER, response) #  ```Code``` sometimes it wraps with [PYTHON] [\PYTHON]
    
    # Extract code samples
    try:
        gen_code = blocks[1]       
    except IndexError as e:
        # Malformed response
        return None
    
    # Test for syntax errors:
    try:
        exec(gen_code, {}, {})
    except: # Lord forgive me
        # Invalid code sample
        return None
    
    return gen_code

def extract_assertion_tests(response: str) -> Optional[list[str]]: #TODO This is exceedingly fickle. May not scale up well
    TEST_REGEX = 'def .*():'
    # Partition response
    try:
        test_starts = [m.start() for m in re.finditer(TEST_REGEX, response)] 
        i = test_starts[0]   
    except IndexError as e:
        # Malformed response
        return None
    
    # Compile tests
    test_cases = []
    for j in test_starts[1:]:
        test_cases.append(response[i:j].rstrip())
        i = j

    return test_cases

def extract_property_tests(response: str)-> Optional[list[str]]:
    # Partition using given tags
    PROP_TAG = "    @given"
    FLUFF_IDENTIFIER = "return" # Final property may have dangling stuff to get rid of
    try:
        properties = [PROP_TAG + prop.rstrip() for prop in response.split(PROP_TAG)[1:]] #Drop first as it is header
        properties[-1] = re.split(FLUFF_IDENTIFIER, properties[-1])[0].rstrip() # Trim Fluff if any
        return properties
    except IndexError as e:
        # Malformed response
        return None
    
def get_property_test_name(prop_test: str) -> str:
    return prop_test.split("def")[-1].split("(")[0].strip()

def get_property_test_body(prop_test: str) -> str:
    return prop_test[prop_test.index("\n")+1:]  

def recompile_property_test_suite(properties: list[str]) -> str:
    PROPERTY_TEST_SIGNATURE = "from hypothesis import given, strategies\ndef property_test(candidate_function):"
    SEPARATOR = "\n\n"
    COMMA = ","
    return f"{PROPERTY_TEST_SIGNATURE}\n{SEPARATOR.join(properties)}{SEPARATOR}    return [{COMMA.join([get_property_test_name(prop) for prop in properties])}]"

def extract_json_tests(response: str) -> Optional[dict]:
    try:
        tests = re.split(WRAPPER, response)[1] # ```JSON``` 
        test_cases = json.loads(tests)
    except (json.JSONDecodeError, IndexError) as e:
        # Malformed response, possibly a python dictionary
        try:
            test_cases = eval(tests)
        except TimeoutError as e:
            raise e
        except Exception as e:
            # Properly malformed response
            return None
    return test_cases

#TODO Prompt Constant file
def gen_code_samples(prompt: str, tests: Optional[list[str] | dict], num_samples: int, **kwargs) -> list[str]:
    from Model.model_interface import IAModel
    # Determine what type of test we are using, and transform to prompt
    if tests:
        json_mode = isinstance(tests, dict)
        if json_mode:
            tests = json.dumps(tests)
        else:
            tests = recompile_property_test_suite(tests)
    
    CODE_SYS = "You are a python expert who will provide python code to \
            solve the following coding problem that obeys the constraints and \
            passes the given test cases. If you use any modules, include the \
            import statement. Please produce exactly one code sample, and wrap \
            your code answer using ```. Do not include any test cases."
    code_generator = IAModel(CODE_SYS)

    # Enforce any test constraints
    if tests:
        if json_mode:
            TEST_PROMPT = "\n\nPlease produce exactly one python function. The function must satisfy the input output pairs presented in the following JSON snippet: " + str(tests) + \
                        "Where 'in' gives a set of inputs, and 'out' is the output expected output given the assotiated inputs."
        else:
            TEST_PROMPT = "\n\nThe code sample must satisfy the property tests provided by the following testing function: \n" + str(tests)
        prompt += TEST_PROMPT + "\n But, do not include any testcases in the requested code sample."
    
    #Generate samples
    code_samples = []
    for i in range(num_samples):
        response = code_generator.prompt(prompt, supress_update=True) # Repeatedly prompt same thing
        if LOG:
            with open(kwargs[OUTPUT], 'a') as f:
                f.write(response)

        sample = extract_code(response)
        if sample:
            code_samples.append(sample)
        
    return code_samples

def refine_code(prompt: str, sample: str, tests: Optional[list[str] | dict], num_samples: int, failed_tests: Optional[list[str] | dict] = None, **kwargs) -> list[str]:
    from Model.model_interface import IAModel
    # Determine what type of test we are using
    if tests:
        json_mode = isinstance(tests, dict)
        if json_mode:
            tests = json.dumps(tests)
        else:
            tests = recompile_property_test_suite(tests)
        
    CODE_REF_SYS =  "You are a python expert who will refine the given python code to \
            ensure it solves the following coding problem, obeys the constraints and \
            passes the given test cases. If you use any modules, include the \
            import statement. Please produce exactly one code sample, and wrap \
            your code answer using ```. Do not include any test cases in your response."
    code_refiner = IAModel(CODE_REF_SYS)

    # Request refinement of a code sample.
    prompt += "\n I currently have the following code sample to solve this problem, but it does not completely solve the problem: \n ```" + sample + "```"

    if failed_tests:
        if json_mode:
            prompt += "in particular, my code does not provide the expected outputs given the inputs presented in the following JSON snippet: " + str(failed_tests)
        else:
            prompt += "in particular, my code is failing to pass the property tests: " + str(failed_tests) 
        

    # Enforce any test constraints
    if tests:
        if json_mode:
            TEST_PROMPT = "\n\nPlease produce exactly one python function. The function must satisfy the input output pairs presented in the following JSON snippet: " + str(tests) + \
                        "Where 'in' gives a set of inputs, and 'out' is the output expected output given the assotiated inputs."
        else:
            TEST_PROMPT = "\n\nThe code sample must satisfy the property tests provided by the following testing function: \n" + str(tests)
        prompt += TEST_PROMPT + "\n But, do not include any testcases in the requested code sample."

    #Generate samples
    code_samples = []
    for i in range(num_samples):
        response = code_refiner.prompt(prompt, supress_update=True) # Repeatedly prompt same thing
        if LOG:
            with open(kwargs[OUTPUT], 'a') as f:
                f.write(response)
        sample = extract_code(response)
        if sample:
            code_samples.append(sample)
        
    return code_samples


def gen_test_suite(prompt: str, code_sample: Optional[str] = None, json_mode: bool = False, **kwargs) -> Optional[list[str] | dict]:
    from Model.model_interface import IAModel
    TEST_SYS = "You are a Python expert, who will provide a comprehensive test \
                    suite for a hypothetical solution to the given Python coding problem. \
                    Do not produce a solution to the problem, instead produce exactly one \
                    test suite."
    

    prompt = "Please generate a test suite to test a future solution for the following problem: " + prompt

    if json_mode:
        TEST_SYS += "Do not generate any code. Instead produce a JSON sample that \
            represents the desired tests. The generated JSON sample should contain paired inputs \
            and expected outputs. The JSON should be exactly of the form:" + \
            """
            ```
            {
                TESTNAME: {
                    in: {
                        PARAMNAME: PARAMVALUE
                    },
                    out: OUTPUT
                }
            }
            ```
            """ + "Where TESTNAME is the name of the test, PARAMNAME is the name of a parameter, \
                PARAMVALUE is the value of the parameter to be tested, and OUTPUT is the expected output given \
                the specified inputs. Parameters should appear in the order they would be input to the function. \
                Remember that JSON uses all lower case for true and false"
    else:
        TEST_SYS += "The Hypothesis library provides the ability to write property tests for functions. \
            You will produce exactly one python function that runs relevant property tests on an input function \
            (A hypothetical future solution to a given problem). The generated property test function should be of the form:\n" + \
            """
            ```
            from hypothesis import given, strategies
            def property_test(candidate_function) -> None:
                
                @given(...)
                def property_1(...):
                    ...
                    candidate_function ...
                
                @given(...)
                def property_2(...):
                    ...
                    assert ...

                return [property_1,property_2,... ] 
            ```
            """ + "The function should return a list containing the property tests. \
            Do not import unittest or pytest. Do not include any other code beyond the property_test function."
        
    
    if code_sample:
        prompt += "\nA possible solution to this problem is the following: " + \
            f"""
            ```
            {code_sample}
            ```
            """ 

    # Generate tests
    tests = IAModel(TEST_SYS).prompt(prompt)
    if LOG:
        with open(kwargs[OUTPUT], 'a') as f:
            f.write(tests)

    # Extract tests 
    if json_mode:
        return extract_json_tests(tests)
    else:
        return extract_property_tests(tests) 
        
def refine_test_suite(prompt: str, tests: dict, code_sample: Optional[str] = None, filter = False, known_correct = None, known_incorrect = None, **kwargs) -> Optional[list[str] | dict]:    
    from Model.model_interface import IAModel
    if known_correct or known_incorrect:
        raise NotImplementedError("Mode not added yet") #TODO
    
    json_mode = isinstance(tests, dict)
    if not json_mode:
        tests = recompile_property_test_suite(tests)

    TEST_REF_SYS = "You are a Python expert, who will improve upon a comprehensive test \
                    suite for a hypothetical solution to the given Python coding problem. \
                    Do not produce a solution to the problem, instead produce exactly one \
                    test suite."
    
    prompt = "A test suite was generated for a future solution for the following problem: " + prompt
    if json_mode:
        INSTRUCTIONS = "\n The generated test suite is a JSON sample containing paired inputs and expected outputs. The JSON is exactly of the form:" + \
            """
            ```
            {
                TESTNAME: {
                    in: {
                        PARAMNAME: PARAMVALUE
                    },
                    out: OUTPUT
                }
            }
            ```
            """ + "Where TESTNAME is the name of the test, PARAMNAME is the name of a parameter, \
                PARAMVALUE is the value of the parameter to be tested, and OUTPUT is the expected output given \
                the specified inputs. Parameters appear in the order that they would be input to the function. \
                Remember that JSON uses all lower case for true and false. \
                This was the generated test suite: " + str(tests)
        
        INSTRUCTIONS += "\n Please extend the coverage of this test suite by adding further input output pairs. \
                        Your additions must follow the provided format. Do not produce any code."
    else:
        INSTRUCTIONS = "\n The generated test suite is a python function that runs relevant property tests on a candidate function. The function is of the form" + \
        """
        ```
            from hypothesis import given, strategies
            def property_test(candidate_function) -> None:
                
                @given(...)
                def property_1(...):
                    ...
                    candidate_function ...
                
                @given(...)
                def property_2(...):
                    ...
                    assert ...
                
                return [property_1,property_2,... ]
            ```
        """  + "This was the generated test suite: " + str(tests)

        INSTRUCTIONS += "\n Please extend the coverage of this test suite by adding further property tests. \
                        Your additions must follow the provided format."
    
    if filter:
        INSTRUCTIONS += "Please exclude any tests from the given test suite if they are not suitable tests for the given problem"
       
    
    if code_sample:
        prompt += "A possible solution to this problem is the following: " + \
            f"""
            ```
            {code_sample}
            ```
            """

    prompt += INSTRUCTIONS 

    # Generate tests
    tests = IAModel(TEST_REF_SYS).prompt(prompt)
    if LOG:
        with open(kwargs[OUTPUT], 'a') as f:
            f.write(tests)

    if json_mode:
        return extract_json_tests(tests)
    else:
        return extract_property_tests(tests) 


def eval_samples(code_samples: list[str], test_suite: list[str]|dict) -> tuple[dict[str,float], tuple[str, float]]:
    # Determine what form of test suite we are working with
    json_mode = isinstance(test_suite, dict)
    
    best_sample = ""
    greatest_pass = 0
    test_results = {} #TODO find something better than the entire test as a key.
    for sample in code_samples:
        # Load sample code to test
        sample_locals = {}
        exec(sample, {}, sample_locals) # This should have been tested upon code gen, and so we deserve any errors
        pass_count = 0

        # Run tests
        for test in test_suite: 
            curr_locals = sample_locals.copy()
            passed = True

            # Locals from code sample should possess precicely one function
            func = None
            for val in curr_locals.values(): #TODO make significantly more readable
                if callable(val):
                    func = val
                    break

            if func:
                # JSON formatted tests
                if json_mode:
                    # Extract test
                    test_data = deepcopy(test_suite)[test] # Arbitrary code may mutate TODO be slightly more efficient
                    try:
                        exp_in = test_data["in"] #TODO constants
                        exp_out = test_data["out"]
                    except KeyError as e:
                        # Malformed test, skip
                        passed = False
                    
                    #Run test
                    if passed:
                        try:
                            passed = func(*exp_in.values()) == exp_out
                        except TimeoutError as e:
                            raise e
                        except Exception as e:
                            passed = False

                # Hypothesis property tests
                else:
                    # load test
                    property_locals = {}
                    try:
                        exec(recompile_property_test_suite([test]), globals(), property_locals)                    

                        # Run test
                        list(property_locals.values())[-1](func)[0]() # May throw assetion error TODO Relies on insertion order

                    except TimeoutError as e:
                        raise e
                    except Exception as e: # TODO split into assertion and otherwise
                        passed = False

            else:
                # Malformed sample, ignore (Should not occur)
                passed = False  

            # Track stats
            if passed:               
                pass_count += 1
                test_results[test] = test_results.get(test,0) + 1
        
        if (pass_count > greatest_pass or (pass_count == greatest_pass and len(sample) < len(best_sample))): # prioritise simpler code samples in event of tie.
            greatest_pass = pass_count
            best_sample = sample

    return {test: (score/len(code_samples) if len(code_samples) > 0 else 0) for test,score in test_results.items()}, (best_sample, greatest_pass/len(test_suite)) # TODO account for no tests earlier

def get_json_feedback(tests: dict, id: Optional[int] = None) -> dict[str, int]: # {test: code}
    return auto_json_feedback(id,tests) if id else human_json_feedback(tests)

def get_property_feedback(properties: list[str], id: Optional[int] = None) -> dict[str, int]: # {test: code}
    return auto_property_feedback(id, [recompile_property_test_suite([prop]) for prop in properties]) if id else human_property_feedback(properties)

def update_json_tests(tests: dict, new_tests: dict, overwrite: bool = True) -> None:
    for new_test in new_tests:
        if (new_test in tests):
            if (tests[new_test]['in'] == new_tests[new_test]['in']): # If you have let a keyerror slip past until now you deserve what is coming to you
                # Overwrite with new information. Assume any contradictions are a change of mind
                if overwrite:
                    tests[new_test] = new_tests[new_test] 
            else:
                # New test with same title
                new_name = new_test + DUP_TAG
                while new_name in tests:
                    new_name = new_name + DUP_TAG
                tests[new_name] = new_tests[new_test]
        else:
            # New test
            tests[new_test] = new_tests[new_test]

def update_properties(props: list[str], new_props: list[str], overwrite: bool = True) -> None: #TODO no overwrite
    existing_names = [get_property_test_name(prop) for prop in props]
    existing_bodies = [get_property_test_body(prop) for prop in props]

    for new_prop in new_props:
        if (not get_property_test_body(new_prop) in existing_bodies): # Skip any properties we already have
            
            # Ensure unique names
            prop_name = get_property_test_name(new_prop)
            if (prop_name in existing_names):
                new_name = prop_name + DUP_TAG
                while new_name in existing_names:
                    new_name = new_name + DUP_TAG
                
                new_prop = new_prop.replace(prop_name, new_name, 1)
            
            # Add new tests       
            props.append(new_prop)

def evaluate_tests(
        good_tests: dict|list[str], 
        bad_tests: dict|list[str], 
        new_tests: dict|list[str],
        test_results: dict[str, float], 
        current_candidate: str,
        id: Optional[int] = None,
        **kwargs
    ) -> None: 
    # TODO I really should be using pandas at this point
    json_mode = isinstance(new_tests, dict)

    # identify interesting tests
    auto_good_tests = {} if json_mode else [] # this is going to go well and introduce no bugs
    auto_bad_tests = {} if json_mode else []
    interesting_tests = {} if json_mode else []

    if current_candidate:
        candidate_scores, _ = eval_samples([current_candidate], new_tests)
        for test in new_tests:
            if test in candidate_scores and candidate_scores[test] >= 0.999999:
                if test_results[test] >= kwargs[INTERESTING_BOUNDS][1]:
                    # If we pass previous candidate and most current samples assume we are good
                    if json_mode:
                        auto_good_tests[test] = new_tests[test]
                    else:
                        auto_good_tests.append(test)
                else:
                    # If we pass previous candidate but not most current samples that is interesting
                    if json_mode:
                        interesting_tests[test] = new_tests[test]
                    else:
                        interesting_tests.append(test)
            else:
                # Any test that fails the previous candidate code is interesting
                if json_mode:
                    interesting_tests[test] = new_tests[test]
                else:
                    interesting_tests.append(test)
    
    else:
        # Fallback method in the event we do not have a prior candidate
        # Consider a confidence interval based on ratio of passed samples
        for test in new_tests:
            if (test in test_results) and (test_results[test] >= kwargs[INTERESTING_BOUNDS][0]):
                if test_results[test] <= kwargs[INTERESTING_BOUNDS][1]:
                    if json_mode:
                        interesting_tests[test] = new_tests[test]
                    else:
                        interesting_tests.append(test)
                else:
                    if json_mode:
                        auto_good_tests[test] = new_tests[test]
                    else:
                        auto_good_tests.append(test)
            else:
                if json_mode:
                    auto_bad_tests[test] = new_tests[test]
                else:
                    auto_bad_tests.append(test)

    # Determine validity of interesting tests:
    feedback = get_json_feedback(interesting_tests, id) if json_mode else get_property_feedback(interesting_tests, id)

    if LOG:
        with open(kwargs[OUTPUT], 'a') as f:
                    f.write(f"\nAUTO_GOOD_TESTS: {auto_good_tests}\nAUTO_BAD_TESTS: {auto_bad_tests}\nINTERESTING_TESTS: {interesting_tests}\n")
                    if feedback:
                        f.write(f"\nFEEDBACK: {feedback}\n")
    
    known_good = {test: interesting_tests[test] for test in feedback if feedback[test] == GOOD} if json_mode else [test for test in feedback if feedback[test] == GOOD] 
    known_bad = {test: interesting_tests[test] for test in feedback if not feedback[test] == GOOD} if json_mode else [test for test in feedback if not feedback[test] == GOOD] # TODO Currently we don't discriminate reason
    
    # Update test database
    if json_mode:
        update_json_tests(good_tests, auto_good_tests, overwrite=False) # Treat automatically determined tests as weakest information
        update_json_tests(bad_tests, auto_bad_tests, overwrite=False)
        update_json_tests(good_tests, known_good)
        update_json_tests(bad_tests, known_bad)
    else:
        update_properties(good_tests, auto_good_tests, overwrite=False)
        update_properties(bad_tests, auto_bad_tests, overwrite=False)
        update_properties(good_tests, known_good)
        update_properties(bad_tests, known_bad)


################################################################################

@concurrent.process(timeout = TIMEOUT)
def iterative_gen(prompt: str, id: Optional[int] = None, **kwargs) -> str:
    
    # Track the current best code (and score)
    candidate = (None, 0)

    # Test database
    good_tests = {} if kwargs[JSON] else []
    bad_tests = {} if kwargs[JSON] else []

    # Working iteration
    curr_tests = {} if kwargs[JSON] else []
    samples = []

    # Initial round of test generation (We follow test driven paradigm)
    for _ in range(MAX_TRY):
        curr_tests = gen_test_suite(prompt, candidate[0], json_mode= kwargs[JSON], **kwargs)
        if curr_tests:
            break
    
    # Initial Code Gen
    for _ in range(MAX_TRY): # Account for model cooking the samples
        samples = gen_code_samples(prompt, good_tests, num_samples=kwargs[NUM_SAMPLES], **kwargs)
        if samples: 
            break
            
    if not (curr_tests and samples):
        # result_handle.result = candidate[0] 
        return candidate[0] # The model simply isn't going to get it.

    
    #Iteration (The main event)
    for _ in range(MAX_ITERATION):

        # Update test database
        if kwargs[THESIS]:
            # Examine generated tests
            test_results, _ = eval_samples(samples, curr_tests)
            if LOG:
                with open(kwargs[OUTPUT], 'a') as f:
                    f.write(f"\nNEW TEST EVALUATION RESULTS: {test_results}\n")
            
            evaluate_tests(good_tests, bad_tests, curr_tests, test_results, candidate[0], id, **kwargs)
        
        else:
            good_tests = curr_tests

        # Extract new best candidate using updated test database
        if good_tests:
            test_results, new_candidate = eval_samples(samples, good_tests)
            if LOG:
                with open(kwargs[OUTPUT], 'a') as f:
                    f.write(f"\nGOOD TEST EVALUATION RESULTS: {test_results}\nBEST SAMPLE ON GOOD TESTS: {new_candidate}\n" )
        else:
            new_candidate = (None, 0) # Skip iteration if we have no good tests
        
        # Update best candidate
        if new_candidate[0] and new_candidate[1] >= candidate[1]: # Account for falling over on an iteration
            candidate = new_candidate
            # result_handle.result = candidate[0]
        
        if LOG:
            with open(kwargs[OUTPUT], 'a') as f:
                f.write(f"\nCURRENT BEST CANDIDATE: {candidate}\n**********************\n\n")
  

        if candidate[1] < 0.999 or len(good_tests) < 3: # Don't want to return with only one good test
            # Generate further tests
            for _ in range(MAX_TRY):
                if good_tests: # May not actually have any good tests to refine yet
                    new_tests = refine_test_suite(prompt, good_tests, candidate[0], num_samples=kwargs[NUM_SAMPLES], **kwargs)
                else:
                    new_tests = gen_test_suite(prompt, candidate[0], json_mode = kwargs[JSON], **kwargs)

                if new_tests:
                    curr_tests = new_tests
                    break
            
            # Refine code samples
            for _ in range(MAX_TRY):
                if candidate[0]: # While we have samples, we may not have a candidate
                    new_samples = refine_code(prompt, candidate[0], good_tests, num_samples=kwargs[NUM_SAMPLES], **kwargs)
                else:
                    new_samples = gen_code_samples(prompt, good_tests, num_samples=kwargs[NUM_SAMPLES], **kwargs)
                
                if new_samples:
                    samples = new_samples
                    break

        else:
            break

    return candidate[0]
    



if __name__ == "__main__":
    # TODO CLI Interface
    # PROMPT =  "Please write me a function that derives a mathematical expression given in string format"
    # PROMPT = "Please write me a function that reduces all elements of a list that matches the type hints of a given function, and leaves any incompatible elements untouched"
    # PROMPT = "Please write me a function that returns the difference between the count of the most common and least common characters in a string"
    prompt = input("Enter Prompt: \n")
    params = {
        OUTPUT: "Code/IA/Results/Manual_Tests/test_out.txt",
        NUM_SAMPLES: 5,
        INTERESTING_BOUNDS: (0.3, 0.7),
        THESIS: True
    }
    out = params[OUTPUT]
    with open(out, 'w+') as f:
        f.write(f'Prompt: {prompt}\n')
        if LOG:
            f.write('-------------------\n')

    result = iterative_gen(prompt, **params)
    # result = result_handle.result

    with open(out, 'a') as f:
        if LOG:
            f.write('\n-------------------\n')
        f.write(f"Final reponse: {result}")

def run_experiment(id: int, prompt: str, **kwargs):
    out = kwargs.get(OUTPUT, "Results/out.txt")

    with open(out, 'w+') as f:
        f.write(f'Prompt: {prompt}\n')
        if LOG:
            f.write('-------------------\n')

    # Do the thing
    black_magic = iterative_gen(prompt, id, **kwargs)
    try:
        result = black_magic.result()
    except TimeoutError as e:
        result = None
        with open(out, 'a') as f:
            f.write(f"\n{TIMEOUT} SECONDS EXCEEDED: TIMED OUT\n")
    except Exception as e: # I give up
        result = None
        with open(out, 'a') as f:
            f.write(f"\nERROR OCCURED: {e}\n")
    # result = result_handle.result

    with open(out, 'a') as f:
        if LOG:
            f.write('\n-------------------\n')
        f.write(f"Final reponse: {result}")

    return result
