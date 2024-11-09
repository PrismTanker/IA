from llama2_chat_templater.prompt_template import PromptTemplate

class PromptTemplate(PromptTemplate):
    """
    Extends prompt template class to allow initialisation
    with an existing chat history, and for prompting without updating state.
    """

    def __init__(self, system_prompt:str =None, existing_history: tuple[list[str], list[str]] = None) -> None:
        """
        Initialises prompt tempater.

        Args:
            system_prompt (str, optional): System prompt. Defaults to None.
            existing_history (tuple[list[str], list[str]], optional): Initial 
                (input, repsonse) conversation history. 
                The number of inputs and responses must be equal. Defaults to 
                None.
        """
        super().__init__(system_prompt)
        if existing_history:
            messages, responses = existing_history
            if len(messages) != len(responses):
                raise ValueError(
                    "Number of user messages does not equal number of system replies."
                )
            else:
                self.user_messages = messages
                self.model_replies = responses

    def add_user_message(self, message: str, return_prompt=True, supress_update = False):
        if supress_update and not return_prompt:
            return
        self.user_messages.append(message)
        if return_prompt:
            prompt = self.build_prompt()
        if supress_update:
            self.user_messages.pop()
        if return_prompt:
            return prompt
        

    def add_model_reply(self, reply: str, return_reply= False, supress_update = False) -> None:
        """
        Adds a model reply to the template. Overridden as tokenizer mucks up
        default history strip behavior.

        Args:
            reply (str): Model reply
            return_reply (bool, optional): Whether the reply should be returned. 
                                           Defaults to False.
        """
        HISTORY_TERMINATOR = "[/INST]"        
        reply = reply[reply.rindex(HISTORY_TERMINATOR) + len(HISTORY_TERMINATOR):] #TODO probably worth allowing already trimmed inputs
        if not supress_update:
            self.model_replies.append(reply)
        if len(self.user_messages) != len(self.model_replies):
            raise ValueError(
                "Number of user messages does not equal number of system replies."
            )
        if return_reply:
            return reply
