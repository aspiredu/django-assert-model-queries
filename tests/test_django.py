from django.db.models import Count
from django.test import TestCase

from django_assert_model_queries.test import (
    AssertModelQueriesContext,
    ModelNumQueriesHelper,
)
from .testapp.models import Community


class TestDjangoIntegration(ModelNumQueriesHelper, TestCase):
    def test_assert_model_num_queries_context(self):
        with AssertModelQueriesContext({"testapp.Community": 1}):
            Community.objects.create(name="test")
        with AssertModelQueriesContext({"testapp.Community": 1}):
            Community.objects.update(name="new")
        with AssertModelQueriesContext({"testapp.Community": 1}):
            Community.objects.get(name="new")
        with AssertModelQueriesContext({"testapp.Community": 1}):
            Community.objects.aggregate(count=Count("id"))
        with AssertModelQueriesContext(
            {
                "testapp.Community": 2,
                "testapp.Chapter": 1,
                "testapp.Community_topics": 1,
            }
        ):
            Community.objects.all().delete()


class TestDjangoTestCaseHelper(ModelNumQueriesHelper, TestCase):
    databases = {"default", "mysql"}

    def test_helper(self):
        manager = Community.objects
        for db in ["default", "mysql"]:
            with self.subTest(db=db):
                with self.assertModelQueries({"testapp.Community": 1}, using=db):
                    manager.using(db).create(name="test")
                with self.assertModelQueries({"testapp.Community": 1}, using=db):
                    manager.using(db).update(name="new")
                with self.assertModelQueries({"testapp.Community": 1}, using=db):
                    manager.using(db).get(name="new")
                with self.assertModelQueries({"testapp.Community": 1}, using=db):
                    manager.using(db).aggregate(count=Count("id"))
                with self.assertModelQueries(
                    {
                        "testapp.Community": 2,
                        "testapp.Chapter": 1,
                        "testapp.Community_topics": 1,
                    },
                    using=db,
                ):
                    manager.using(db).all().delete()
