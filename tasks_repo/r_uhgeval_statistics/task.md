In this repository, the method `xinhua.XinhuaHallucinations.statistics` in `uhgeval/dataset/xinhua.py` has lost its implementation: its body is `raise NotImplementedError`. Implement it.

Signature (line 32 of `uhgeval/dataset/xinhua.py`):
```python
    def statistics(self) -> dict:
```

Requirement:
- Functionality: Calculates and returns the statistics of different types of objects contained in the XinhuaHallucinations instance's data. It counts the occurrences of each type ('doc', 'gen', 'kno', 'num') and updates the statistics accordingly.
- Arguments: :param self: XinhuaHallucinations. An instance of the XinhuaHallucinations class. It uses the 'data' attribute of the instance, which is expected to be a list of dictionaries, each with a 'type' key.
:return: dict. A dictionary with keys corresponding to the types ('doc', 'gen', 'kno', 'num') and values representing the count of each type found in the 'data' attribute of the instance.

Keep the signature and the rest of the repository unchanged except where the implementation
needs it. Tests for this function are not provided; the repository's other code and tests show
how it is used. Run Python and tests with `python` from the repository root.
