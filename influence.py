from twitter import *
import sys
import os
from datetime import datetime, timedelta

appkey = "keyhere"
appsecret = "secrethere"


#From https://github.com/sixohsix/twitter/blob/master/twitter/logger.py
def get_tweets(twitter, screen_name, earliest=None, max_id=None):
    kwargs = dict(count=3200, screen_name=screen_name, include_rts=True, trim_user=True)
    if max_id:
        kwargs['max_id'] = max_id

    n_tweets = 0
    influence = 0
    tweets = twitter.statuses.user_timeline(**kwargs)
    for tweet in tweets:
        tweetdate = datetime.strptime(tweet["created_at"], '%a %b %d %H:%M:%S +0000 %Y')
        if(earliest):
            if(tweetdate < earliest):
                max_id = None
                break
        elif tweet['id'] == max_id:
            continue
        elif("retweeted_status" in tweet):
            influence -= 1
        else:
            influence += tweet["retweet_count"]
        max_id = tweet['id']
        n_tweets += 1
    return n_tweets, influence, max_id

#Authenticate running user
MY_TWITTER_CREDS = os.path.expanduser('~/.influence_credentials')
if not os.path.exists(MY_TWITTER_CREDS):
    oauth_dance("Influence tracker", appkey,
        appsecret, MY_TWITTER_CREDS)

oauth_token, oauth_secret = read_token_file(MY_TWITTER_CREDS)

api = Twitter(auth=OAuth(
    oauth_token, oauth_secret, appkey, appsecret))
search = Twitter(domain="search.twitter.com", auth=OAuth(
    oauth_token, oauth_secret, appkey, appsecret))

screen_name = sys.argv[1]
if(screen_name == 'rate'):
    print api.account.rate_limit_status()
else:
    earliest = datetime.now() - timedelta(6)
    users = api.friends.ids(screen_name=screen_name)
    influencecount = 0
    if(len(sys.argv) > 3):
        influencecount = int(sys.argv[3])
    max_id = None
    found_user = False
    for uid in users['ids']:
        if(len(sys.argv) > 2 and not found_user):
            if(sys.argv[2] == str(uid)):
                found_user = True
            else:
                continue
        userinfluence = 0
        testuser = api.users.show(user_id=uid)
        if(testuser["protected"]):
            continue
        uname = testuser["screen_name"]
        while True:
            try:
                earliest = datetime.now()
                tweets_processed, influence, max_id = get_tweets(api, uname, earliest, max_id)
                userinfluence += influence
                if(tweets_processed == 0 or max_id == None):
                    break
            except TwitterError as e:
                print e
                print "Last UID: " + str(uid)
                print "Last influence: " + str(influencecount)
                quit()
        pagenum = 1
        breakloop = False
        while True:
            try:
                mentions = search.search(q="@" + uname, rpp=100, page=pagenum)['results']
                mentioncount = 0
                for mention in mentions:
                    mentioncount += 1
                    if(datetime.strptime(mention["created_at"], '%a, %d %b %Y %H:%M:%S +0000') < earliest):
                        breakloop = True
                        break
                pagenum += 1
                userinfluence += mentioncount
                if(len(mentions) == 0 or pagenum > 15 or breakloop == True):
                    print userinfluence
                    influencecount += userinfluence
                    break
            except TwitterError as e:
                print e
                print "Last UID: " + str(uid)
                print "Last influence: " + str(influencecount)
                quit()
    print "Total influence: " + str(influencecount)
