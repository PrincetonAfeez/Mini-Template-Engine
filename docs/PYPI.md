# Publishing to PyPI

> **Status: not yet published.** The PyPI project URL in `pyproject.toml`
> (https://pypi.org/project/mini-template-engine/) is reserved and documented for the
> release workflow; the package is not yet on PyPI. Until the first release is cut,
> install from source (`pip install -e ".[dev]"`). After publishing, the package will
> be available at `pip install mini-template-engine`.

## One-time maintainer setup

1. Create a PyPI account and project named `mini-template-engine`.
2. Enable [Trusted Publishing](https://docs.pypi.org/trusted-publishers/) for this GitHub repository.
3. Create a GitHub environment named `pypi` with protection rules if desired.

## Release process

1. Update version in `pyproject.toml` and `template_engine/_version.py`.
2. Update `CHANGELOG.md`.
3. Create a GitHub Release (tag `v0.1.0` format).
4. The `Publish to PyPI` workflow builds, tests, and uploads the package.

## Local dry run

```bash
pip install -e ".[dev]"
python -m build
twine check dist/*
# twine upload --repository testpypi dist/*   # optional TestPyPI
```
