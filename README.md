# X2J-beta

Utilities to convert and transform Excel intervention data to a JSON structure.

## Installation

```
pip install -r requirements.txt
```

Pandas is optional.  If it is not available the utilities fall back to a minimal
OpenXML parser to read Excel files.

## Running tests

```
pytest -q
```