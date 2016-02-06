"""
    This is a script used to get a slew of keywords from microsoft
"""



from bs4 import BeautifulSoup as bSoup
import requests
import re
import string

punctuation = string.punctuation

ROOT_DOMAIN = 'http://academic.research.microsoft.com'

NEXT_PAGE_ID = 'ctl00_MainContent_bottomPageNext'

MAX_NEXT     = 10

def getKeywordsFromPage(soup):
    kw = []
    # find the tbody
    tbody = soup.find('tbody')

    # all keywords are links
    map(lambda a: kw.append(a.text.strip()), tbody.find_all('a'))

    return kw

def getNextPage(soup):
    """ returns soup for next page, returns None if not found"""
    link_for_next_page = soup.find(id = 'ctl00_MainContent_bottomPageNext')

    if not link_for_next_page:
        return None

    #response = requests.get(ROOT_DOMAIN+link_for_next_page.get('href'))
    #new_soup = bSoup(response.content)
    return link_for_next_page.get('href')

def getContent(page_url):
    """ gets and returns content for page_url """
    return requests.get(page_url).content

def getTopicPages():
    """ returns a list of links to pages that contain the keywords """
    links = []
    response = getContent(ROOT_DOMAIN)
    main_soup = bSoup(response)

    side_bar = main_soup.find(class_='domain-list-nav')
    list_of_links = side_bar.find('ul')

    
    map(lambda a: links.append(a.get('href')), list_of_links.find_all('a'))

    return links

def getGetMoreLink(topic_main_url):
    """ from the topic page, get the see more link"""
    response = getContent(ROOT_DOMAIN+topic_main_url) 
    topic_main_soup = bSoup(response)

    see_more_link = topic_main_soup.find(class_='seemore')
    
    assert see_more_link != None

    ## entity types differ between different links
    link = see_more_link.find('a').get('href')
    link = re.sub(r'entitytype=\d+', 'entitytype=8', link)
    return  link

def getTopicName(soup):
    topic = soup.find(id = 'ctl00_MainContent_lblTopObjects').text.strip()
    topic = re.sub(r'[^ A-Za-z]', "", topic)
    return "_".join(re.sub(r'Top keywords in', "", topic).split())


def main():

    topic_links = getTopicPages()

    keyword_page_links = map(lambda url: getGetMoreLink(url), topic_links)

    for kw_page in keyword_page_links:
        content = getContent(ROOT_DOMAIN+kw_page)
        current_page_soup = bSoup(content)

        current_topic = getTopicName(current_page_soup)
        kw = []
        kw.extend(getKeywordsFromPage(current_page_soup))
        next_link = getNextPage(current_page_soup)


        # put a safety control on for testing
        i = 0
        while next_link and i < MAX_NEXT:
            content = getContent(ROOT_DOMAIN+next_link)
            current_page_soup = bSoup(content)
            kw.extend(getKeywordsFromPage(current_page_soup))
            next_link = getNextPage(current_page_soup)
            i += 1

    
        with open('{}_keywords.txt'.format(current_topic), 'w') as fp:
            map(lambda w: fp.write(w+'\n'), kw)

    return
            
        
if __name__ == '__main__':
    main() 