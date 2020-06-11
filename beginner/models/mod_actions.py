import beginner.models as models


class ModAction(models.Model):
    action_type = models.CharField(32)
    user_id = models.BigIntegerField()
    mod_id = models.BigIntegerField()
    details = models.CharField(max_length=2048)
    datetime = models.DateTimeField()
