# Iterative Assistant (IA)

This is the code for the IA developed for my honors thesis "Generative Program Correctness:
An Iterative Assistant (IA) to improve the quality of AI generated code for novice users" completed
at the University of Queensland in 2024.

## Contents
- `Interface/`: Code for allowing the IA to make oracle requests during iteration. Contains both code to use a human user as an oracle, and a testing harness to recieve automatic feedback when the IA is run on problems presented in the extended HumanEval dataset (see the assotiated [repository](https://github.com/PrismTanker/ExtendedHumanEval))
- `Model/`: Code for CodeLLama2 LLM inference.
- `Results/`: Folder that will contain IA output
- `IA.py`: Python code defining the IA architecture, and providing interface to run the IA manually
- `test_runner.py`: Code for automatically running the IA on a subset of the HumanEval dataset, with configurable experimental parameters

## Running the IA
In order to run the IA, first specify the GPTQ quantised CodeLlama2 LLM of choice 
by specifying the `MODEL` constant on line 13 of `Model\model_interface.py`, then
run:
```bash
python IA.py
```
From the top level directory.

For local use, it is likely that only the 7B parameter LLM will be feasible.
The 7B parameter LLM has been tested to work with 32GB of RAM and an RTX2070 GPU with 8GB VRAM.

For further detail on the GPTQ quantised models used with the IA, as well as 
instructions for installing dependencies, please see [the respective HuggingFace repositories](https://huggingface.co/TheBloke/CodeLlama-7B-Python-GPTQ). NOTE: git-lfs should be installed before attempting to
clone these submodules.

## Running Automated experiements
In order to run experiments automatically,
first define an experiment in `test_runner.py` by appending to the `EXPERIMENTS` dictionary.
experiments are defined as dictionaries of the form:
```python
<TEST_NAME>: {
        CONTROL: {
            <CONTROL_VAR1>: <CONTROL_VAL1>,
            <CONTROL_VAR2>: <CONTROL_VAL2>,
            <CONTROL_VAR3>: <CONTROL_VAL3>
        },
        INDEPENDENT: (<INDEPENDENT_VAR>, [<INDEPENDENT_VALS, ... >]),
        PROMPT_TYPES: [<PROMPT_TYPES_TO_USE, ... >],
        PROMPT_RANGE: (<CODING_PROBLEMS_TO_USE, ... >)
    }
```

Then, run:
```bash
python test_runner.py -e <TEST_NAME>
```
From the top level directory.

Output will be recorded in `Results/Experiments/<TEST_NAME>`