"""Provisional offline assistance: TF-IDF example retrieval and impact rules.

This small English-language teaching model uses synthetic examples only. It is
not generative AI, a calibrated classifier, or instructor acceptance criteria.
Recommendations never change a ticket, category selection or database schema.
"""
from collections import Counter
import math
import re

EXAMPLES = (
    ("Hardware", "printer paper jam toner cartridge printing device"),
    ("Hardware", "laptop computer battery screen keyboard mouse monitor broken"),
    ("Hardware", "physical equipment cable disk hardware failure overheating"),
    ("Software", "application software crashes error update install program"),
    ("Software", "spreadsheet document browser operating system frozen bug"),
    ("Software", "email client application version compatibility configuration"),
    ("Access", "login password reset account locked authentication denied"),
    ("Access", "permission access folder authorization user credentials"),
    ("Access", "cannot sign in account multifactor authentication token"),
)
STOPWORDS = frozenset("a an the is are was were to of for and or my our in on with this that it i we cannot".split())
PRIORITY_DEFINITIONS = {
    "High": "Review promptly: text suggests a widespread outage, security incident or data loss.",
    "Normal": "Review through the ordinary support queue; impact is not established.",
    "Low": "Review when scheduled: text explicitly describes a cosmetic or non-urgent request.",
}


def tokens(text):
    return [word for word in re.findall(r"[^\W_]+", text.casefold()) if word not in STOPWORDS]


DOCUMENTS = [(category, Counter(tokens(text))) for category, text in EXAMPLES]
IDF = {word: math.log((1 + len(DOCUMENTS)) / (1 + sum(word in counts for _, counts in DOCUMENTS))) + 1
       for word in {word for _, counts in DOCUMENTS for word in counts}}


def recommend(title, description):
    """Return bounded, deterministic advice; no files, sockets or APIs are used."""
    if not isinstance(title, str) or not isinstance(description, str):
        raise ValueError("Title and description must be text")
    if len(title) > 200 or len(description) > 10000:
        raise ValueError("Title exceeds 200 characters or description exceeds 10000 characters")
    text = title + " " + description
    query = Counter(tokens(text))
    vector = {word: count * IDF[word] for word, count in query.items() if word in IDF}
    norm = math.sqrt(sum(value * value for value in vector.values()))
    scores = {}
    for category, counts in DOCUMENTS:
        weighted = {word: count * IDF[word] for word, count in counts.items()}
        denominator = norm * math.sqrt(sum(value * value for value in weighted.values()))
        score = sum(vector.get(word, 0) * value for word, value in weighted.items()) / denominator if denominator else 0
        scores[category] = max(scores.get(category, 0), score)
    ranked = sorted(scores, key=lambda category: (-scores[category], category))
    best, second = ranked[:2]
    category = best if scores[best] >= 0.12 and scores[best] - scores[second] >= 0.05 else None
    # These illustrative impact phrases are local policy, not official priorities.
    impact_text = re.sub(r"\b(?:no|not|without)\s+(?:an?\s+)?(?:outage|breach|ransomware|data loss)\b", "", text.casefold())
    high = re.search(r"\b(?:outage|ransomware|breach|data loss|all users|company wide)\b", impact_text)
    low = re.search(r"\b(?:cosmetic|non[- ]urgent|when convenient)\b", text.casefold())
    priority = "High" if high else "Low" if low else "Normal"
    evidence = sorted(set(query) & set(IDF))[:8]
    return {
        "provisional": True, "method": "local-tfidf-example-retrieval-v1",
        "category": category, "similarity": round(scores[best], 4),
        "priority": priority, "priority_definition": PRIORITY_DEFINITIONS[priority],
        "matched_terms": evidence,
        "explanation": "Review the suggested category manually." if category else "No clear category match; select a category manually.",
        "limitations": "Synthetic English examples; similarity is not probability. Priority rules are provisional and require human review. Nothing is saved automatically.",
    }
