import os

import pickle
import pprint

from fp.fp import FreeProxy
from datetime import datetime
from scholarly import scholarly

if __name__ == "__main__":
    
    proxy = FreeProxy(rand=True, timeout=1, country_id=['US', 'CA']).get()  
    scholarly.use_proxy(http=proxy, https=proxy)

    # cache all author details and serialize them to a flat file
    # helps to recompute related publications count without having to re-crawl
    cache = {}
    if os.path.exists("cache.pkl"):
        with open("cache.pkl", "rb") as fp:
            cache = pickle.load(fp)
    
    start = datetime.now()
    #query = "Dinesh Raghu IBM"
    query = "Mausam Indian Institute of Technology Delhi"

    authors = [a for a in scholarly.search_author(query)]
    for author_idx, author in enumerate(authors):
        print("crawling author", str(author_idx+1)+"/"+str(len(authors)))
        if author.id not in cache:
            author = author.fill([])
            publications = {}
            total_publications = len(author.publications)
            for pub_idx, publication in enumerate(author.publications):
                print("\tcrawling publication", str(pub_idx+1)+"/"+str(total_publications))
                publication.fill()
            cache[author.id] = author
        else:
            author = cache[author.id]
    
    # print author basic details and list of conferences published
    print(author.name, author.affiliation, "(", author.id,")")
    for idx, publication in enumerate(author.publications):
        if 'conference' in publication.bib:
            print("\t",publication.bib['conference'])

    end = datetime.now()
    difference = (end - start).seconds
    print("Total time taken:", difference, "seconds")
    
    with open("cache.pkl", "wb") as fp:
        pickle.dump(cache, fp)