import beginner.models as models
import pickle


class Scheduler(models.Model):
    ID = models.AutoField(primary_key=True)
    name = models.CharField(max_length=64)
    when = models.DateTimeField(formats="%Y-%m-%d %H:%M")
    tag = models.CharField(max_length=64)  # Used to identify the callback
    payload = models.CharField(max_length=256)
