"""Base class for all TravelMind agents."""
from __future__ import annotations

import json
from typing import Any

import anthropic

from travel_mind.config import ANTHROPIC_API_KEY, MAX_TOKENS, MODEL
from travel_mind.tools import execute_tool


class BaseAgent:
    """Runs a Claude agentic loop with tool use and prompt caching."""

    name: str = "base"
    system_prompt: str = "You are a helpful travel AI agent."
    tools: list[dict] = []

    def __init__(self):
        self._client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    def run(self, user_message: str, customer_profile=None, extra_context: dict | None = None) -> tuple[str, int]:
        """
        Execute the agentic loop: send message → handle tool calls → loop until end_turn.
        Returns (final_text, total_tokens_used).
        """
        messages = [{"role": "user", "content": user_message}]
        total_tokens = 0

        while True:
            response = self._client.messages.create(
                model=MODEL,
                max_tokens=MAX_TOKENS,
                system=[
                    {
                        "type": "text",
                        "text": self.system_prompt,
                        "cache_control": {"type": "ephemeral"},
                    }
                ],
                tools=self.tools,
                messages=messages,
            )

            total_tokens += response.usage.input_tokens + response.usage.output_tokens

            if response.stop_reason == "end_turn":
                text = self._extract_text(response.content)
                return text, total_tokens

            if response.stop_reason == "tool_use":
                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        result = execute_tool(block.name, block.input, customer_profile)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": json.dumps(result),
                        })

                messages.append({"role": "assistant", "content": response.content})
                messages.append({"role": "user", "content": tool_results})
            else:
                text = self._extract_text(response.content)
                return text, total_tokens

    @staticmethod
    def _extract_text(content: list) -> str:
        parts = []
        for block in content:
            if hasattr(block, "type") and block.type == "text":
                parts.append(block.text)
        return "\n".join(parts)
