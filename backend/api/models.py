from django.db import models
from django.utils.crypto import get_random_string
from django.urls import reverse


class ShortLink(models.Model):
    recipe = models.OneToOneField(
        'recipes.Recipe', on_delete=models.CASCADE, related_name='shortlink'
    )
    key = models.CharField(max_length=8, unique=True, editable=False)

    def save(self, *args, **kwargs):
        if not self.key:
            self.key = get_random_string(8)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('redirect_short_link', args=[self.key])
