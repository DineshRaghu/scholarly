import os

import pickle
import pprint

from fp.fp import FreeProxy
from datetime import datetime
from scholarly import scholarly

def set_new_proxy():
    while True:
        proxy = FreeProxy(rand=True, timeout=1).get()
        proxy_works = scholarly.use_proxy(http=proxy, https=proxy)
        if proxy_works:
            break
    print("Working proxy:", proxy)
    return proxy    

set_new_proxy()

if __name__ == "__main__":
    
    # cache all author details and serialize them to a flat file
    # helps to recompute related publications count without having to re-crawl
    cache = {}
    if os.path.exists("cache.pkl"):
        with open("cache.pkl", "rb") as fp:
            cache = pickle.load(fp)
    
    start = datetime.now()
    query = "Mausam Indian Institute of Technology Delhi"

    authors = []
    while True:
        try:
            authors = [a for a in scholarly.search_author(query)]
            #print("Retrieved authors")
            break
        except Exception as e:
            print("trying new proxy")
            set_new_proxy() 

    
    for author_idx, author in enumerate(authors):
        print("\ncrawling author", str(author_idx+1)+"/"+str(len(authors)))
        if author.id not in cache:
            while True:
                try:
                    author = author.fill([])
                    #print("filled author details")
                    break
                except Exception as e:
                    print("trying new proxy")
                    set_new_proxy()
            
            publications = {}
            total_publications = len(author.publications)
            for pub_idx, publication in enumerate(author.publications):
                print("\tcrawling publication", str(pub_idx+1)+"/"+str(total_publications), "\n")
                while True:
                    try:
                        publication.fill()
                        #print("\tFilled publication details\n")
                        break
                    except Exception as e:
                        print("\ttrying new proxy")
                        set_new_proxy()
            cache[author.id] = author
        else:
            author = cache[author.id]

    total_conference_count = 0
    related_conference_count = 0
    # print author basic details and list of conferences published
    for idx, publication in enumerate(author.publications):
        if 'conference' in publication.bib and 'arXiv' not in publication.bib['conference']:
            total_conference_count += 1
            conference = publication.bib['conference']
            if "International Joint Conference on Artificial Intelligence" in conference or "AAAI Conference on Artificial Intelligence" in conference:
                related_conference_count += 1
            #print("\t",publication.bib['conference'])
    
    print(author.name, ",", author.affiliation, "(", author.id,")")
    print("h-index:", str(author.hindex))
    print("Total citations:", str(author.citedby))
    print("Interests:", author.interests)
    print("Total publication count", str(total_conference_count))
    print("Related conference publication count", str(related_conference_count))

    end = datetime.now()
    difference = (end - start).seconds
    print("Total time taken:", difference, "seconds")
    
    with open("cache.pkl", "wb") as fp:
        pickle.dump(cache, fp)