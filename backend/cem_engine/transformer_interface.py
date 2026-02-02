from typing import Optional
import json
import logging

logger = logging.getLogger(__name__)

try:
    from transformers import AutoModelForSeq2SeqLM, AutoTokenizer, pipeline
except Exception as e:
    # Delay import errors until used
    AutoModelForSeq2SeqLM = None
    AutoTokenizer = None
    pipeline = None


class HFPromptParser:
    """Simple Hugging Face based prompt parser for extracting JSON specs."""

    def __init__(self, model_name: str = "google/flan-t5-large", device: Optional[int] = None):
        if pipeline is None:
            raise RuntimeError("transformers not available; install requirements")

        self.model_name = model_name
        self.device = device if device is not None else -1
        # Use text2text-generation pipeline which works with many seq2seq models
        try:
            self.pipe = pipeline(
                "text2text-generation",
                model=self.model_name,
                device=self.device,
                truncation=True
            )
        except Exception as e:
            logger.warning(f"Failed to initialize pipeline for {model_name}: {e}")
            # Re-raise to surface issues during initialization
            raise

    def _prepare_prompt(self, user_prompt: str) -> str:
        system_prompt = (
            "You are an expert robotics engineer who extracts precise specifications from natural language.\n\n"
            "Extract and return ONLY a JSON object with the EXACT structure specified.\n"
            "If information is missing, use engineering defaults. Return only JSON, no explanations.\n\n"
            "User prompt:\n" + user_prompt
        )
        return system_prompt

    def parse(self, prompt: str, max_length: int = 2048) -> dict:
        text = self._prepare_prompt(prompt)

        # Run generation
        outputs = self.pipe(text, max_length=max_length, do_sample=False)
        raw = outputs[0]["generated_text"] if isinstance(outputs[0], dict) else str(outputs[0])

        # Strip code fences if present
        raw = raw.strip()
        if raw.startswith("```"):
            # remove first fence line and trailing fence
            raw = raw.strip('`')

        # Try to load JSON
        try:
            spec = json.loads(raw)
            return spec
        except json.JSONDecodeError:
            # Attempt to find a JSON substring
            import re
            m = re.search(r"\{[\s\S]*\}", raw)
            if m:
                try:
                    return json.loads(m.group(0))
                except Exception:
                    logger.error("Failed to parse JSON substring from model output")
            logger.error(f"Unable to parse JSON from model output: {raw}")
            raise
