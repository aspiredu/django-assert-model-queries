from django.db import models


class Community(models.Model):
    name = models.CharField(max_length=255)
    topics = models.ManyToManyField("Topic", related_name="communities")


class Chapter(models.Model):
    community = models.ForeignKey(
        Community, on_delete=models.CASCADE, related_name="chapters"
    )
    name = models.CharField(max_length=255)


class Topic(models.Model):
    name = models.CharField(max_length=255)
