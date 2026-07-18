
# Testing

Cashflow uses Pytest for testing. Tests are generally located in a `tests.py` file in each Django app.


## Runing tests
To run all the tests in the project, use the following command:

```bash
poetry run pytest
```

To run tests for a specific app, use the following command:

```bash
poetry run pytest path/to/app/tests.py
```