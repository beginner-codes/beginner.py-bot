import beginner.models as models


class Settings(models.Model):
    name = models.CharField(max_length=256)
    value = models.CharField(max_length=2048)
