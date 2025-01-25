import logging
from .llm import *

class LLMManager:
    def __init__(self, event):
        self.event = event
        self.LLM = OllamaLLM(model="llama3.1:latest")

    def prompt_llm(self):
        prompt = self.LLM.decision_prompt(self.event)
        response = ""
        self.event.logger.info("Prompting LLM...")

        # To prevent potential infinite loops, set a maximum number of attempts

        while response.lower() not in ["yes", "no"]:
            try:
                response = self.LLM.chat(prompt)
                if self.LLM.model == "deepseek-r1:14b":
                    # eliminate <think> and </think> and everything in between
                    response = response.split("<think>")[0].split("</think>")[-1]
                self.event.logger.info(f"LLM response: {response}")
            except Exception as e:
                self.event.logger.error(f"Error while communicating with LLM: {str(e)}")
                break  # Exit the loop if there's an exception

        if response.lower() == "yes":
            self.event.LLM_can_sell = True
            self.event.logger.info("LLM decision: YES - Can sell.")
        elif response.lower() == "no":
            self.event.LLM_can_sell = False
            self.event.logger.info("LLM decision: NO - Cannot sell.")

        return self.event.LLM_can_sell
