from django.db import models
from django.db.models.deletion import CASCADE
from django.urls import reverse
from django.conf import settings


class Subject(models.Model):
    title = models.CharField(max_length=30, verbose_name="tytuł")
    slug = models.SlugField()
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=CASCADE,
        related_name="subjects",
        verbose_name="właściciel",
    )

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("dictionary:dict_list", args=[self.slug])

    class Meta:
        ordering = ["slug"]
        verbose_name = "temat"
        verbose_name_plural = "tematy"
        constraints = [
            models.UniqueConstraint(
                name="unique_subject_for_user", fields=["slug", "owner"]
            )
        ]


class Dictionary(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="dicts")
    title = models.CharField(max_length=30, verbose_name="nazwa")
    slug = models.SlugField()
    description = models.CharField(
        max_length=150, verbose_name="opis", null=True, blank=True
    )
    words = models.JSONField(verbose_name="słowa", default=dict)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("dictionary:dict_detail", args=[self.subject.slug, self.slug])

    class Meta:
        ordering = ["slug"]
        verbose_name = "słownik"
        verbose_name_plural = "słowniki"
        constraints = [
            models.UniqueConstraint(
                name="unique_dictionary_for_subject", fields=["slug", "subject"]
            )
        ]
