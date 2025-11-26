from typing import Dict, Any, List, Optional
import re
from collections import Counter

# Common English stop words
STOP_WORDS = {
    'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', 'your',
    'yours', 'yourself', 'yourselves', 'he', 'him', 'his', 'himself', 'she',
    'her', 'hers', 'herself', 'it', 'its', 'itself', 'they', 'them', 'their',
    'theirs', 'themselves', 'what', 'which', 'who', 'whom', 'this', 'that',
    'these', 'those', 'am', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
    'have', 'has', 'had', 'having', 'do', 'does', 'did', 'doing', 'a', 'an',
    'the', 'and', 'but', 'if', 'or', 'because', 'as', 'until', 'while', 'of',
    'at', 'by', 'for', 'with', 'about', 'against', 'between', 'into', 'through',
    'during', 'before', 'after', 'above', 'below', 'to', 'from', 'up', 'down',
    'in', 'out', 'on', 'off', 'over', 'under', 'again', 'further', 'then',
    'once', 'here', 'there', 'when', 'where', 'why', 'how', 'all', 'any', 'both',
    'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not',
    'only', 'own', 'same', 'so', 'than', 'too', 'very', 'can', 'will', 'just',
    'should', 'now', 'd', 'll', 'm', 'o', 're', 've', 'y', 'ain', 'couldn',
    'didn', 'doesn', 'hadn', 'hasn', 'haven', 'isn', 'mightn', 'mustn', 'needn',
    'shan', 'shouldn', 'wasn', 'weren', 'won', 'wouldn'
}

# Common English punctuation
PUNCTUATION = set("!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~")

from ..models import ToolName, TextRequest, ToolResponse
from .base import BaseTool

class SimpleKeywordExtractor(BaseTool):
    """A simple keyword extractor that doesn't rely on any external NLP libraries."""

    def __init__(self, **kwargs):
        super().__init__(name=ToolName.KEYWORD_EXTRACTOR, **kwargs)
        self.stop_words = STOP_WORDS

    @property
    def description(self) -> str:
        return "Extracts keywords and key phrases from text using basic text analysis."

    def _is_punctuation(self, char: str) -> bool:
        """Check if a character is a punctuation mark."""
        return char in PUNCTUATION

    def _is_stop_word(self, word: str) -> bool:
        """Check if a word is a stop word."""
        return word.lower() in self.stop_words

    def _clean_word(self, word: str) -> str:
        """Remove punctuation and lowercase a word."""
        # Remove punctuation from the beginning and end of the word
        while word and self._is_punctuation(word[0]):
            word = word[1:]
        while word and self._is_punctuation(word[-1]):
            word = word[:-1]
        return word.lower()

    def _extract_named_entities(self, text: str) -> List[Dict[str, Any]]:
        """Extract potential named entities using capitalization patterns."""
        # Look for capitalized words/phrases as potential named entities
        words = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)

        # Filter out common false positives
        common_phrases = {'The', 'And', 'For', 'But', 'Or', 'Not', 'With', 'This', 'That'}
        named_entities = []

        for phrase in words:
            # Skip single-letter words and common phrases
            if len(phrase) > 1 and phrase not in common_phrases:
                named_entities.append({
                    'text': phrase,
                    'type': 'entity'  # Generic type
                })

        return named_entities

    def _extract_keywords(self, text: str, top_n: int = 10) -> List[Dict[str, Any]]:
        """Extract keywords using basic frequency analysis."""
        # Simple word tokenization using regex (words with at least 2 letters)
        words = re.findall(r'\b[a-z]{2,}\b', text.lower())

        if not words:
            return []

        # Filter out stop words and count frequencies
        word_counts = Counter(word for word in words if word not in self.stop_words)

        # Calculate total words (for frequency percentage)
        total_words = len(words)

        # Get top N keywords with their frequency percentage
        keywords = []
        for word, count in word_counts.most_common(top_n):
            score = (count / total_words) * 100
            keywords.append({
                'phrase': word,
                'score': round(score, 2)
            })

        return keywords

    async def process(self, request: TextRequest) -> ToolResponse:
        """Extract keywords and key phrases from the input text."""
        text = request.text.strip()
        if not text:
            return ToolResponse(
                tool_name=self.name,
                result={
                    "keywords": [],
                    "named_entities": [],
                    "text_length": 0,
                    "word_count": 0
                },
                metadata={"processed": False, "error": "Empty input text"}
            )

        params = request.params or {}
        top_n = min(int(params.get("top_n", 10)), 50)  # Limit to 50 max
        extract_named_entities = params.get("extract_named_entities", False)

        # Extract keywords and named entities
        keywords = self._extract_keywords(text, top_n=top_n)
        named_entities = self._extract_named_entities(text) if extract_named_entities else []

        # Count words (simple approach)
        words = re.findall(r'\b\w+\b', text)

        # Prepare response
        result = {
            "keywords": keywords,
            "named_entities": named_entities,
            "text_length": len(text),
            "word_count": len(words)
        }

        return ToolResponse(
            tool_name=self.name,
            result=result,
            metadata={"processed": True}
        )

# For backward compatibility
KeywordExtractor = SimpleKeywordExtractor
