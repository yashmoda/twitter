import csv
import json
import traceback
from datetime import datetime

from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from tweepy import Stream
from tweepy import OAuthHandler
from tweepy.streaming import StreamListener

# Create your views here.
from stream_tweet.models import TweetData, KeysData

access_token = KeysData.objects.get(key="access_token").value
secret = KeysData.objects.get(key="access_token_secret").value
api_key = KeysData.objects.get(key="api_key").value
api_secret = KeysData.objects.get(key="api_secret").value


class listener(StreamListener):

    def on_data(self, data):
        data = json.loads(data)
        print(data)
        final_format = "%Y-%m-%dT%H:%M:%S.%fZ"
        initial_format = "%a %b %d %H:%M:%S %z %Y"
        TweetData.objects.create(
            created_at=datetime.strptime(data["created_at"], initial_format).strftime(final_format),
            tweet_text=data["text"],
            user_name=data["user"]["name"], retweet_count=data["retweet_count"],
            user_screen_name=data["user"]["screen_name"], favorite_count=data["favorite_count"])
        return True

    def on_error(self, status):
        print(status)


@csrf_exempt
@require_http_methods(["POST"])
def stream_tweet(request):
    response_json = {}
    try:
        query = request.POST.get('query')
        print(query)
        auth = OAuthHandler(api_key, api_secret)
        auth.set_access_token(access_token, secret)

        twitterStream = Stream(auth, listener())
        twitterStream.filter(track=query)

        response_json['success'] = True

    except Exception as e:
        traceback.print_exc()
        response_json['success'] = str(e)
    return JsonResponse(response_json)


@require_http_methods(["GET"])
def search_data(request):
    response_json = {'tweets': []}
    try:
        search_keyword = request.GET.get('search_keyword', '')
        sort_order = request.GET.get('sort_order', "asc")
        sort_field = request.GET.get('sort_field', 'datetime')  # Either 'datetime' or 'tweet'
        filter_from_date = request.GET.get('filter_from_date', '')
        filter_to_date = request.GET.get('filter_from_date', '')
        filter_tweet_count = request.GET.get('tweet_count', 0)
        filter_tweet_count_type = request.GET.get('tweet_count_type', 'equal')  # 'lt', 'gt', 'equal'
        filter_tweet_text = request.GET.get('tweet_text_keyword',
                                            '')  # filter by text/username (startwith/endswith/contains/exact match)
        filter_tweet_text_type = request.GET.get('tweet_text_type',
                                                 'icontains')  # filter by text/username (startswith/endswith/icontains/exact match)
        page = request.GET.get('page')
        """ Search queryset """
        query_search = Q(tweet_text__icontains=search_keyword) | Q(user_name__icontains=search_keyword)

        """ Filters """
        # ----------- Data range filter ------------
        query_daterange_filter = None
        if filter_from_date is not '' or filter_to_date is not '':
            if filter_from_date is not '':
                filter_from_date = datetime.strptime(str(filter_from_date), '%d-%m-%Y').strftime('%Y-%m-%d')
            if filter_to_date is not '':
                filter_to_date = datetime.strptime(str(filter_to_date), '%d-%m-%Y').strftime('%Y-%m-%d')
            if filter_from_date is not '' and filter_to_date is not '':
                query_daterange_filter = Q(created__at__date__range=[filter_from_date, filter_to_date])
            elif filter_from_date is not '' and filter_to_date == '':
                query_daterange_filter = Q(created_at__date__gte=filter_from_date)
            elif filter_to_date is not '' and filter_from_date == '':
                query_daterange_filter = Q(created_at__date__lte=filter_to_date)

        # ----------- Tweet count filter ------------
        query_tweet_count_filter = None
        if filter_tweet_count != 0 and filter_tweet_count != '':
            if filter_tweet_count_type == "lt":
                query_tweet_count_filter = Q(retweet_count_lt=int(filter_tweet_count))
            elif filter_tweet_count_type == "gt":
                query_tweet_count_filter = Q(retweet_count_gt=int(filter_tweet_count))
            else:
                query_tweet_count_filter = Q(retweet_count=int(filter_tweet_count))

        # ----------- name/tweet text filter ------------
        query_tweet_filter = None
        if filter_tweet_text != "":
            if filter_tweet_text_type == "startswith":
                query_tweet_filter = Q(tweet_text__startswith=filter_tweet_text) | Q(
                    user_name__startswith=filter_tweet_text)
            elif filter_tweet_text_type == "endswith":
                query_tweet_filter = Q(tweet_text__endswith=filter_tweet_text) | Q(
                    user_name__endswith=filter_tweet_text)
            elif filter_tweet_text_type == "icontains":
                query_tweet_filter = Q(tweet_text__icontains=filter_tweet_text) | Q(
                    user_name__icontains=filter_tweet_text)
            else:
                query_tweet_filter = Q(tweet_text=filter_tweet_text) | Q(user_name=filter_tweet_text)

        tweet_list = TweetData.objects.filter(
            query_search | query_daterange_filter | query_tweet_count_filter | query_tweet_filter)

        """ Sorting list """
        if sort_field == "datetime":
            sorting_field = 'created_at'
        else:
            sorting_field = 'tweet_text'

        if sort_order.lower() == "desc":
            sorting_field = '-' + sorting_field
        tweet_list = tweet_list.order_by(sorting_field)
        paginator = Paginator(tweet_list, 10)
        try:
            tweets = paginator.page(page)
        except PageNotAnInteger:
            tweets = paginator.page(1)
        except EmptyPage:
            tweets = paginator.page(paginator.num_pages)
        for obj in tweets:
            temp_json = {'id': obj.id,
                         'created_at': obj.created_at,
                         'tweet_text': obj.tweet_text,
                         'user_name': obj.user_name,
                         'user_screen_name': obj.user_screen_name,
                         'retweet_count': obj.retweet_count,
                         'favorite_count': obj.favorite_count}
            response_json['tweets'].append(temp_json)
        response_json['success'] = True
    except Exception:
        response_json['success'] = False
    return JsonResponse(response_json)


@require_http_methods(["GET"])
def convert_to_csv(request):
    response_json = {}
    try:

        data = str(request.GET.get('data')).replace("#", " ")
        print(data)
        data = json.loads(data)
        f = csv.writer(open("data.csv", "w"))
        f.writerow(["created_at", "tweet_text", "user_name", "user_screen_name", "retweet_count", "favorite_count"])
        for x in data:
            f.writerow([x["created_at"], x["tweet_text"], x["user_name"], x["user_screen_name"],
                        str(x["retweet_count"]), str(x["favorite_count"])])
        response_json['success'] = True
    except Exception:
        traceback.print_exc()
        response_json['success'] = False
    return JsonResponse(response_json)





