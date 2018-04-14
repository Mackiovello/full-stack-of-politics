import requests
import polyglot
from polyglot.mapping import Embedding
import requests, tweepy, re
import time

#Define categories
CATEGORIES = [["bostäder", "bostad", "byggande", "bygger"], ["polis", "försvar", "brott", "kriminalitet"], ["sjukvård", "hälsa", "sjukhus", "välfärd", "välfärden"]]
CATEGORY_NAMES = ["Bostäder", "Polisen", "Sjukvården"]


def categorize_tweets(currentTwitterAccount, n_max_tweets = 5):
	from polyglot.downloader import downloader
	downloader.download("embeddings2.sv")

	subscription_key = "7387424f11ab4ec7b08b31f4a4f7f823"
	api_url = "https://westcentralus.api.cognitive.microsoft.com/text/analytics/v2.0/"
	key_phrase_api_url = api_url + "keyPhrases"
	language_api_url = api_url + "languages"

	embeddings = Embedding.load("/home/oliver/polyglot_data/embeddings2/sv/embeddings_pkl.tar.bz2")

	consumer_key = "0D1k9X4rvKeNjJMU6AjyOYfv2"
	consumer_secret = "L2sPX4appghs9F4afaT1ISNyHxWgGJAXSoEumzJOQS6IjvltCF"
	access_token = "434339373-8DKIoTsy5K2OfH8DYdvofQUtAILjZ6ZFQWj4DwJc"
	access_token_secret = "MbNois2Rfcmtv2EvHb31jjIqm5cHV5oUZQHA5pRJrw6MX"

	auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
	auth.set_access_token(access_token, access_token_secret)

	api = tweepy.API(auth)



	#Fetch swedish tweets

	def language_check(string):
	    headers   = {"Ocp-Apim-Subscription-Key": subscription_key}
	    response  = requests.post(language_api_url, headers=headers, json={"documents":[{"id":1, "text":string}]})
	    if response.ok:
	        print(response.json())
	        return response.json()["documents"][0]["detectedLanguages"][0]["iso6391Name"]
	    else:
	        if response.status_code == 429:
	            time.sleep(1)
	            return language_check(string)
	        response.raise_for_status()
	        
	documents={"documents":[]}
	tweets_raw = [] 
	i = 0
	for tweet in tweepy.Cursor(api.user_timeline, id=currentTwitterAccount,tweet_mode="extended").items(n_max_tweets):
	    #removing the http link at the end of the text
	    result = re.sub(r"http\S+", "",tweet.full_text)
	    if language_check(result) == "sv":
	        documents['documents'].append({'id':i,'language':'sv','text':result})
	        tweets_raw.append(result)
	        i+=1



	### Extract key words

	headers   = {"Ocp-Apim-Subscription-Key": subscription_key}
	response  = requests.post(key_phrase_api_url, headers=headers, json=documents)
	key_phrases = response.json()


	# Parse key words
	key_words = [[y for y in x.values()][0] for x in key_phrases["documents"]]
	key_words = [[y.split(" ") for y in x] for x in key_words]
	key_words = [[y.strip() for sublist in l for y in sublist] for l in key_words]
	print(key_words)


	### Determine closest category for the sets of key words

	def embedding_distances(word, category): #Adapter to handle missing words for embedding model
	    try:
	        return embeddings.distances(word, category)
	    except:
	        return [1e16] #If word is not present, return big integer..
	    
	def topic(word): #Determine category score for word
	    topic_list = [embedding_distances(word.lower(), category) for category in CATEGORIES] #compute distances to categories
	    topic_list = [min(l) for l in topic_list] #compute average of each sublist
	    min_value = min(topic_list)
	    return topic_list.index(min_value), min_value
	topic_dists = [[topic(word) for word in l] for l in key_words]

	def cluster_topics(topic_dist):
	    topic_dict = {}
	    for t in topic_dist:
	        if t[0] in topic_dict:
	            topic_dict[t[0]] = (min(topic_dict[t[0]][0], t[1]), topic_dict[t[0]][1]+1)
	        else:
	            topic_dict[t[0]] = (t[1], 1)
	    topics = [(key, value[0]) for key,value in topic_dict.items()]
	    values = [x[1] for x in topics]
	    return topics[values.index(min(values))]


	categorized_tweets = [(tweets_raw[i], CATEGORY_NAMES[cluster_topics(topic_dists[i])[0]]) for i in range(len(topic_dists))]
	print(categorized_tweets)
	return categorized_tweets

if __name__ == '__main__':
	currentTwitterAccount = "shekarabi"
	categorize_tweets(currentTwitterAccount)


