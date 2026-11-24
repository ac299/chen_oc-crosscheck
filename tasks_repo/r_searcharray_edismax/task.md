In this repository, the function `searcharray.solr.edismax` in `searcharray/solr.py` has lost its implementation: its body is `raise NotImplementedError`. Implement it.

Signature (line 169 of `searcharray/solr.py`):
```python
def edismax(frame: pd.DataFrame,
            q: str,
            qf: List[str],
            mm: Optional[str] = None,
            pf: Optional[List[str]] = None,
            pf2: Optional[List[str]] = None,
            pf3: Optional[List[str]] = None,
            q_op: str = "OR",
            similarity: Similarity = default_bm25) -> Tuple[np.ndarray, str]:
```

Requirement:
- Functionality: This function performs an Extended Disjunction Max Query (edismax) search over a given DataFrame, considering various search parameters such as query fields, minimum match specifications, and phrase, bigram, and trigram matches. It supports both term-centric and field-centric approaches to calculate the relevance scores of documents based on the input query and returns the scores along with an explanation of how they were computed.
- Arguments: :param frame: pd.DataFrame. The DataFrame over which the search is performed.
:param q: str. The query string used for the search.
:param qf: List[str]. The fields in the DataFrame to search against.
:param mm: Optional[str]. The minimum should match specification, which dictates the minimum number of query terms that must match. Defaults to None.
:param pf: Optional[List[str]]. The fields to search for phrase matches. Defaults to None.
:param pf2: Optional[List[str]]. The fields to search for bigram matches. Defaults to None.
:param pf3: Optional[List[str]]. The fields to search for trigram matches. Defaults to None.
:param q_op: str. The default operator for the query, which can be "OR" or "AND". Defaults to "OR".
:param similarity: Similarity. The similarity measure to use for scoring documents. Defaults to a BM25 similarity measure.
:return: Tuple[np.ndarray, str]. A tuple containing an array of search results scores and a string explaining the scoring.

Keep the signature and the rest of the repository unchanged except where the implementation
needs it. Tests for this function are not provided; the repository's other code and tests show
how it is used. Run Python and tests with `python` from the repository root.
