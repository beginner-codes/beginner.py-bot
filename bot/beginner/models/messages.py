import beginner.models as models
from enum import Enum


class MessageTypes(Enum):
    RULE = "RULE"
    TIP = "TIP"


class Message(models.Model):
    message_type = models.CharField(20)  # RULE, TIP, etc.
    message = models.CharField(max_length=2000)
    title = models.CharField(max_length=200)
    label = models.CharField(max_length=100)
    author = models.CharField(max_length=100)
