# Okasa
Ohh ma gaa

## Tests & CI ✅

- Install runtime deps: `pip install -r requirements.txt` (includes `pillow` and `cairosvg`).
- Install test runner: `pip install pytest`.
- Run smoke tests locally: `pytest tests/test_scripts_smoke.py -q`.

A GitHub Actions workflow `.github/workflows/ci.yml` runs the tests on push and pull requests to `main`.
