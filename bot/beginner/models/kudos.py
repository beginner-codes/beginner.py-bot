import beginner.models as models


class Kudos(models.Model):
    given = models.DateTimeField(formats="%Y-%m-%d %H:%M")
    user_id = models.BigIntegerField()
    giver_id = models.BigIntegerField()
    message_id = models.BigIntegerField()
    kudos = models.IntegerField()
