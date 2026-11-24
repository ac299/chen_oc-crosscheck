In this repository, the function `chat.utils.run_cmd` in `chat/utils.py` has lost its implementation: its body is `raise NotImplementedError`. Implement it.

Signature (line 265 of `chat/utils.py`):
```python
def run_cmd(cmd: str):
```

Requirement:
- Functionality: Executes a given bash command by printing it first and then using the system's command line interface to run it.
- Arguments: :param cmd: str, The bash command to be executed.
:return: int, The exit status of the executed command. A value of 0 typically indicates that the command was executed successfully, while any other value indicates an error.

Keep the signature and the rest of the repository unchanged except where the implementation
needs it. Tests for this function are not provided; the repository's other code and tests show
how it is used. Run Python and tests with `python` from the repository root.
