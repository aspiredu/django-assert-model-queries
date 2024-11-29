# Django Assert Model Queries

This project seeks to assist asserting the number of queries per model
during testing.

**Note:** This does so by monkey-patching the ``SQLCompiler`` classes. It's
not something that should be relied upon in production.

## Getting Started

1. Install the package

  ```shell
  python -m venv venv
  source venv/bin/activate
  pip install django-assert-model-queries
  ```

2. Use in your tests:

  ```python
  # pytest example

  import pytest
  from testapp.models import Community


  class TestPytestIntegration:
      @pytest.mark.django_db
      def test_assert_model_queries(self, assert_model_queries):
          with assert_model_queries({"testapp.Community": 1}):
              Community.objects.create(name="test")
          with assert_model_queries({"testapp.Community": 2, "testapp.Chapter": 1, "testapp.Community_topics": 1}):
              Community.objects.all().delete()
  ```

  ```python
  # Django TestCase example

  from django.test import TestCase
  from django_assert_model_queries import AssertModelNumQueriesContext, ModelNumQueriesHelper
  from testapp.models import Community

  class TestDjangoIntegration(ModelNumQueriesHelper, TestCase):
      def test_assert_model_num_queries_context(self):
          with AssertModelNumQueriesContext({"testapp.Community": 1}):
              Community.objects.create(name="test")
          with AssertModelNumQueriesContext({"testapp.Community": 2, "testapp.Chapter": 1, "testapp.Community_topics": 1}):
              Community.objects.all().delete()

  class TestDjangoHelperIntegration(ModelNumQueriesHelper, TestCase):
      def test_helper(self):
          with self.assertModelNumQueries({"testapp.Community": 1}):
              Community.objects.create(name="test")
          with self.assertModelNumQueries({"testapp.Community": 2, "testapp.Chapter": 1, "testapp.Community_topics": 1}):
              Community.objects.all().delete()
  ```

## TODO:

- Write tests and docs for ignore
- Write tests and docs for non-strict eval
