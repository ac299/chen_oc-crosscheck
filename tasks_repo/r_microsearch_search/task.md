In this repository, the method `microsearch.engine.SearchEngine.search` in `src/microsearch/engine.py` has lost its implementation: its body is `raise NotImplementedError`. Implement it.

Signature (line 60 of `src/microsearch/engine.py`):
```python
    def search(self, query: str) -> dict[str, float]:
```

Requirement:
- Functionality: The function performs a search based on the input query. It normalizes the query string, splits it into keywords, and then calculates the BM25 score for each keyword across URLs. The scores for URLs are aggregated and returned as a dictionary where each URL is a key and its aggregated score is the value.
- Arguments: :param self: SearchEngine. An instance of the SearchEngine class.
:param query: str, The search query input by the user. It is normalized and split into keywords for scoring.
:return: dict[str, float], A dictionary where each key is a URL and its value is the aggregated BM25 score based on the input query's keywords.

Keep the signature and the rest of the repository unchanged except where the implementation
needs it. Tests for this function are not provided; the repository's other code and tests show
how it is used. Run Python and tests with `python` from the repository root.
