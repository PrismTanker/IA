import argparse
import pathlib
import os

RESULTS_PATH = os.path.join(pathlib.Path(__file__).parent.resolve(),"Results","Experiments")
INDEX_FILE = "details.txt"
RESULT_FILE = "results.txt"
RESULT_JSON = "results.json"

import random
from Interface.AutoHarness.data.extended_humaneval.HumanEval import *
from IA import run_experiment, OUTPUT, \
    NUM_SAMPLES, INTERESTING_BOUNDS, THESIS, JSON

CONTROL = "Control_Variables"
INDEPENDENT = "Independent_Variable"
PROMPT_TYPES = "Used_Prompts"
PROMPT_RANGE = "Used_Prompt_Range"

EXPERIMENTS = {
    "test": {
        CONTROL: {
            INTERESTING_BOUNDS: (0.3,0.7),
            THESIS: True,
            JSON: True
        },
        INDEPENDENT: (NUM_SAMPLES, [3]),
        PROMPT_TYPES: [PROMPTS,AMB_ERROR_PROMPTS],
        PROMPT_RANGE: (30,35,1)
    },
    "test_prompt_types": {
        CONTROL: {
            INTERESTING_BOUNDS: (0.3,0.7),
            THESIS: True,
            JSON: True
        },
        INDEPENDENT: (NUM_SAMPLES, [3]),
        PROMPT_TYPES: [PROMPTS,CONTEXTLESS,ENGLISH_ONLY,AMB_PROMPTS,ERROR_PROMPTS,AMB_ERROR_PROMPTS],
        PROMPT_RANGE: (23,24,1)
    },
    "control_exploration": {
        CONTROL: {
            INTERESTING_BOUNDS: (0.3,0.7),
            THESIS: False,
            JSON: True
        },
        INDEPENDENT: (NUM_SAMPLES, [5,10,50,100]),
        PROMPT_TYPES: [PROMPTS,CONTEXTLESS,ENGLISH_ONLY,AMB_PROMPTS,ERROR_PROMPTS,AMB_ERROR_PROMPTS],
        PROMPT_RANGE: (0,len(HUMANEVAL[IDS]),1)#(Start, Stop, Step)
    },

    "sample_impact": {
        CONTROL: {
            INTERESTING_BOUNDS: (0.3,0.7),
            THESIS: True,
            JSON: True
        },
        INDEPENDENT: (NUM_SAMPLES, [2**i for i in range(6)]),
        PROMPT_TYPES: [PROMPTS,ENGLISH_ONLY],
        PROMPT_RANGE: (15,36,1)#(Start, Stop, Step)
    },

    "timeout_test": {
        CONTROL: {
            INTERESTING_BOUNDS: (0.3,0.7),
            THESIS: True,
            JSON: True
        },
        INDEPENDENT: (NUM_SAMPLES, [3]),
        PROMPT_TYPES: [ENGLISH_ONLY],
        PROMPT_RANGE: (30,35,1)#(Start, Stop, Step)
    },

    "control_versus_IA_1": {
        CONTROL: {
            INTERESTING_BOUNDS: (0.3,0.7),
            NUM_SAMPLES: 10,
            JSON: True
        },
        INDEPENDENT: (THESIS, [False, True]),
        PROMPT_TYPES: [PROMPTS],
        PROMPT_RANGE: (1,102,2)#(Start, Stop, Step)
    },

    "control_versus_IA_2": {
        CONTROL: {
            INTERESTING_BOUNDS: (0.3,0.7),
            NUM_SAMPLES: 10,
            JSON: True
        },
        INDEPENDENT: (THESIS, [False, True]),
        PROMPT_TYPES: [CONTEXTLESS],
        PROMPT_RANGE: (1,102,2)#(Start, Stop, Step)
    },
    "control_versus_IA_3": {
        CONTROL: {
            INTERESTING_BOUNDS: (0.3,0.7),
            NUM_SAMPLES: 10,
            JSON: True
        },
        INDEPENDENT: (THESIS, [False, True]),
        PROMPT_TYPES: [ENGLISH_ONLY],
        PROMPT_RANGE: (1,102,2)#(Start, Stop, Step)
    },
    "control_versus_IA_4": {
        CONTROL: {
            INTERESTING_BOUNDS: (0.3,0.7),
            NUM_SAMPLES: 10,
            JSON: True
        },
        INDEPENDENT: (THESIS, [False, True]),
        PROMPT_TYPES: [AMB_PROMPTS],
        PROMPT_RANGE: (1,102,2)#(Start, Stop, Step)
    },
    "control_versus_IA_5": {
        CONTROL: {
            INTERESTING_BOUNDS: (0.3,0.7),
            NUM_SAMPLES: 10,
            JSON: True
        },
        INDEPENDENT: (THESIS, [False, True]),
        PROMPT_TYPES: [ERROR_PROMPTS],
        PROMPT_RANGE: (1,102,2)#(Start, Stop, Step)
    },
    "control_versus_IA_6": {
        CONTROL: {
            INTERESTING_BOUNDS: (0.3,0.7),
            NUM_SAMPLES: 10,
            JSON: True
        },
        INDEPENDENT: (THESIS, [False, True]),
        PROMPT_TYPES: [AMB_ERROR_PROMPTS],
        PROMPT_RANGE: (1,102,2)#(Start, Stop, Step)
    },
    "property_test": {
        CONTROL: {
            INTERESTING_BOUNDS: (0.3,0.7),
            THESIS: True,
            JSON: False
        },
        INDEPENDENT: (NUM_SAMPLES, [2,3]),
        PROMPT_TYPES: [ENGLISH_ONLY],
        PROMPT_RANGE: (33,36,1)#(Start, Stop, Step)
    },

    "property_exploration_1": {
        CONTROL: {
            INTERESTING_BOUNDS: (0.3,0.7),
            NUM_SAMPLES: 10,
            JSON: False
        },
        INDEPENDENT: (THESIS, [True]),
        PROMPT_TYPES: [PROMPTS],
        PROMPT_RANGE: (1,102,2)#(Start, Stop, Step)
    },

    "property_exploration_2": {
        CONTROL: {
            INTERESTING_BOUNDS: (0.3,0.7),
            NUM_SAMPLES: 10,
            JSON: False
        },
        INDEPENDENT: (THESIS, [True]),
        PROMPT_TYPES: [CONTEXTLESS],
        PROMPT_RANGE: (1,102,2)#(Start, Stop, Step)
    },
    "property_exploration_3": {
        CONTROL: {
            INTERESTING_BOUNDS: (0.3,0.7),
            NUM_SAMPLES: 10,
            JSON: False
        },
        INDEPENDENT: (THESIS, [True]),
        PROMPT_TYPES: [ENGLISH_ONLY],
        PROMPT_RANGE: (1,102,2)#(Start, Stop, Step)
    },
    "property_exploration_4": {
        CONTROL: {
            INTERESTING_BOUNDS: (0.3,0.7),
            NUM_SAMPLES: 10,
            JSON: False
        },
        INDEPENDENT: (THESIS, [True]),
        PROMPT_TYPES: [AMB_PROMPTS],
        PROMPT_RANGE: (1,102,2)#(Start, Stop, Step)
    },
    "property_exploration_5": {
        CONTROL: {
            INTERESTING_BOUNDS: (0.3,0.7),
            NUM_SAMPLES: 10,
            JSON: False
        },
        INDEPENDENT: (THESIS, [True]),
        PROMPT_TYPES: [ERROR_PROMPTS],
        PROMPT_RANGE: (1,102,2)#(Start, Stop, Step)
    },
    "property_exploration_6": {
        CONTROL: {
            INTERESTING_BOUNDS: (0.3,0.7),
            NUM_SAMPLES: 10,
            JSON: False
        },
        INDEPENDENT: (THESIS, [True]),
        PROMPT_TYPES: [AMB_ERROR_PROMPTS],
        PROMPT_RANGE: (1,102,2)#(Start, Stop, Step)
    }

}


