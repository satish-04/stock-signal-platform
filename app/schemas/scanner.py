import re
from datetime import date

from pydantic import BaseModel, Field, field_validator

SYMBOL_PATTERN = re.compile(r"[A-Z0-9^][A-Z0-9.\-]{0,15}")


class OptionsScanRequest(BaseModel):
    """Both fields are optional: the default scan covers the standard universe and the
    next weekly expiry."""

    expiry: date | None = None
    symbols: list[str] | None = Field(default=None, min_length=1, max_length=300)

    @field_validator("symbols")
    @classmethod
    def normalize_symbols(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return None
        symbols = [symbol.strip().upper() for symbol in value]
        invalid = [symbol for symbol in symbols if not SYMBOL_PATTERN.fullmatch(symbol)]
        if invalid:
            raise ValueError(f"Invalid symbols: {', '.join(invalid[:5])}")
        return list(dict.fromkeys(symbols))
