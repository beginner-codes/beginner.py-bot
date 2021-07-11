import beginner.models as models


class ContestantInfo(models.Model):
    original_author_id = models.BigIntegerField()
    bot_message_id = models.BigIntegerField()
