import os
import csv
import copy
import pprint
import pickle

from lxml import etree as ElementTree

# for other other conference aliases, please refer to "areadict" variable in line 70 of the script below
# https://github.com/emeryberger/CSrankings/blob/gh-pages/util/csrankings.py
conf_to_aliases = {
    'aaai': ['AAAI', 'AAAI/IAAI'],
    'ijcai': ['IJCAI']
}

confdict = {}
for conf, aliases in conf_to_aliases.items():
    for alias in aliases:
        confdict[alias] = conf

name_to_id = {}
author_info_map = {}
interested_authors = set([])

def parseAuthors():

    
    global name_to_id
    global author_info_map
    global interested_authors

    count = 0

    if not os.path.exists('dblp.xml') or not os.path.exists('dblp.dtd'):
        print("\nPlease download the latest file from download dblp.xml and dblp.dtd file from https://dblp.uni-trier.de/xml/\n")
        exit(0)
    
    print("Parsing authors...")

    with open('dblp.xml', mode='rb') as f:
    
        for (event, node) in ElementTree.iterparse(f, events=['start', 'end'],load_dtd=True):
            
            count += 1
            if count%10000000 == 0:
                print("\tparsed " + str(count) + " nodes")
                
            if node.tag == "www":
                attributes = node.attrib
                key = None
                author_aliases = []
                affiliations = []
                urls = []
                if 'key' in attributes:
                    key = attributes['key']
                for child in node:
                    child_attributes = child.attrib
                    if "type" in child_attributes and child_attributes["type"] == "affiliation":
                        affiliations.append(child.text)
                    if(child.tag == "author"):
                        author_aliases.append(child.text)
                    if(child.tag == "url"):
                        urls.append(child.text)
                

                if key !=None and key.startswith("homepages/"):
                    
                    author_info = {}
                    key = key.replace("homepages/", "")
                    author_info['key'] = key
                    
                    author_info['aliases'] = []
                    for alias in author_aliases:
                        if alias == "" or alias == None:
                            continue
                        encoded_alias = alias.encode("utf-8")
                        author_info['aliases'].append(encoded_alias)
                        name_to_id[encoded_alias] = author_info['key']
                        
                    author_info['affiliation'] = []
                    for affiliation in affiliations:
                        if affiliation == "" or affiliation == None:
                            continue
                        author_info['affiliation'].append(affiliation.encode("utf-8"))
                    
                    author_info['urls'] = []
                    for url in urls:
                        author_info['urls'].append(url)

                    author_info_map[key] = copy.deepcopy(author_info)
            
            if (node.tag == 'inproceedings' or node.tag == 'article'):
                attributes = node.attrib
                key =  attributes['key']
                
                confname = None
                authors = []
                for child in node:
                    if child.tag == 'booktitle':
                        confname = child.text
                    if child.tag == 'journal':
                        confname = child.text
                    if child.tag == "author":
                        authors.append(child.text)
                    
                if  confname != None and confname in confdict:
                    for author in authors:
                        interested_authors.add(author.encode("utf-8"))

def parsePubs():
    
    print("Parsing publications...")
    
    global name_to_id
    global author_info_map
    global interested_authors
    
    author_pub_map = {}

    count = 0

    with open('dblp.xml', mode='rb') as f:
    
        for (event, node) in ElementTree.iterparse(f, events=['start', 'end'],load_dtd=True):

            count += 1
            if count%10000000 == 0:
                print("\tparsed " + str(count) + " nodes")

            if (node.tag == 'inproceedings' or node.tag == 'article'):
                attributes = node.attrib
                key =  attributes['key']
                
                confname = None
                authors = []
                for child in node:
                    if child.tag == 'booktitle':
                        confname = child.text
                    if child.tag == 'journal':
                        confname = child.text
                    if child.tag == "author":
                        if child.text != "" and child.text != None:
                            encoded_author = child.text.encode("utf-8")
                            authors.append(encoded_author)
                    if child.tag == "year":
                        year = child.text
                
                for author in authors:
                    if author in interested_authors:
                        author_dblp_id = name_to_id[author]
                        if author_dblp_id not in author_pub_map:
                            author_pub_map[author_dblp_id] = {}
                            author_pub_map[author_dblp_id]['pubs'] = set([])
                            author_pub_map[author_dblp_id]['list'] = []
                        if key not in author_pub_map[author_dblp_id]['pubs']:
                            author_pub_map[author_dblp_id]['pubs'].add(key)
                            author_pub_map[author_dblp_id]['list'].append((confname, year))

    print("Serializing parsed data")
    # dump to pickle file
    with open('objs.pkl', 'wb') as f:
        pickle.dump([author_info_map, author_pub_map], f)

def write_data_as_csv():

    with open('objs.pkl', 'rb') as f:
        print('Loading pkl file')
        author_info_map, author_pub_map = pickle.load(f)
        
    print('Populating fields')
    data_to_write = []
    for author_dblp_id, pub_info in author_pub_map.items():

        data_row = []

        author_info = author_info_map[author_dblp_id]
        longest_name = longest_string = max(author_info['aliases'], key=len)

        data_row.append(longest_name)
        data_row.append(author_dblp_id)
        
        total = 0
        related = 0

        total_10 = 0
        related_10 = 0
        
        for (confname, year) in pub_info['list']:
            # skip arXiv articles
            if confname == "CoRR":
                continue
            if confname in confdict:
                related += 1
            total += 1

            # only papers in the last ten years
            if year != None and year != "":
                if 2020-int(year) <= 10:
                    total_10 += 1
                    if confname in confdict:
                        related_10 += 1
        
        data_row.append(str(related_10))
        data_row.append(str(total_10))

        data_row.append(str(related))
        data_row.append(str(total))
        
        data_row.append(str(author_info['affiliation']))
        data_row.append(str(author_info['urls']))
        
        data_to_write.append(copy.deepcopy(data_row))
    
    print('Sorting data')
    data_to_write = sorted(data_to_write, key = lambda x: int(x[2]), reverse=True)

    print('Writing to file')
    header = ["name","dblp-id","related_pub_count_last_10_years", "total_pub_count_last_10_years", "related_pub_count","total_pub_count", "affiliations", "urls"]
    with open('author-details.csv','w') as f:
        mywriter = csv.writer(f)
        mywriter.writerow(header)
        for data_row in data_to_write:
            mywriter.writerow(data_row)
        
if __name__ == "__main__":

    # this module, computes the statistics of interested authors and prints it to a csv file
    # interested authors are those who have published atleast one paper in either aaai OR ijcai
    # to add more related conferences, add them to "conf_to_aliases" map above

    # obj.pkl store a list of all interested authors and their publications
    # if the condition for interested authors is changed in conf_to_aliases, 
    # please detele the obj.pkl, and run the script
    
    if not os.path.isfile('objs.pkl'):
        parseAuthors()
        parsePubs()

    write_data_as_csv()

