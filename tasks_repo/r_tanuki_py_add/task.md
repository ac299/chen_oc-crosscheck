In this repository, the method `tanuki.bloom_filter.BloomFilter.add` in `src/tanuki/bloom_filter.py` has lost its implementation: its body is `raise NotImplementedError`. Implement it.

Signature (line 60 of `src/tanuki/bloom_filter.py`):
```python
    def add(self, string):
```

Requirement:
- Functionality: Adds a string to the Bloom filter by calculating multiple hash values and setting the bits at the calculated indices in the bit array to 1. This is used to efficiently check whether an item might be in a set without storing the actual items.
- Arguments: :param self: BloomFilter. An instance of the BloomFilter class.
:param string: str, The string to be added to the Bloom filter. It is used to calculate the hash values which determine the indices in the bit array that should be set to 1.
:return: No return values.

Keep the signature and the rest of the repository unchanged except where the implementation
needs it. Tests for this function are not provided; the repository's other code and tests show
how it is used. Run Python and tests with `python` from the repository root.
