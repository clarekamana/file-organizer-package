# Publishing file-sorter-cli

Never put passwords or API tokens in this repository. Authenticate with your own
PyPI / TestPyPI API token, either when twine prompts (username `__token__`, password =
your token) or via `~/.pypirc` / the `TWINE_USERNAME` and `TWINE_PASSWORD` environment
variables. Tokens are created in your account settings on pypi.org and test.pypi.org
(they are separate accounts).

## 0. Before each release

- Bump `version` in `pyproject.toml` **and** `__version__` in `src/file_organizer/__init__.py`.
- Add an entry to `CHANGELOG.md`.
- Run `pytest`.
- A version can never be re-uploaded once used, even if deleted.

## 1. Build

```bash
python -m pip install --upgrade build twine
python -m build
```

Produces `dist/file_sorter_cli-<version>-py3-none-any.whl` and `dist/file_sorter_cli-<version>.tar.gz`.

## 2. Check the distribution

```bash
python -m twine check dist/*
```

## 3. Upload to TestPyPI

```bash
python -m twine upload --repository testpypi dist/*
```

(For `--repository testpypi` to work, `~/.pypirc` needs a `[testpypi]` section with
`repository = https://test.pypi.org/legacy/`. Otherwise use
`--repository-url https://test.pypi.org/legacy/`.)

## 4. Test the installation

In a fresh virtual environment:

```bash
pip install --index-url https://test.pypi.org/simple/ file-sorter-cli
file-sorter --version
```

## 5. Upload to PyPI

Only after TestPyPI looks right:

```bash
python -m twine upload dist/*
pip install file-sorter-cli
```
