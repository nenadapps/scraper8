import datetime
from random import randint, shuffle
from time import sleep
from urllib.request import Request, urlopen
from bs4 import BeautifulSoup

def get_html(url):
    html_content = ''
    try:
        req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        html_page = urlopen(req).read()
        html_content = BeautifulSoup(html_page, "html.parser")
    except:
        pass

    return html_content

def get_details(url, country_name):

    stamp = {}

    try:
        html = get_html(url)
    except:
        return stamp

    try:
        price = html.select('#productPrices')[0].get_text()
        price = price.replace(",", "")
        stamp['price'] = price.replace('£', '').strip() 
    except:
        stamp['price'] = None

    try:
        name = html.select("#productName")[0].get_text()
        stamp['name'] = name
    except:
        stamp['name'] = None

    try:
        sku = html.select('#productDetailsList li')[0].get_text()
        stamp['sku'] = sku.replace('Stock Code:', '').strip() 
    except:
        stamp['sku'] = None

    try:
        raw_text = html.find_all("div", {"id":"productDescription"})[0].get_text().strip()
        stamp['raw_text'] = raw_text
    except:
        stamp['raw_text'] = None
        
    try:
        sold_out = html.find_all("img", {"alt":"Sold Out"})
        if sold_out:
            stamp['sold_out'] = '1'
        else:
            stamp['sold_out'] = '0'
    except:
        stamp['sold_out'] = None    

    stamp['currency'] = "GBP"
    
    stamp['country'] = country_name

    # image_urls should be a list
    images = []
    try:
        image_items = html.select('#productMainImage img')
        for image_item in image_items:
            img = 'http://kayatana.com/' + image_item.get('src')
            images.append(img)
    except:
        pass

    stamp['image_urls'] = images

    # scrape date in format YYYY-MM-DD
    scrape_date = datetime.date.today().strftime('%Y-%m-%d')
    stamp['scrape_date'] = scrape_date

    stamp['url'] = url
    print(stamp)
    print('+++++++++++++')
    sleep(randint(25, 65))
    return stamp

def get_page_items(url):

    items = []
    next_url = ''
    country_name = ''

    try:
        html = get_html(url)
    except:
        return items, next_url, country_name

    try:
        country_name = html.select("#navBreadCrumb a")[1].get_text().strip()
    except:
        pass

    try:
        for item in html.select('.itemTitle a'):
            item = item.get('href').replace('&amp;', '&')
            item_parts = item.split('&zenid=')
            item_href = item_parts[0]
            items.append(item_href)
    except:
        pass

    try:
        next_url = html.find_all('a', attrs={'title': ' Next Page '})[0].get('href')
        next_url = next_url.replace('&amp;', '&')
    except:
        pass

    shuffle(items)

    return items, next_url, country_name

def get_countries(url, class_name):
    
    items = []

    try:
        country_html = get_html(url)
    except:
        return items

    try:
        for item in country_html.select('.' + class_name):
            item_link = item.get('href')
            items.append(item_link)
    except:
        pass

    return items

# start url
start_url = 'http://kayatana.com'

# loop through all countries
countries = get_countries(start_url, 'category-top')
for country in countries:
    countries2 = get_countries(country, 'category-products')
    for country2 in countries2:
        while(country2):
            page_items, country2, country_name = get_page_items(country2)
            # loop through all items on current page
            for page_item in page_items:
                stamp = get_details(page_item, country_name)

