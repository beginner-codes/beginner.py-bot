import beginner.models as models


class Points(models.Model):
    awarded = models.DateTimeField(formats="%Y-%m-%d %H:%M")
    user_id = models.BigIntegerField()
    giver_id = models.BigIntegerField(null=True)
    message_id = models.BigIntegerField(null=True)
    points = models.IntegerField()
