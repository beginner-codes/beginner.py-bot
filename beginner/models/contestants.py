import beginner.models as models


class ContestantInfo(models.Model):
    original_author_id = models.IntegerField()
    bot_message_id = models.IntegerField()
    
