"""Security, input validation, and output sanitization guardrails for AI Agent."""
import re
from typing import Any, Dict, List, Tuple


class AgentGuardrails:
    """Security checks enforcing prompt safety, credential redaction, and order sanitation."""

    FORBIDDEN_PATTERNS = [
        re.compile(r"\b(exec|eval|__import__|os|system|subprocess|shutil|shell|drop\s+table)\b", re.IGNORECASE),
        re.compile(r"sk-[a-zA-Z0-9_\-]{15,}", re.IGNORECASE),  # OpenAI key pattern
        re.compile(r"sbp_[a-zA-Z0-9_\-]{15,}", re.IGNORECASE),  # Supabase key pattern
    ]

    ALLOWED_SYMBOLS = {"EURUSD", "GBPUSD", "USDJPY", "XAUUSD", "AUDUSD", "USDCAD", "USDCHF"}

    @classmethod
    def sanitize_input(cls, prompt: str) -> str:
        """Sanitize user or autonomous trigger prompts, rejecting malicious code injection."""
        if not prompt or not isinstance(prompt, str):
            return ""

        for pattern in cls.FORBIDDEN_PATTERNS:
            if pattern.search(prompt):
                # Neutralize dangerous keywords
                prompt = pattern.sub("[BLOCKED_INSTRUCTION]", prompt)

        return prompt.strip()

    @classmethod
    def sanitize_output(cls, text: str) -> str:
        """Ensure no sensitive secrets or keys are leaked in agent responses."""
        if not text:
            return ""

        # Redact API keys
        sanitized = re.sub(r"sk-[a-zA-Z0-9_\-]{15,}", "[REDACTED_API_KEY]", text)
        sanitized = re.sub(r"sbp_[a-zA-Z0-9_\-]{15,}", "[REDACTED_KEY]", sanitized)
        sanitized = re.sub(r"(password|secret)\s*[:=]\s*['\"][^'\"]+['\"]", r"\1: '********'", sanitized, flags=re.IGNORECASE)
        return sanitized

    @classmethod
    def validate_order_request_input(
        cls,
        symbol: str,
        side: str,
        quantity: float,
        stop_loss: float,
        take_profit: float,
        reason: str,
    ) -> Tuple[bool, List[str]]:
        """Validate fundamental constraints on order requests before Risk Engine submission."""
        reasons = []

        clean_symbol = symbol.upper().strip()
        if clean_symbol not in cls.ALLOWED_SYMBOLS:
            reasons.append(f"Symbol '{symbol}' is not in approved system symbol whitelist {list(cls.ALLOWED_SYMBOLS)}.")

        clean_side = side.upper().strip()
        if clean_side not in ("BUY", "SELL"):
            reasons.append(f"Order side '{side}' is invalid; must be 'BUY' or 'SELL'.")

        if quantity <= 0.0 or quantity > 10.0:
            reasons.append(f"Quantity {quantity} is out of allowable boundaries (0.01 - 10.00 lots).")

        if stop_loss <= 0.0:
            reasons.append("Stop loss is required and must be strictly positive.")

        if take_profit <= 0.0:
            reasons.append("Take profit is required and must be strictly positive.")

        if not reason or len(reason.strip()) < 5:
            reasons.append("A detailed analytical reason must be provided for order auditing.")

        return (len(reasons) == 0, reasons)


guardrails = AgentGuardrails()
