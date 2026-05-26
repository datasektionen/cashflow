# Update project dependencies

This project uses Poetry to manage dependencies.

## 1. Check which packages need updating

```bash
poetry show --outdated
```

You should see an output similar to this, showing which packages that can be updated:

```
certifi             2026.2.25 2026.4.22 Python package for providing Mozilla's CA Bundle.
charset-normalizer  3.4.5     3.4.7     The Real First Universal Charset Detector. Open, modern and actively maintained alternative to Chardet.
click               8.3.1     8.3.3     Composable command line interface toolkit
cryptography        46.0.5    48.0.0    cryptography is a package which provides cryptographic recipes and primitives to Python developers.
django              6.0.3     6.0.5     A high-level Python web framework that encourages rapid development and clean, pragmatic design.
djangorestframework 3.16.1    3.17.1    Web APIs for Django, made easy.
gunicorn            25.1.0    26.0.0    WSGI HTTP Server for UNIX
idna                3.11      3.15      Internationalized Domain Names in Applications (IDNA)
```

There are two options when updating a dependency: (a) update within version constraints (these are defined in
pyproject.toml), which should prevent breaking changes, or (b) update to the latest version, which may include
breaking changes.

## 2.a) Update within version constraints

Updating within version constraints is simple, just run the following command:

```bash
poetry update
```

This will update all dependencies to the latest version that satisfies the version constraints defined in
`pyproject.toml`.

## 2.b) Update to the latest version

To update to the latest version, you can use the `poetry add` command and append `@latest` to the package name. For
example, to update the `django` package to the latest version, you would run:

```bash
poetry add django@latest
```

Do this for each package that you want to update to the latest version. Note that this may introduce breaking changes.

## 3. Regenerate the lock file

The lock file (`poetry.lock`) is the file that Poetry uses to keep track of the exact versions of the dependencies that
are installed. After updating the dependencies, you should regenerate the lock file to ensure that it reflects the new
versions. You can do this by running:

```bash
poetry lock
```

## 4. Install the updated dependencies

Finally, you can install the updated dependencies by running:

```bash
poetry install
```