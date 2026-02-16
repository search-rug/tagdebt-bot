import os
import json
import copy
import logging
import traceback
from typing import List, Optional
from pydantic import BaseModel, Field
import instructor
from instructor import Provider
from model import factory

class TechDebtClassification(BaseModel):
    contains_technical_debt: bool = Field(..., description="True if the text discusses technical debt, false otherwise.")
    rationale: str = Field(..., description="A step-by-step explanation for the decision, based on the analysis.")
    evidence: List[str] = Field(..., description="Exact sentence(s) from the text that support the decision. Empty list if no technical debt.")

class SATD_LLM_Detector:
    """
    LLM-based Self-admitted technical debt classifier using Instructor.
    Supports native API providers: OpenAI, Anthropic, and Google Gemini (AI Studio).
    """

    def __init__(self, model_name: str, api_key: Optional[str] = None, prompt_file: str = "plugins/satd_llm_instructor/prompts.json"):
        self.model_name = model_name
        self.api_key = api_key
        self.prompt_file = prompt_file
        self._client = None  # Lazy initialization
        self.prompt_messages = self._load_prompt_messages()

    @property
    def client(self) -> instructor.Instructor:
        if self._client is None:
            self._client = self._get_llm_client()
        return self._client

    def _get_llm_client(self) -> instructor.Instructor:
        if '/' not in self.model_name:
            raise ValueError("MODEL name must be in the format '<provider>/<model_name>'")

        provider, name = self.model_name.split('/', 1)
        provider_env_map = {
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "google": "GEMINI_API_KEY"
        }
        
        env_key_name = provider_env_map.get(provider)
        api_key = self.api_key or (os.getenv(env_key_name) if env_key_name else None) or os.getenv("API_KEY")

        if not api_key:
            raise ValueError(f"API key missing for provider '{provider}'. Set {env_key_name or 'API_KEY'} in .env.")

        if provider == "openai":
            # Enable Responses mode for OpenAI
            return instructor.from_provider(
                self.model_name, 
                api_key=api_key, 
                mode=instructor.Mode.RESPONSES_TOOLS
            )
        else:
            # Standard structured output for Google and Anthropic
            return instructor.from_provider(self.model_name, api_key=api_key)

    def _load_prompt_messages(self) -> List[dict]:
        try:
            with open(self.prompt_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logging.error(f"Error loading prompt file {self.prompt_file}: {e}")
            return [
                {"role": "system", "content": "You are an expert software architect analyzing text for technical debt."},
                {"role": "user", "content": "Analyze the text below: "}
            ]

    def label(self, text: str) -> str:
        try:
            client = self.client
        except Exception as e:
            logging.error(f"Model '{self.model_name}' failed to initialize: {e}")
            return "error: missing configuration"

        provider = self.model_name.split('/')[0]

        try:
            if provider == "openai":
                system_content = self.prompt_messages[0]['content']
                user_instruction = self.prompt_messages[1]['content']
                full_input = f"{system_content}\n\nTask: {user_instruction}\n\nIssue Text:\n{text}"
                
                classification = client.responses.create(
                    input=full_input,
                    response_model=TechDebtClassification,
                    max_retries=2,
                    max_tokens=4000
                )
            else:
                messages = copy.deepcopy(self.prompt_messages)
                messages[-1]['content'] += f"\n\nText: {text}"
                
                classification = client.create(
                    messages=messages,
                    response_model=TechDebtClassification,
                    max_retries=2,
                    max_tokens=4000
                )

            return "SATD" if classification.contains_technical_debt else "non-SATD"
        except Exception as e:
            logging.error(f"LLM call for '{self.model_name}' failed.")
            logging.error(f"Error Type: {type(e).__name__}")
            logging.error(f"Error Message: {str(e)}")
            if hasattr(e, 'last_response'):
                logging.error(f"Raw Response: {e.last_response}")
            return "error"

def initialize() -> None:
    factory.register_model("SATD_LLM_Instructor", SATD_LLM_Detector)
