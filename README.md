# Django Assert Model Queries

This project seeks to assist asserting the number of queries per model
during testing.

**Note:** This does so by monkey-patching the ``SQLCompiler`` classes. It's
not something that should be relied upon in production.

## Installation

  ```shell
  pip install django-assert-model-queries
  ```

## Usage

There are integrations for both pytest and Django / `unittest`. Both of
which use the context manager,
``django_assert_model_queries.AssertModelQueriesContext`` under the
hood.

The basic usage is to define a dictionary of expected queries to be
evaluated at the end of the context manager's scope. If the counts
differ, a helpful error message will be rendered indicating what the
differences were and what *all* the queries were during the context.

```python
from django_assert_model_queries import AssertModelQueriesContext
from testapp.models import Community

with AssertModelQueriesContext({"testapp.Community": 2}):
    Community.objects.create(name="test")
    Community.objects.update(name="test")
```

When an unexpected query runs, this ``AssertModelQueriesContext`` will
tell you which model generated an unexpected query.


### Example

Here is an example of what you can expect from the tool:

```pycon
In [1]: from django_assert_model_queries import AssertModelQueriesContext
   ...: from django.contrib.auth.models import User
   ...: with AssertModelQueriesContext({}):
   ...:     User.objects.first()
   ...:
---------------------------------------------------------------------------
AssertionError                            Traceback (most recent call last)
Cell In[1], line 3
      1 from django_assert_model_queries import AssertModelQueriesContext
      2 from django.contrib.auth.models import User
----> 3 with AssertModelQueriesContext({}):
      4     User.objects.only("id").first()

File ~/site-packages/django_assert_model_queries/test.py:145, in AssertModelQueriesContext.__exit__(self, exc_type, exc_value, traceback)
    142 if exc_type is not None:
    143     return
--> 145 self.handle_assertion(actual, expected)
    146 self.expected_model_counts = None

File ~/site-packages/django_assert_model_queries/test.py:172, in AssertModelQueriesContext.handle_assertion(self, actual, expected)
    170         pytest.fail(self.failure_message(actual, expected))
    171 else:
--> 172     assert actual == expected, self.failure_message(actual, expected)

AssertionError: {'auth.User': 1} != {}
- {'auth.User': 1}
+ {}

All queries:
SELECT "auth_user"."id" FROM "auth_user" ORDER BY "auth_user"."id" ASC LIMIT 1
```

### pytest

If you use pytest, you can use the fixture ``assert_model_queries`` as a short-cut.

```python
# pytest example

import pytest
from testapp.models import Community


class TestPytestIntegration:
    @pytest.mark.django_db
    def test_assert_model_queries(self, assert_model_queries):
        with assert_model_queries({"testapp.Community": 1}):
            Community.objects.create(name="test")

        with assert_model_queries({
          "testapp.Community": 2,
          "testapp.Chapter": 1,
          "testapp.Community_topics": 1,
        }):
            Community.objects.all().delete()
```

### unittest

If you test with Django's ``TestCase``, inherit from the mixin
``ModelNumQueriesHelper`` to be able to utilize the
``self.assertModelQueries`` assertion method.

```python
# Django TestCase example

from django.test import TestCase
from django_assert_model_queries import AssertModelQueriesContext, ModelNumQueriesHelper
from testapp.models import Community

class TestDjangoIntegration(ModelNumQueriesHelper, TestCase):
    def test_assert_model_num_queries_context(self):
        with AssertModelQueriesContext({"testapp.Community": 1}):
            Community.objects.create(name="test")
        with AssertModelQueriesContext({"testapp.Community": 2, "testapp.Chapter": 1, "testapp.Community_topics": 1}):
            Community.objects.all().delete()

class TestDjangoHelperIntegration(ModelNumQueriesHelper, TestCase):
    def test_helper(self):
        with self.assertModelQueries({"testapp.Community": 1}):
            Community.objects.create(name="test")
        with self.assertModelQueries({"testapp.Community": 2, "testapp.Chapter": 1, "testapp.Community_topics": 1}):
            Community.objects.all().delete()
```

### Complex usages

There are a few parameters that may help in certain scenarios.

- ``ignore``: A collection of models that should be ignored. For example,
  maybe you want to ignore ``Session`` queries if you're using a database
  backed session.
- ``strict=False``: You can limit the count evaluation to just the models
  specified in the ``expect_model_counts`` collection. Be warned, this can
  hide N+1 issues.

To use these, you must specify them when instantiating
``AssertModelQueriesContext``.

```python
from django_assert_model_queries import AssertModelQueriesContext
from django.contrib.sessions.models import Session

assert_context = AssertModelQueriesContext(ignore={Session})
with assert_context({"testapp.Community": 1}):
    do_something()


assert_context = AssertModelQueriesContext(strict=False)
with assert_context({"testapp.Community": 1}):
    do_something()
```
