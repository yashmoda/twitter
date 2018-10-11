from django.contrib import admin


# Register your models here.
from stream_tweet.models import TweetData, KeysData


class TweetDataAdmin(admin.ModelAdmin):
    search_fields = ['retweet_count', 'tweet_text', 'favorite_count', 'user_name', 'user_screen_name']
    list_display = ['favorite_count', 'tweet_text', 'user_name', 'user_screen_name', 'retweet_count']


admin.site.register(TweetData, TweetDataAdmin)


class KeysDataAdmin(admin.ModelAdmin):
    search_fields = ['key', 'value']
    list_display = ['key', 'value']


admin.site.register(KeysData, KeysDataAdmin)