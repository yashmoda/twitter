from django.db import models

# Create your models here.
class TweetData(models.Model):
    created_at = models.DateTimeField()
    tweet_text = models.TextField()
    user_name = models.CharField(max_length=256)
    user_screen_name = models.CharField(max_length=256)
    retweet_count = models.IntegerField()
    favorite_count = models.IntegerField()
    created = models.DateTimeField(auto_now_add=True, auto_now=False)
    modified = models.DateTimeField(auto_now=True, auto_now_add=False)

    def __unicode__(self):
        return str(self.tweet_text)


class KeysData(models.Model):
    key = models.CharField(max_length=256)
    value = models.TextField()
