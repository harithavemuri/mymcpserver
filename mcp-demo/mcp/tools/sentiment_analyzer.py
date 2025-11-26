from typing import Dict, Any, List, Tuple
import re

# Expanded word lists for sentiment analysis
POSITIVE_WORDS = {
    'good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic', 'awesome',
    'outstanding', 'superb', 'perfect', 'best', 'love', 'like', 'enjoy', 'happy',
    'joy', 'pleased', 'satisfied', 'delighted', 'brilliant', 'fabulous', 'stellar',
    'terrific', 'marvelous', 'exceptional', 'splendid', 'incredible', 'admirable',
    'charming', 'delicious', 'enjoyable', 'favorable', 'friendly', 'fun', 'glad',
    'graceful', 'grateful', 'honest', 'kind', 'lovely', 'lucky', 'nice', 'pleasant',
    'proud', 'relaxed', 'successful', 'thrilled', 'upbeat', 'vibrant', 'winning',
    'witty', 'wonderful', 'yay', 'yes', 'yummy', 'zealous', 'adore', 'bliss',
    'celebrate', 'cheer', 'cheerful', 'delight', 'ecstatic', 'elated', 'euphoric',
    'exhilarated', 'festive', 'gleeful', 'jolly', 'jovial', 'jubilant', 'merry',
    'optimistic', 'peaceful', 'playful', 'positive', 'radiant', 'sunny', 'upbeat',
    'victorious'
}

NEGATIVE_WORDS = {
    'bad', 'terrible', 'awful', 'horrible', 'worst', 'poor', 'disappointing',
    'hate', 'dislike', 'sad', 'unhappy', 'angry', 'annoyed', 'frustrated',
    'miserable', 'depressed', 'upset', 'displeased', 'angry', 'annoyed',
    'anxious', 'appalling', 'atrocious', 'awful', 'boring', 'broken', 'cancer',
    'crash', 'cruel', 'cry', 'damage', 'damn', 'death', 'defeated', 'defective',
    'deny', 'depressed', 'deprived', 'desperate', 'difficult', 'dirty',
    'disaster', 'disgusting', 'failure', 'fear', 'feeble', 'fool', 'foul',
    'frighten', 'gross', 'guilty', 'hard', 'harsh', 'hate', 'hideous', 'hurt',
    'ill', 'inferior', 'injure', 'jealous', 'lose', 'lousy', 'mess', 'miss',
    'nasty', 'naughty', 'negative', 'nervous', 'not', 'pain', 'pessimistic',
    'poor', 'repulsive', 'sad', 'scare', 'selfish', 'sick', 'sickening',
    'stingy', 'stop', 'stress', 'terrible', 'trouble', 'ugly', 'unfair',
    'unhappy', 'upset', 'wrong', 'stupid'
}

# Intensifiers that can modify sentiment
INTENSIFIERS = {
    'very', 'really', 'extremely', 'absolutely', 'completely', 'totally',
    'utterly', 'exceptionally', 'incredibly', 'remarkably', 'particularly',
    'especially', 'enormously', 'hugely', 'unusually', 'uncommonly', 'decidedly',
    'highly', 'truly', 'genuinely', 'certainly', 'undoubtedly', 'definitely',
    'surely', 'assuredly', 'drastically', 'exceedingly', 'extraordinarily',
    'immensely', 'intensely', 'powerfully', 'profoundly', 'strikingly',
    'tremendously', 'unusually', 'vastly'
}

# Negation words that can flip sentiment
NEGATIONS = {
    'not', 'no', 'never', 'none', 'nobody', 'nothing', 'neither', 'nowhere',
    'hardly', 'scarcely', 'barely', 'doesnt', 'isnt', 'wasnt', 'shouldnt',
    'wouldnt', 'couldnt', 'wont', 'cant', 'dont'
}

