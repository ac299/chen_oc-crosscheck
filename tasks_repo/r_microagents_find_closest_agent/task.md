In this repository, the method `agent_similarity.AgentSimilarity.find_closest_agent` in `agents/agent_similarity.py` has lost its implementation: its body is `raise NotImplementedError`. Implement it.

Signature (line 69 of `agents/agent_similarity.py`):
```python
    def find_closest_agent(self, purpose_embedding: np.ndarray) -> Tuple[Optional[Agent], float]:
```

Requirement:
- Functionality: Finds the closest agent to a given purpose embedding by calculating the cosine similarity between the purpose embedding of each agent and the given purpose embedding. It returns the agent with the highest similarity score to the given purpose embedding.
- Arguments: :param purpose_embedding: np.ndarray, The embedding vector of the purpose for which the closest agent is being searched. It is used to compare against the purpose embeddings of the agents to find the closest match.
:return: Tuple[Optional[Agent], float], A tuple containing the closest agent to the given purpose embedding and the highest similarity score. If no agents are found or an error occurs, it may return None for the agent and -inf for the similarity score.

Keep the signature and the rest of the repository unchanged except where the implementation
needs it. Tests for this function are not provided; the repository's other code and tests show
how it is used. Run Python and tests with `python` from the repository root.
