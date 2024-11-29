from textwrap import dedent
from unittest.mock import patch, Mock

import pytest
from django.db.models import Count

from django_assert_model_queries import AssertModelNumQueriesContext
from django_assert_model_queries.patch import query_counts, reset_query_counter, patch_sql_compilers_for_debugging

from tests.testapp.models import Community


class TestPatching:
    @pytest.fixture
    def patch(self):
        unpatch = patch_sql_compilers_for_debugging()
        reset_query_counter()
        yield
        unpatch()
        reset_query_counter()

    @pytest.mark.django_db
    def test_unpatched_compilers(self):
        Community.objects.create(name="test")
        Community.objects.update(name="new")
        Community.objects.get(name="new")
        Community.objects.aggregate(count=Count("id"))
        Community.objects.all().delete()
        assert query_counts.get() == {}

    @pytest.mark.django_db
    def test_patched_compilers(self, patch):
        Community.objects.create(name="test")
        Community.objects.update(name="new")
        Community.objects.get(name="new")
        Community.objects.aggregate(count=Count("id"))
        assert query_counts.get() == {"testapp.Community": 4}
        Community.objects.all().delete()
        assert query_counts.get() == {"testapp.Community": 6, "testapp.Chapter": 1, "testapp.Community_topics": 1}

class TestAssertModelNumQueriesContext:
    @pytest.fixture
    def assert_context(self):
        context = AssertModelNumQueriesContext(connection=Mock(queries=[{"sql": "SELECT * FROM testapp.community"}]))
        context.initial_queries = 0
        context.final_queries = 1
        return context

    @pytest.mark.django_db
    def test_call_expects_overrides_init(self):
        context = AssertModelNumQueriesContext({"testapp.Community": 0})
        with context({"testapp.Community": 1}):
            assert Community.objects.first() is None
            assert context.expected_model_counts == {"testapp.Community": 1}

    def test_failure_message(self, assert_context):
        assert assert_context.failure_message({"djangonaut.Space": 1}, {"django.Commons": 2}) == dedent(
            """            {'djangonaut.Space': 1} != {'django.Commons': 2}
            - {'djangonaut.Space': 1}
            + {'django.Commons': 2}

            All queries:
            SELECT * FROM testapp.community"""
        )
        assert assert_context.failure_message({"djangonaut.Space": 1}, {}) == dedent(
            """            {'djangonaut.Space': 1} != {}
            - {'djangonaut.Space': 1}
            + {}

            All queries:
            SELECT * FROM testapp.community"""
        )
        assert assert_context.failure_message({}, {"django.Commons": 2}) == dedent(
            """            {} != {'django.Commons': 2}
            - {}
            + {'django.Commons': 2}

            All queries:
            SELECT * FROM testapp.community"""
        )

