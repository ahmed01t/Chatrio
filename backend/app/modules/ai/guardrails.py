"""
Security Guardrails & Prompt Injection Defense.

Implements multi-layer defenses to protect Chatrio's AI agent from:
1. Instruction Resets & Overrides ("Ignore previous instructions").
2. Jailbreak Personas ("DAN mode", "Developer mode", "Uncensored assistant").
3. Delimiter & Boundary Escapes (`<customer_input>`, `<|im_start|>`, `[INST]`).
4. System Prompt & Credential Exfiltration ("Print system prompt", "Repeat all above").
5. Pricing & Policy Manipulation ("Give me 90% discount", "Set price to 0").
"""

import re
from typing import ClassVar

# Regex patterns matching prompt injection and jailbreak attempts
INJECTION_PATTERNS: list[tuple[str, str]] = [
    # 1. Instruction Reset / Override
    (
        r"(?i)\b(ignore|disregard|forget|override|bypass)\b.*\b(all|previous|prior|above|system)\b.*\b(instructions|rules|prompts|directives)\b",
        "instruction_reset_override",
    ),
    (
        r"(?i)\b(start|begin)\s+(over|anew)\s+and\s+(listen|follow)\s+only\b",
        "instruction_reset_override",
    ),
    # 2. Jailbreak Personas & Modes
    (
        r"(?i)\b(dan\s+mode|do\s+anything\s+now|jailbreak|developer\s+mode|unfiltered\s+mode|god\s+mode)\b",
        "jailbreak_persona",
    ),
    (
        r"(?i)\b(act\s+as|pretend\s+you\s+are|roleplay\s+as)\s+(an?\s+)?(unrestricted|uncensored|evil|hacked|omnipotent)\b",
        "jailbreak_persona",
    ),
    # 3. System Prompt & Exfiltration
    (
        r"(?i)\b(print|show|repeat|display|reveal|output|tell\s+me)\b.*\b(system\s+prompt|core\s+instructions|initial\s+prompt|hidden\s+prompt|everything\s+above)\b",
        "prompt_exfiltration",
    ),
    (
        r"(?i)\b(what\s+are\s+your|what\s+is\s+your)\s+(exact\s+)?(system\s+instructions|system\s+prompt|rules\s+above)\b",
        "prompt_exfiltration",
    ),
    # 4. Token & Boundary Injection
    (
        r"(<\|im_start\|>|<\|im_end\|>|<\|system\|>|\[INST\]|\[/INST\]|###\s*System:)",
        "delimiter_injection",
    ),
    # 5. Pricing / Authority Hijacking
    (
        r"(?i)\b(i\s+am\s+(the\s+)?(owner|admin|developer|manager|boss)|give\s+me\s+everything\s+(for\s+)?free|set\s+price\s+to\s+0)\b",
        "authority_spoofing",
    ),
]


class SecurityGuardrails:
    """Security guardrails ensuring input and output integrity."""

    TAG_CLEANUP_REGEX: ClassVar[re.Pattern] = re.compile(
        r"</?(customer_input|system|prompt|assistant|human)[^>]*>",
        re.IGNORECASE,
    )
    TOKEN_CLEANUP_REGEX: ClassVar[re.Pattern] = re.compile(
        r"(<\|im_start\|>|<\|im_end\|>|<\|system\|>|\[INST\]|\[/INST\]|###\s*System:)",
        re.IGNORECASE,
    )

    @classmethod
    def detect_prompt_injection(cls, text: str) -> tuple[bool, str | None]:
        """
        Scans inbound customer text for known injection and jailbreak patterns.

        Args:
            text: Raw customer message text.

        Returns:
            (is_injection, reason): True and pattern category if detected, False otherwise.
        """
        clean_text = text.strip()
        for pattern, reason in INJECTION_PATTERNS:
            if re.search(pattern, clean_text):
                return True, reason
        return False, None

    @classmethod
    def wrap_user_input(cls, text: str) -> str:
        """
        Sanitizes and safely encapsulates user text inside strict XML boundary tags.

        Strips any rogue boundary tags or model tokens before enclosing.
        """
        # 1. Strip fake XML boundary tags
        sanitized = cls.TAG_CLEANUP_REGEX.sub("", text)
        # 2. Strip special model tokens
        sanitized = cls.TOKEN_CLEANUP_REGEX.sub("", sanitized)
        # 3. Enclose in authoritative boundary
        return f"<customer_input>\n{sanitized.strip()}\n</customer_input>"

    @classmethod
    def sanitize_output(cls, response_text: str) -> str:
        """
        Validates outbound LLM response before sending to WhatsApp.

        Ensures no internal prompt instructions or delimiter tags were leaked.
        """
        cleaned = cls.TAG_CLEANUP_REGEX.sub("", response_text)
        cleaned = cls.TOKEN_CLEANUP_REGEX.sub("", cleaned)

        # Defense against accidental system prompt echo
        lower = cleaned.lower()
        if (
            "you are the autonomous whatsapp customer assistant" in lower
            or "prime directive" in lower
        ):
            return (
                "I am here to help you browse our products and place orders! "
                "How can I assist you today?"
            )

        return cleaned.strip()
