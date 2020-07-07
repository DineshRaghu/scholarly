import os

import pickle
import pprint

from datetime import datetime
from scholarly import scholarly

if __name__ == "__main__":
    
    cache = {}
    if os.path.exists("cache.pkl"):
        with open("cache.pkl", "rb") as fp:
            cache = pickle.load(fp)
    
    start = datetime.now()
    query = 'Dinesh Raghu IBM'
    authors = [a for a in scholarly.search_author(query)]
    for author in authors:
        if author.id not in cache:
            author = author.fill([])
            publications = {}
            for idx, publication in enumerate(author.publications):
                publication.fill()
                print(publication)
            cache[author.id] = author
        else:
            author = cache[author.id]
        pprint.pprint(author)
    end = datetime.now()
    difference = (end - start).seconds
    print("Total time taken:", difference, "seconds")
    
    with open("cache.pkl", "wb") as fp:
        pickle.dump(cache, fp)