from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils.text import slugify
from unidecode import unidecode

from .models import Subject, Dictionary


@receiver(pre_save, sender=Subject)
@receiver(pre_save, sender=Dictionary)
def populate_slug(sender, instance, update_fields, **kwargs):
    if not update_fields or 'title' in update_fields:
        instance.slug = slugify(unidecode(instance.title))
