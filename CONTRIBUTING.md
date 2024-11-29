# Contributing

## Running the tests

This project requires that a MySQL/Maria database be running.
The test suite assumes the password will be `djAssertModelQueries3`.

```shell
docker run --detach --name mariadb -e MYSQL_ROOT_PASSWORD=djAssertModelQueries3 --publish 3306:3306 mariadb:11.4
```

1. Install [uv](https://github.com/astral-sh/uv)
2. Create a virtualenv
  ```shell
  uv venv
  source .venv/bin/activate
  ```
3. Install [tox](https://tox.wiki/en/latest/)
  ```shell
  uv pip install tox
  ```
4. Run the tests
  ```shell
  tox -f py313 # If you want to run tests for a specific version of python
  tox # If you want to run all tests
  ```

## Updating dependencies

To update the test dependencies, there's a helper compile script.

```shell
cd tests/requirements
uv run python -m compile
cd ..
git add tests/requirements/*
git commit
```
