import os

import pickle
import pprint

from fp.fp import FreeProxy
from datetime import datetime
from scholarly import scholarly

class ScholarlyWrapper:

    def __init__(self):
        
        self._set_new_proxy()
        self._load_cache()

    def _set_new_proxy(self):
        while True:
            proxy = FreeProxy(rand=True, timeout=1).get()
            proxy_works = scholarly.use_proxy(http=proxy, https=proxy)
            if proxy_works:
                break
        print("Working proxy:", proxy)
        return proxy  
    
    def _save_cache(self):
        with open("cache.pkl", "wb") as fp:
            pickle.dump(self._cache, fp)

    def _load_cache(self):
        # cache all author details and serialize them to a flat file
        # helps to recompute related publications count without having to re-crawl
        self._cache = {}
        if os.path.exists("cache.pkl"):
            with open("cache.pkl", "rb") as fp:
                self._cache = pickle.load(fp)
  

    def _search_author_by_name(self, name):
        authors = []
        while True:
            try:
                authors = [a for a in scholarly.search_author(name)]
                #print("Retrieved authors")
                return authors
            except Exception as e:
                print("trying new proxy")
                self._set_new_proxy() 

    def _fill_author(self, author):
        if author.id not in self._cache:
            while True:
                try:
                    author = author.fill([])
                    total_publications = len(author.publications)
                    for pub_idx, publication in enumerate(author.publications):
                        print("\tcrawling publication", str(pub_idx+1)+"/"+str(total_publications), "\n")
                        publication = self._fill_publication(publication)
                        
                    self._cache[author.id] = author
                    self._save_cache()
                    return author
                except Exception as e:
                    print("trying new proxy")
                    self._set_new_proxy()
        else:
            author = self._cache[author.id]
            return author

    def _fill_publication(self, publication):
        while True:
            try:
                publication.fill()
                return publication
            except Exception as e:
                print("\ttrying new proxy")
                self._set_new_proxy()
    
    def get_authour_details(self, query):

        authors = self._search_author_by_name(query)

        filled_authors = []
        for author_idx, author in enumerate(authors):
            print("\ncrawling author", str(author_idx+1)+"/"+str(len(authors)))
            author = self._fill_author(author)
            filled_authors.append(author)
            
        return filled_authors

    def print_author_details(self, authors):
        for author in authors:
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
            
            print("")
            print(author.name, ",", author.affiliation, "(", author.id,")")
            print("h-index:", str(author.hindex))
            print("Total citations:", str(author.citedby))
            print("Interests:", author.interests)
            print("Total publication count", str(total_conference_count))
            print("Related conference publication count", str(related_conference_count))
            print("")

if __name__ == "__main__":
    
    wrapper = ScholarlyWrapper()
    
    start = datetime.now()
    query = "Mausam Indian Institute of Technology Delhi"

    authors = wrapper.get_authour_details(query)
    wrapper.print_author_details(authors)

    end = datetime.now()
    difference = (end - start).seconds
    print("Total time taken:", difference, "seconds")
    
    