def analyze_sentiment(text: str) -> Tuple[float, float]:
    """
    Simple sentiment analysis that returns polarity and subjectivity scores.
    Returns:
        Tuple of (polarity, subjectivity) where both are in range [-1.0, 1.0]
    """
    words = re.findall(r'\b\w+\b', text.lower())
    if not words:
        return 0.0, 0.0

    pos_count = 0
    neg_count = 0
    word_count = len(words)

    for i, word in enumerate(words):
        # Check for negations (simple approach: if previous word is a negation)
        is_negated = (i > 0 and words[i-1] in NEGATIONS)

        if word in POSITIVE_WORDS:
            if is_negated:
                neg_count += 1
            else:
                pos_count += 1
        elif word in NEGATIVE_WORDS:
            if is_negated:
                pos_count += 1
            else:
                neg_count += 1

    # Count intensifiers that might modify sentiment
    intensifier_count = sum(1 for word in words if word in INTENSIFIERS)

    # Simple polarity calculation
    if pos_count == 0 and neg_count == 0:
        polarity = 0.0
    else:
        polarity = (pos_count - neg_count) / (pos_count + neg_count)

    # Apply intensifier effect (up to 50% stronger sentiment)
    if polarity != 0 and intensifier_count > 0:
        polarity = polarity * (1 + min(0.5, intensifier_count * 0.1)) * (1 if polarity > 0 else -1)

    # Ensure polarity is within bounds
    polarity = max(-1.0, min(1.0, polarity))

    # Calculate subjectivity (0.0 = completely objective, 1.0 = completely subjective)
    sentiment_word_count = pos_count + neg_count
    if word_count > 0:
        subjectivity = min(1.0, (sentiment_word_count / word_count) * 2.5)
    else:
        subjectivity = 0.0

    return polarity, subjectivity

from ..models import ToolName, TextRequest, ToolResponse
from .base import BaseTool


class SentimentAnalyzer(BaseTool):
    """A tool for analyzing sentiment in text using a custom rule-based approach."""

    def __init__(self, **kwargs):
        super().__init__(name=ToolName.SENTIMENT_ANALYZER, **kwargs)

    @property
    def description(self) -> str:
        return "Analyzes the sentiment of text using a rule-based approach."

    def _count_words(self, text: str) -> int:
        """Count the number of words in the text."""
        return len(re.findall(r'\b\w+\b', text))

    def _count_sentences(self, text: str) -> int:
        """Count the number of sentences in the text."""
        # Simple sentence splitting on common punctuation
        sentences = re.split(r'[.!?]+', text)
        return len([s for s in sentences if s.strip()])

    async def process(self, request: TextRequest) -> ToolResponse:
        """Analyze the sentiment of the input text."""
        text = request.text.strip()
        if not text:
            return ToolResponse(
                tool_name=self.name,
                result={
                    "polarity": 0.0,
                    "subjectivity": 0.0,
                    "word_count": 0,
                    "sentence_count": 0
                },
                metadata={"processed": False, "error": "Empty input text"}
            )

        # Analyze sentiment using our custom function
        polarity, subjectivity = analyze_sentiment(text)

        # Count words and sentences
        word_count = self._count_words(text)
        sentence_count = self._count_sentences(text)

        # Determine overall sentiment label
        if polarity > 0.1:
            sentiment_label = "positive"
        elif polarity < -0.1:
            sentiment_label = "negative"
        else:
            sentiment_label = "neutral"

        # Prepare response with label
        result = {
            "polarity": round(polarity, 4),
            "subjectivity": round(subjectivity, 4),
            "label": sentiment_label,  # Make sure this is included
            "word_count": word_count,
            "sentence_count": sentence_count
        }

        # Add sentence-level analysis if requested
        if request.params.get("analyze_sentences", False):
            sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
            result["sentences"] = []

            for sentence in sentences:
                sent_polarity, sent_subjectivity = analyze_sentiment(sentence)

                # Determine sentiment label
                if sent_polarity > 0.1:
                    sent_label = "positive"
                elif sent_polarity < -0.1:
                    sent_label = "negative"
                else:
                    sent_label = "neutral"

                result["sentences"].append({
                    "text": sentence,
                    "sentiment": {
                        "polarity": round(sent_polarity, 4),
                        "subjectivity": round(sent_subjectivity, 4),
                        "label": sent_label
                    },
                    "word_count": self._count_words(sentence)
                })

        return ToolResponse(
            tool_name=self.name,
            result=result,
            metadata={"processed": True}
        )
