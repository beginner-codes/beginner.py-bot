import beginner.models as models
import pickle


class OnlineSample(models.Model):
    taken = models.DateTimeField(formats="%Y-%m-%d %H:%M")
    sample_type = models.CharField()  # MINUTE, 10MINUTE, HOUR, DAY, WEEK
    max_seen = models.IntegerField()
    min_seen = models.IntegerField(null=True)