def test_solution(id: int, solution: str) -> bool:
    """
    Test if code yielded by the IA passes the HumanEval problem

    Args:
        id (int): Id of HumanEval problem
        solution (str): Code returned by IA

    Returns:
        bool: If the IA generated code passes problem
    """
    if not solution:
        return False

    try:
        #Extract Solution
        dummy_locals = {}
        exec(solution, {}, dummy_locals)
        func = None
        for val in dummy_locals.values():
            if callable(val):
                func = val
                break
        if not func:
            raise ValueError()
        
        # Load in test (will have signature check(candidate))
        silly_locals = {}
        checker = None
        exec(HUMANEVAL[TESTS][id], {}, silly_locals)
        for val in silly_locals.values():
            if callable(val):
                checker = val
                break

        # Test solution: (How awful)
        checker(func)

    except (AssertionError, ValueError, Exception) as e:
        return False
    return True

if __name__ == '__main__':
    # Get experiment to run
    parser = argparse.ArgumentParser(description='Run experiment')
    parser.add_argument("--experiment", "-e", type=str,
                    help='experiment name')
    exp = parser.parse_args().experiment

    # Generate location to store experiment
    experiment_path = os.path.join(RESULTS_PATH, exp)
    os.makedirs(experiment_path)
    with open(os.path.join(experiment_path, INDEX_FILE), "w+") as f:
        f.write(f"Testing: {EXPERIMENTS[exp][INDEPENDENT][0]} = {EXPERIMENTS[exp][INDEPENDENT][1]}\n")
        f.write("Controlling:\n")
        for param in EXPERIMENTS[exp][CONTROL]:
            f.write(f"{param} = {EXPERIMENTS[exp][CONTROL][param]}\n")
    
    # Summary statistics (pass@1)
    with open(os.path.join(experiment_path, RESULT_FILE), "w+") as f:
        f.write("Pass@1:\n")

    # Run experiment
    params = EXPERIMENTS[exp][CONTROL]
    results = {}
    for independent_val in EXPERIMENTS[exp][INDEPENDENT][1]:
        results[independent_val] = {}
        ind_path = os.path.join(experiment_path, str(independent_val))
        os.makedirs(ind_path)
        params.update({EXPERIMENTS[exp][INDEPENDENT][0]: independent_val})
        
        with open(os.path.join(experiment_path, RESULT_FILE), "a+") as f:
            f.write(f"--- {EXPERIMENTS[exp][INDEPENDENT][0]} = {independent_val}:\n")
        # (Human readable) intermediate result file
        with open(os.path.join(ind_path, RESULT_FILE), "a+") as f:
            f.write("Results:\n")

        for prompt_type in EXPERIMENTS[exp][PROMPT_TYPES]:
            results[independent_val][prompt_type] = {True: [], False: []}
            prompt_path = os.path.join(ind_path, prompt_type)
            os.makedirs(prompt_path)

            for i in range(*EXPERIMENTS[exp][PROMPT_RANGE]):
                params.update({OUTPUT: os.path.join(prompt_path, str(i)+".txt")})
                solution = run_experiment(i, HUMANEVAL[prompt_type][i], **params)
                evaluation = test_solution(i, solution)
                results[independent_val][prompt_type][evaluation].append(i)

                # Dump result Json after each test for recovery in event of crash (or the uni cutting me off)
                with open(os.path.join(experiment_path, RESULT_JSON),"w+") as f:
                    f.write(json.dumps(results))
            
            # Record intermediate results
            with open(os.path.join(ind_path, RESULT_FILE), "a+") as f:
                f.write(f"--- {prompt_type}:\n")
                f.write(f"   - Pass: {results[independent_val][prompt_type][True]}\n")
                f.write(f"   - Fail: {results[independent_val][prompt_type][False]}\n")
            
            # Compute and record pass@1 statistics
            pass_rate = len(results[independent_val][prompt_type][True])/len(range(*EXPERIMENTS[exp][PROMPT_RANGE]))
            with open(os.path.join(experiment_path, RESULT_FILE), "a+") as f:
                f.write(f"- {prompt_type}: {pass_rate}\n")




      

    
    
