"""ISO date naming strategy: YYYY-MM-DD <description>.ext"""

import re
from pathlib import Path
from typing import Dict, List, Optional

from alakazam.naming.base import NamingStrategy


class ISODateNaming(NamingStrategy):
    """
    ISO date naming strategy: YYYY-MM-DD <description>.ext

    Generates filenames in the format:
        2024-01-15 Document Description.pdf

    Features:
        - ISO 8601 date format for sortability
        - Highlights document source or author near the start of the filename
        - Space-separated for readability
        - Extension preserved
        - Length limiting with intelligent truncation and dangling-word cleanup
    """

    # Invalid filename characters across platforms
    INVALID_CHARS = '<>:"/\\|?*'

    # Trailing words that should never be left dangling at the end of a truncated filename
    DANGLING_WORDS = {
        "a",
        "an",
        "and",
        "at",
        "billed",
        "by",
        "conferring",
        "covering",
        "for",
        "from",
        "in",
        "including",
        "of",
        "on",
        "or",
        "regarding",
        "reporting",
        "requiring",
        "showing",
        "submitted",
        "the",
        "to",
        "totaling",
        "with",
    }

    # Metadata keys checked in priority order for document source / author
    SOURCE_METADATA_KEYS = (
        "document_source",
        "source",
        "author",
        "institution_abbreviation",
        "provider_name",
        "organization",
        "company",
        "vendor",
        "merchant",
        "issuer",
        "school",
        "university",
        "department",
    )

    # Placeholder source values that should not be treated as valid document sources
    UNKNOWN_SOURCE_VALUES = {
        "n/a",
        "na",
        "none",
        "null",
        "unknown",
        "unknown author",
        "unknown company",
        "unknown issuer",
        "unknown merchant",
        "unknown organization",
        "unknown provider",
        "unknown sender",
        "unknown source",
        "unknown vendor",
        "unspecified",
    }

    def __init__(self, max_length: int = 80, title_case: bool = True):
        """
        Initialize ISO date naming strategy.

        Args:
            max_length: Maximum filename length (default 80)
            title_case: Whether to use title case for description (default True)
        """
        self.max_length = max_length
        self.title_case = title_case
        self._pattern = re.compile(r'^\d{4}-\d{2}-\d{2} .+\.\w+$')

    def generate_filename(self, analysis: Dict, original_name: str) -> str:
        """Generate filename in YYYY-MM-DD format highlighting source/author."""
        date = analysis['document_date']
        ext = Path(original_name).suffix

        description = self._select_base_description(analysis, original_name)
        source = self.extract_source(analysis, original_name=original_name)
        if source:
            description = self._ensure_source_highlighted(description, source)

        # Clean description
        description = self._clean_description(description)

        # Apply title case if requested
        if self.title_case:
            description = self._to_title_case(description)

        # Strip any trailing dangling words/punctuation even before truncation
        description = self._strip_dangling_tokens(description)

        # Build filename
        filename = f"{date} {description}{ext}"

        # Truncate if needed
        if len(filename) > self.max_length:
            filename = self._truncate(date, description, ext)

        return filename

    def _select_base_description(self, analysis: Dict, original_name: str) -> str:
        """Select the best base description from new_filename or description."""
        new_filename = analysis.get("new_filename")
        if isinstance(new_filename, str) and new_filename.strip():
            stem = self._extract_stem_from_filename(new_filename.strip())
            stem = self._strip_unknown_source_prefix(stem)
            if stem:
                return self._rewrite_prose_description(stem)

        raw_desc = analysis.get("description", Path(original_name).stem)
        if isinstance(raw_desc, str) and raw_desc.strip():
            return self._rewrite_prose_description(self._strip_unknown_source_prefix(raw_desc.strip()))

        return Path(original_name).stem

    @classmethod
    def _strip_unknown_source_prefix(cls, text: str) -> str:
        """Remove leading 'Unknown Merchant' / 'Unknown Vendor' prefixes from a stem."""
        for placeholder in sorted(cls.UNKNOWN_SOURCE_VALUES, key=len, reverse=True):
            if placeholder.startswith("unknown"):
                text = re.sub(r"^" + re.escape(placeholder) + r"\s+", "", text, flags=re.IGNORECASE).strip()
        return text

    @staticmethod
    def _extract_stem_from_filename(filename: str) -> str:
        """Strip leading YYYY-MM-DD date and trailing file extension from a filename."""
        stem = re.sub(r"\.[A-Za-z0-9]{2,5}$", "", filename).strip()
        stem = re.sub(r"^\d{4}-\d{2}-\d{2}[\s_-]+", "", stem).strip()
        return stem

    @classmethod
    def _is_valid_source(cls, val: object) -> bool:
        if not isinstance(val, str):
            return False
        cleaned = val.strip().lower()
        if not cleaned or cleaned in cls.UNKNOWN_SOURCE_VALUES:
            return False
        if cleaned.startswith("unknown ") or cleaned.startswith("unspecified ") or cleaned.startswith("generic "):
            return False
        return True

    @classmethod
    def extract_source(cls, analysis: Dict, original_name: Optional[str] = None) -> Optional[str]:
        """Extract the primary document source or author from an analysis dict."""
        if not isinstance(analysis, dict):
            return None

        for top_key in ("document_source", "source", "author"):
            val = analysis.get(top_key)
            if cls._is_valid_source(val):
                return cls._normalize_source_name(str(val).strip())

        metadata = analysis.get("metadata")
        if isinstance(metadata, dict):
            # Prefer short abbreviation if provider_name is very long and abbreviation exists
            abbrev = metadata.get("institution_abbreviation")
            if cls._is_valid_source(abbrev):
                return cls._normalize_source_name(str(abbrev).strip())

            for key in cls.SOURCE_METADATA_KEYS:
                val = metadata.get(key)
                if cls._is_valid_source(val):
                    return cls._normalize_source_name(str(val).strip())

        # Try extracting "from <Source>" or "submitted to <Source>" from description
        desc = analysis.get("description")
        if isinstance(desc, str):
            match = re.search(
                r"\b(?:from|submitted to|issued by|by)\s+(?:the\s+)?([A-Z][A-Za-z0-9&.,' -]{2,45}?)(?:\s+(?:for|to|by|regarding|covering|reporting|conferring|in|on|at|with|totaling|billed)\b|[,.]|$)",
                desc,
            )
            if match and cls._is_valid_source(match.group(1)):
                return cls._normalize_source_name(match.group(1).strip())

        # Fall back to a human-named prefix in original_name if not a generic scan filename
        if original_name:
            orig_stem = Path(original_name).stem
            if not re.match(r"^(?:\d{4}-\d{2}-\d{2}|IMG_|scan|doc|test|file)", orig_stem, flags=re.IGNORECASE):
                orig_clean = re.sub(r"\s+\b(?:receipt|invoice|statement|form|document|scan)\b.*$", "", orig_stem, flags=re.IGNORECASE).strip()
                if cls._is_valid_source(orig_clean) and len(orig_clean) >= 3:
                    return cls._normalize_source_name(orig_clean)

        return None

    @staticmethod
    def _normalize_source_name(source: str) -> str:
        """Clean and concisely normalize a source/organization name for filenames."""
        # If source has a parenthetical acronym like "United Services Automobile Association (USAA)", prefer the acronym if long
        paren_match = re.search(r"\(([A-Z0-9&]{2,10})\)", source)
        if paren_match and len(source) > 28:
            return paren_match.group(1)

        # Strip suffix noise like "- MCTR" or "- Bursar's Office"
        source = re.sub(r"\s+-\s+.*$", "", source).strip()
        # Strip corporate suffix punctuation like ", Inc." -> "" or " Inc"
        source = re.sub(r",?\s*\b(?:Inc\.?|LLC|L\.L\.C\.|Corp\.?|Corporation|Ltd\.?)$", "", source, flags=re.IGNORECASE).strip()
        # Strip commas (e.g. "University of California, Berkeley" -> "University of California Berkeley")
        source = source.replace(",", "")
        source = re.sub(r"\s{2,}", " ", source).strip()
        return source

    def _rewrite_prose_description(self, text: str) -> str:
        """Convert verbose prose descriptions into concise source-first title stems."""
        cleaned = text.strip().rstrip(".")

        # Strip verbose secondary clauses ("conferring ...", "showing ...", "including ...", "requiring ...", "covering ...", "with an estimated ...")
        cleaned = re.sub(
            r",?\s+\b(?:conferring|showing|including|requiring|covering|reporting|with an?)\b.*$",
            "",
            cleaned,
            flags=re.IGNORECASE,
        ).strip()

        # If "regarding <topic>" is followed by a claim/account number or long clause, keep concise topic if stem is short
        regarding_match = re.search(r",?\s+\bregarding\s+(?:an?\s+|the\s+)?(.+)$", cleaned, flags=re.IGNORECASE)
        if regarding_match:
            prefix = cleaned[: regarding_match.start()].strip()
            topic = regarding_match.group(1).strip()
            if len(prefix) < 42:
                # Keep up to 4 words of the topic
                topic_words = topic.split()[:4]
                cleaned = f"{prefix} {' '.join(topic_words)}"
            else:
                cleaned = prefix

        # Pattern: "<DocType> from/submitted to <Source> for/to/by/billed to <Recipient>..."
        match = re.match(
            r"^(?P<doc>.+?)\s+(?:from|submitted to|issued by)\s+(?:the\s+)?(?P<source>[A-Za-z0-9&.,' -]+?)(?:\s+(?:for|to|by|billed to)\s+(?P<rest>.+))?$",
            cleaned,
            flags=re.IGNORECASE,
        )
        if match:
            doc_part = match.group("doc").strip()
            source_part = self._normalize_source_name(match.group("source").strip())
            rest_part = (match.group("rest") or "").strip()
            # Clean "for <purpose>" chains inside rest_part if overly long
            rest_part = re.sub(r"\s+\b(?:for|at|totaling|paid via)\b.*$", "", rest_part, flags=re.IGNORECASE).strip()
            parts = [p for p in (source_part, doc_part, rest_part) if p]
            cleaned = " ".join(parts)

        # Pattern: "<DocType> for <Recipient> from <Source>"
        match_rev = re.match(
            r"^(?P<doc>.+?)\s+(?:for|to)\s+(?P<recipient>[A-Za-z0-9.' -]+?)\s+from\s+(?:the\s+)?(?P<source>[A-Za-z0-9&.,' -]+)$",
            cleaned,
            flags=re.IGNORECASE,
        )
        if match_rev:
            doc_part = match_rev.group("doc").strip()
            recipient_part = match_rev.group("recipient").strip()
            source_part = self._normalize_source_name(match_rev.group("source").strip())
            cleaned = f"{source_part} {doc_part} {recipient_part}"

        # Remove filler prepositions ("for", "totaling ...") to keep titles concise
        cleaned = re.sub(r"\s+\btotaling\b.*$", "", cleaned, flags=re.IGNORECASE).strip()
        cleaned = re.sub(r"\s+\bfor\s+", " ", cleaned, flags=re.IGNORECASE)

        # Clean symbols that clutter filenames (#, parentheses, commas)
        cleaned = cleaned.replace("#", "")
        cleaned = re.sub(r"[(),]", " ", cleaned)
        cleaned = re.sub(r"\s{2,}", " ", cleaned).strip()
        return cleaned

    def _ensure_source_highlighted(self, description: str, source: str) -> str:
        """Ensure the document source/author appears near the beginning of the description."""
        if not source:
            return description

        desc_lower = description.lower()

        # Check if source or a significant token/acronym of source is already in the first half
        candidates = self._source_match_candidates(source)
        early_window = desc_lower[: max(40, len(desc_lower) // 2)]
        if any(cand in early_window for cand in candidates):
            return description

        # If source appears later in the description, remove its later "from <source>" occurrence and prepend it
        for cand in sorted(candidates, key=len, reverse=True):
            if cand in desc_lower:
                pattern = re.compile(
                    r"\b(?:from|by|to|of)?\s*(?:the\s+)?" + re.escape(cand) + r"\b",
                    flags=re.IGNORECASE,
                )
                stripped = pattern.sub("", description).strip()
                stripped = re.sub(r"\s{2,}", " ", stripped).strip()
                return f"{source} {stripped}".strip()

        return f"{source} {description}".strip()

    @staticmethod
    def _source_match_candidates(source: str) -> List[str]:
        """Generate lowercase match candidates for a source (including common abbreviations)."""
        s_clean = re.sub(r"[^a-zA-Z0-9\s]", " ", source).lower()
        s_clean = re.sub(r"\s{2,}", " ", s_clean).strip()
        candidates = [s_clean]

        # Generate general abbreviations (e.g. "University of California Berkeley" -> "uc berkeley", "berkeley")
        uni_match = re.match(r"^university of ([a-z]+)\s+([a-z]+)$", s_clean)
        if uni_match:
            state_word, campus_word = uni_match.group(1), uni_match.group(2)
            candidates.extend([f"u{state_word[0]} {campus_word}", campus_word])

        # Strip " elementary " or " of <state>" for broader matching (e.g. "Oak Creek Elementary PTA" -> "oak creek pta")
        if " elementary " in s_clean:
            candidates.append(s_clean.replace(" elementary ", " "))
        if " of " in s_clean:
            candidates.append(s_clean.split(" of ")[0].strip())
        if s_clean.startswith("state of "):
            without_state = re.sub(r"^state of [a-z]+\s+", "", s_clean)
            if without_state:
                candidates.append(without_state)

        # Initials acronym for 3+ significant words
        sig_words = [w for w in s_clean.split() if w not in {"of", "the", "and", "for", "in"}]
        if len(sig_words) >= 3:
            acronym = "".join(w[0] for w in sig_words)
            candidates.append(acronym)

        # Also check first 2 significant words if multi-word, and any brand word preceding "bank"/"group"
        generic_org_words = {"of", "the", "and", "state", "for", "bank", "na", "n", "a", "inc", "llc", "corp"}
        words = [w for w in s_clean.split() if w not in {"of", "the", "and", "state", "for"}]
        if len(words) >= 2:
            candidates.append(" ".join(words[:2]))
        brand_words = [w for w in s_clean.split() if w not in generic_org_words and len(w) >= 4]
        candidates.extend(brand_words[:2])
        if len(words) == 1 and len(words[0]) >= 3:
            candidates.append(words[0])

        return list(dict.fromkeys(candidates))

    def validate(self, filename: str) -> bool:
        """Validate filename matches YYYY-MM-DD pattern."""
        if not self._pattern.match(filename):
            return False

        # Check for invalid characters
        if any(c in filename for c in self.INVALID_CHARS):
            return False

        # Check length
        if len(filename) > 255:  # Max filename length
            return False

        return True

    def _clean_description(self, description: str) -> str:
        """Remove invalid characters from description."""
        for char in self.INVALID_CHARS:
            description = description.replace(char, '')

        # Collapse multiple spaces
        description = ' '.join(description.split())

        return description.strip()

    def _to_title_case(self, text: str) -> str:
        """Convert to title case, preserving acronyms."""
        # Simple title case that preserves all-caps words
        words = []
        for word in text.split():
            if word.isupper() and len(word) > 1:
                # Keep acronyms as-is (e.g., "PDF", "LLC")
                words.append(word)
            else:
                words.append(word.capitalize())
        return ' '.join(words)

    def _strip_dangling_tokens(self, description: str) -> str:
        """Remove trailing prepositions, articles, conjunctions, single-letter initials, or punctuation from a stem."""
        words = description.split()
        while len(words) > 1:
            last_clean = words[-1].strip(".,;:-()[]{}").lower()
            if (
                not last_clean
                or last_clean in self.DANGLING_WORDS
                or (len(last_clean) == 1 and last_clean.isalpha())
            ):
                words.pop()
            else:
                words[-1] = words[-1].rstrip(".,;:-(")
                break
        return " ".join(words).strip()

    def _truncate(self, date: str, description: str, ext: str) -> str:
        """Intelligently truncate filename to max_length."""
        # Check if even date+ext fits
        min_length = len(date) + len(ext)
        if self.max_length < min_length:
            raise ValueError(
                f"max_length ({self.max_length}) is too small for date+extension "
                f"({min_length} chars minimum)"
            )

        # Calculate available space for description
        fixed_length = len(date) + len(ext) + 1  # +1 for space between date and description
        available = self.max_length - fixed_length

        if available < 10:
            # Not enough space for meaningful description
            return f"{date}{ext}"

        # Truncate at word boundary if possible
        truncated_desc = description[:available]

        # Try to truncate at last space if we cut mid-word
        if len(description) > available and description[available] != ' ':
            last_space = truncated_desc.rfind(' ')
            if last_space > available // 2:  # At least halfway through
                truncated_desc = truncated_desc[:last_space]
        else:
            last_space = truncated_desc.rfind(' ')
            if last_space > available // 2 and not description[:available].endswith(' '):
                # Keep full words if exact boundary, otherwise fall back to last_space if partial word
                pass

        truncated_desc = self._strip_dangling_tokens(truncated_desc.strip())

        return f"{date} {truncated_desc}{ext}"

    def __repr__(self) -> str:
        return f"ISODateNaming(max_length={self.max_length}, title_case={self.title_case})"
