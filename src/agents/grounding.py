"""
Document-agnostic grounding signals.

The Requirements Extractor invents subjects the source document never mentions.
A run against a wilderness weather station specification produced requirements
for humidity readings and light intensity control; neither word occurs anywhere
in the source, which covers temperature, pressure, sunshine, rainfall and wind.
Both fabrications carried acceptance criteria, deliverables and test cases
downstream and reached the user looking as credible as a grounded story.

Two measures here, neither of which removes anything:

  * `source_keywords` extracts the document's own vocabulary at generation
    time, for injection into the prompt. Prevention at the point of writing.
  * `assess_grounding` reports which of a story's terms do not occur in the
    source, for the reader to judge.

Nothing is deleted. A wrong label costs a reader a second look; a wrong
deletion loses a real requirement, which is the failure already fixed twice in
this pipeline (7864d85, 3dbc2ba) and the reason an earlier filtering attempt
was reverted (0f7990d).

Everything operates on the document supplied at runtime. There is no product
name, no domain vocabulary and no reference to any particular specification, so
a weather station, an insulin pump and a library system behave identically.
"""

import re
from collections import Counter
from typing import Any, Dict, List

# English function words plus vocabulary generic to any software specification.
# Grammatical and structural categories only -- nothing domain specific.
_STOP_WORDS = {
    "a", "an", "the", "and", "or", "but", "so", "that", "this", "these",
    "those", "is", "are", "be", "been", "being", "was", "were", "has", "have",
    "had", "it", "its", "their", "they", "them", "our", "your", "which",
    "who", "whom", "whose", "what", "when", "where", "while", "there", "here",
    "of", "to", "in", "on", "at", "by", "for", "with", "from", "into", "onto",
    "upon", "via", "as", "such", "all", "any", "each", "every", "both",
    "can", "will", "shall", "must", "should", "would", "may", "might", "also",
    "not", "than", "then", "if", "else", "other", "another", "more", "most",
    "some", "only", "very", "able", "want", "wants", "need", "needs",
    # generic specification vocabulary: present in documents about anything
    "system", "systems", "software", "hardware", "component", "components",
    "module", "modules", "data", "information", "user", "users", "provide",
    "provides", "support", "supports", "used", "using", "use", "part",
    "parts", "different", "several", "example", "examples", "include",
    "includes", "including", "required", "require", "requires", "requirement",
    "requirements", "well", "make", "makes", "made", "carry", "carried",
}

_WORD_RE = re.compile(r"[a-z][a-z-]{3,}")

_MIN_KEYWORD_LENGTH = 4
_DEFAULT_KEYWORD_LIMIT = 20

# No HIGH/MEDIUM/LOW band is published. Measured against a real document, the
# ratio does not separate the two populations: a fabricated story scored 44%
# while a genuine one scored 29%, because fabrications reuse the document's
# framing ("as a weather station operator ... monitor") and only the subject is
# invented. Asserting a confidence label on that basis would be false
# precision. The list of absent terms is the signal a reader can act on --
# "humidity" missing is obvious; "resist" missing is not a concern.


def _words(text: str) -> List[str]:
    """Content words of a text, lowercased, stop words removed."""
    return [w for w in _WORD_RE.findall((text or "").lower())
            if w not in _STOP_WORDS and len(w) >= _MIN_KEYWORD_LENGTH]


def source_keywords(source_text: str,
                    limit: int = _DEFAULT_KEYWORD_LIMIT) -> List[str]:
    """
    The document's own subject vocabulary, most frequent first.

    Injected into the extraction prompt so the model is told what this
    particular document is about, rather than relying on it to infer the
    boundary from an instruction alone. Derived entirely from the text
    supplied, so it adapts to whatever is uploaded.

    Args:
        source_text: The document being processed
        limit: Maximum number of keywords to return

    Returns:
        Keywords ordered by frequency, then alphabetically for stability
    """
    if not source_text:
        return []

    counts = Counter(_words(source_text))
    # Sort by descending frequency, then alphabetically, so the same document
    # always yields the same list.
    ordered = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return [word for word, _ in ordered[:limit]]


def assess_grounding(text: str, source_text: str) -> Dict[str, Any]:
    """
    Report which terms in generated text do not occur in the source document.

    Deliberately returns no verdict. Nothing is removed and no confidence band
    is asserted, because a ratio was measured not to separate fabricated from
    genuine text. What a reader can use is the vocabulary itself: a subject
    noun absent from the document stands out immediately.

    Args:
        text: Generated text, typically a story title plus its description
        source_text: The document it was generated from

    Returns:
        {"score": float, "unsupported_terms": [...]}
    """
    if not text or not source_text:
        return {"score": 1.0, "unsupported_terms": []}

    vocabulary = set(_words(source_text))
    # Allow simple morphology so "sensors" is supported by "sensor".
    for word in list(vocabulary):
        for suffix in ("s", "es", "ed", "ing"):
            if word.endswith(suffix) and len(word) - len(suffix) >= 3:
                vocabulary.add(word[: -len(suffix)])

    terms = []
    for word in _words(text):
        if word not in terms:
            terms.append(word)

    if not terms:
        return {"score": 1.0, "unsupported_terms": []}

    unsupported = [t for t in terms if not _supported(t, vocabulary)]
    score = (len(terms) - len(unsupported)) / len(terms)

    return {"score": round(score, 3), "unsupported_terms": unsupported}


def _supported(term: str, vocabulary: set) -> bool:
    """Whether a term appears in the source, allowing simple morphology."""
    if term in vocabulary:
        return True
    for suffix in ("s", "es", "ed", "ing"):
        if term.endswith(suffix) and term[: -len(suffix)] in vocabulary:
            return True
    return any(term + suffix in vocabulary for suffix in ("s", "es", "ed", "ing"))
