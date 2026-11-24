`semver.py` implements `parse(version)` and `compare(a, b)` for Semantic Versioning 2.0.0, but users report wrong results. Fix the module so that it follows these rules.

- `parse(version)` returns `(major, minor, patch, prerelease, build)`. `major`, `minor` and `patch` are ints. `prerelease` and `build` are tuples of identifier strings, or the empty tuple when absent.
- `parse` raises `ValueError` for any string that is not a valid SemVer 2.0.0 version. This includes numeric core parts with leading zeros (`01.0.0`), empty identifiers (`1.0.0-`, `1.0.0+`, `1.0.0-alpha..1`), numeric prerelease identifiers with leading zeros (`1.0.0-01`), characters outside `[0-9A-Za-z-]` in identifiers, and any surrounding whitespace or trailing newline. Build identifiers may have leading zeros (`1.0.0+001` is valid).
- `compare(a, b)` returns -1, 0 or 1 following SemVer precedence (spec item 11). Core parts compare numerically. A version with a prerelease is lower than the same version without one. Prerelease identifiers compare left to right: numeric identifiers compare numerically, alphanumeric identifiers compare in ASCII order, and a numeric identifier is lower than an alphanumeric one. When all preceding identifiers are equal, the longer prerelease is higher.
- Build metadata is ignored for precedence, so `compare("1.0.0+a", "1.0.0+b") == 0`.

Keep the existing function names and return types. Run the tests with `python -m pytest -q`.
