#TODO set up __init__.py's to make system more robust
import pathlib
import sys
import os
sys.path.append(str(pathlib.Path(__file__).parent.resolve()))

# from awq import AutoAWQForCausalLM
from transformers import AutoModelForCausalLM, AutoTokenizer
from chat_template import PromptTemplate
import torch.multiprocessing as mp
mp.set_start_method('spawn', force=True)

MODEL = "CodeLlama-7B-Instruct-GPTQ"
MODEL_PATH = os.path.join(str(pathlib.Path(__file__).parent.resolve()), MODEL)
MAX_OUTPUT_TOKENS = 2048


class IAModel():
    """
    class for interfacing with model for iterative assistant.
    Maintains one singular model instance loaded, with each instance
    of this interface providing separate chat perspectives/histories.
    """
    #load STATIC model instance
    # model = AutoAWQForCausalLM.from_quantized(MODEL_PATH, fuse_layers=True,
    #                                       trust_remote_code=True, safetensors=True)
    model = AutoModelForCausalLM.from_pretrained(MODEL_PATH,
                                             device_map="cuda",
                                             trust_remote_code=True,
                                             revision="gptq-4bit-32g-actorder_True")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, trust_remote_code=True)

    def __init__(
            self, 
            system_prompt:str =None, 
            existing_history: tuple[list[str], list[str]] = None
    ) -> None:
        """
        Initialise new chat view for model. #TODO redo these descriptions

        Args:
            system_prompt (str, optional): System prompt. Defaults to None.
            existing_history (tuple[list[str], list[str]], optional): Initial 
                (input, repsonse) conversation history. 
                The number of inputs and responses must be equal. 
                Defaults to None.
        """
        self._templater = PromptTemplate(system_prompt, existing_history)
    
    def get_user_messages(self) -> str:
        """
        Return list of user's messages in order

        Returns:
            str: user's messages in send order
        """
        return self._templater.get_user_messages()
    
    def get_model_replies(self) -> str:
        """
        Return list of model's replies in order

        Returns:
            str: list of model's replies in send order
        """
        return self._templater.get_model_replies()
    
    def prompt(self, prompt: str, supress_update: bool = False) -> str:
        """
        Prompts model based on new prompt and chat history, and returns result.
        Updates message history accordingly unless specified otherwise.

        Parameters:
            prompt (str): new prompt

        Returns:
            str: model response
        """
        print("\n*** Generating response:")

        tokens = self.tokenizer(
            self._templater.add_user_message(
                prompt, 
                return_prompt= True, 
                supress_update=supress_update
            ),
            return_tensors='pt'
        ).input_ids.cuda()

        # Generate output
        generation_output = self.tokenizer.decode(self.model.generate(
            tokens,
            do_sample=True,
            temperature=0.7,
            top_p=0.95,
            top_k=40,
            max_new_tokens=MAX_OUTPUT_TOKENS
        )[0])
        
        return self._templater.add_model_reply(
            generation_output,
            return_reply= True,
            supress_update = supress_update
        )
       
#test code, have a conversation:
if __name__ == "__main__":
    
    system_prompt = "You are a python expert who will provide python code to solve the following coding problems that obeys the constraints and passes the given test cases. If you use any modules, include the import statement. Please produce exactly one code sample, and wrap your code answer using ```. After the code sample, please give a set of Pytest unit tests. The pytests should be just individual assertions, and should also be wrapped in '''."
    model = IAModel(system_prompt)
    prompt = input("Please enter first prompt. Enter nothing at any time to exit: ")
    while prompt:
        print(model.prompt(prompt))
        prompt = input("Please enter new prompt, or nothing to exit: ")
    
