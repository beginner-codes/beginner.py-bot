import beginner.models as models


class Option(models.Model):
    name = models.CharField(64)
    value = models.CharField(1024, default="")
