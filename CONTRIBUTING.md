# Contributing to GearLoan

Contributions are welcome. Here is how to get involved.

## Reporting issues

Open a GitHub issue and describe what you expected versus what happened. Include
Django version, Python version, and steps to reproduce.

## Submitting a pull request

1. Fork the repo and create a branch from `main`.
2. Install dependencies and run the test suite before changing anything:
   ```bash
   pip install -r requirements.txt
   python manage.py test
   ```
3. Write tests for new behaviour; keep existing tests passing.
4. Follow PEP 8. Run `ruff check .` if available.
5. Open a pull request with a clear description of the change and why.

## Code style

- Python 3.11+, Django 5.x.
- Keep business logic in `services.py` and `rules.py`, not in views or models.
- No hardcoded dollar amounts outside `fees/calculators.py`.

## Licence

By contributing you agree that your work is released under the MIT licence.
