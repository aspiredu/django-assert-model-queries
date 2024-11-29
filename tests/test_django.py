from django.db.models import Count
from django.test import TestCase

from django_assert_model_queries.test import (
    AssertModelNumQueriesContext,
    ModelNumQueriesHelper,
)
from .testapp.models import Community


class TestDjangoIntegration(ModelNumQueriesHelper, TestCase):
    def test_assert_model_num_queries_context(self):
        with AssertModelNumQueriesContext({"testapp.Community": 1}):
            Community.objects.create(name="test")
        with AssertModelNumQueriesContext({"testapp.Community": 1}):
            Community.objects.update(name="new")
        with AssertModelNumQueriesContext({"testapp.Community": 1}):
            Community.objects.get(name="new")
        with AssertModelNumQueriesContext({"testapp.Community": 1}):
            Community.objects.aggregate(count=Count("id"))
        with AssertModelNumQueriesContext(
            {
                "testapp.Community": 2,
                "testapp.Chapter": 1,
                "testapp.Community_topics": 1,
            }
        ):
            Community.objects.all().delete()

    def test_helper(self):
        with self.assertModelNumQueries({"testapp.Community": 1}):
            Community.objects.create(name="test")
        with self.assertModelNumQueries({"testapp.Community": 1}):
            Community.objects.update(name="new")
        with self.assertModelNumQueries({"testapp.Community": 1}):
            Community.objects.get(name="new")
        with self.assertModelNumQueries({"testapp.Community": 1}):
            Community.objects.aggregate(count=Count("id"))
        with self.assertModelNumQueries(
            {
                "testapp.Community": 2,
                "testapp.Chapter": 1,
                "testapp.Community_topics": 1,
            }
        ):
            Community.objects.all().delete()
