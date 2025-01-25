# llm.py
from typing import Generator
from ollama import chat
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

class BaseLLM:
    """
    A base interface for Large Language Models.
    Subclasses should at least implement:
      - chat(prompt) -> str
      - chat_stream(prompt) -> Generator[str, None, None]
    """

    def decision_prompt(self, event):
        """
        Given an event builds a decision prompt for the LLM to consider.
        """
        prompt = f"""Given the following token code:
        {event.token.code}
        Do you you see any backdoors, rug pulls, or other security issues? Would you say that this token is sellable at a later time?
        ANSWER (YES/NO): (ANSEWR ONLY USING YES OR NO NOTHING ELSE)"""
        return prompt

    def chat(self, prompt: str) -> str:
        """
        Blocking call that returns a single response as a string.
        """
        raise NotImplementedError("Subclasses must implement chat(prompt).")

    def chat_stream(self, prompt: str) -> Generator[str, None, None]:
        """
        Streaming call that yields partial responses (chunks/tokens).
        """
        raise NotImplementedError("Subclasses must implement chat_stream(prompt).")

class OllamaLLM(BaseLLM):
    """
    Uses the official Ollama Python library to interact with a locally running Ollama server.
    By default, it uses the 'llama3.1' model.
    """

    def __init__(
        self,
        model: str = "mymodel",
        stream: bool = False,
        **ollama_kwargs
    ):
        """
        :param model: The model name you want Ollama to use, e.g. 'llama3.1', 'llama2', 'codellama'.
        :param stream: Whether to stream responses by default (you can override in method calls).
        :param ollama_kwargs: Additional kwargs like temperature, top_k, top_p, etc.
        """
        self.model = model
        self.stream_by_default = stream
        self.ollama_kwargs = ollama_kwargs

    def chat(self, prompt: str) -> str:
        """
        Returns the entire response from the LLM as a single string (blocking).
        Internally uses `ollama.chat(...)` without streaming.
        """
        # We'll force 'stream=False' here for a blocking call
        response = chat(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            stream=False,
            **self.ollama_kwargs
        )
        # `chat(...)` returns a ChatResponse object that can be treated like a dict
        # The full text is in response['message']['content']
        # If multiple chunks or segments are in the response, they might be joined.
        # Typically, you'll find the entire final content in `response['message']['content']`.
        return response["message"]["content"]

    def chat_stream(self, prompt: str) -> Generator[str, None, None]:
        """
        Yields partial chunks of the response (streaming).
        """
        # We'll explicitly set 'stream=True' for chunked responses
        stream = chat(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            stream=True,
            **self.ollama_kwargs
        )
        for chunk in stream:
            # chunk is typically something like {"message": {"content": "..."}, "done": false/true}
            yield chunk["message"]["content"]

class OpenAILLM(BaseLLM):
    """
    Example class that uses OpenAI's ChatCompletion API.
    """

    def __init__(
        self,
        openai_api_key: str = OPENAI_API_KEY,
        model: str = "gpt-4o-mini",
        stream: bool = False,
        **openai_kwargs
    ):
        """
        :param openai_api_key: Your OpenAI API key.
        :param model: The OpenAI model to use (e.g., 'gpt-3.5-turbo', 'gpt-4').
        :param temperature: Sampling temperature.
        :param max_tokens: The maximum number of tokens to generate.
        :param stream: Whether to stream responses by default.
        """
        self.openai_api_key = openai_api_key
        self.model = model
        self.stream_by_default = stream
        self.client = OpenAI(api_key=self.openai_api_key)
        self.openai_kwargs = openai_kwargs

    def chat(self, prompt: str) -> str:
        """
        Returns the entire response from the LLM as a single string (blocking).
        """
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            stream=False,
            **self.openai_kwargs
        )
        return response.choices[0].message.content

    def chat_stream(self, prompt: str) -> Generator[str, None, None]:
        """
        Yields partial chunks of the response (streaming).
        """
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            stream=True,
            **self.openai_kwargs
        )

        for chunk in response:
            # Each chunk has a "delta" dict that may contain "content"
            delta = chunk["choices"][0]["delta"]
            if "content" in delta:
                yield delta["content"]