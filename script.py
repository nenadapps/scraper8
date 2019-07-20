from fake_useragent import UserAgent
import datetime
from random import randint, shuffle
from time import sleep
from urllib.request import Request, urlopen
import bs4
import requests
import sqlite3
import os
import shutil
from stem import Signal
from stem.control import Controller
import socket
import socks

controller = Controller.from_port(port=9051)
controller.authenticate()

UA = UserAgent(fallback='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36')
hdr = {'User-Agent': "'"+UA.random+"'",
       'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
       'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
       'Accept-Encoding': 'none',
       'Accept-Language': 'en-US,en;q=0.8'}

def connectTor():
    socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS5 , "127.0.0.1", 9150)
    socket.socket = socks.socksocket

def renew_tor():
    controller.signal(Signal.NEWNYM)

def showmyip():
    url = "http://www.showmyip.gr/"
    r = requests.Session()
    page = r.get(url)
    soup = bs4.BeautifulSoup(page.content, "lxml")
    try:
        ip_address = soup.find("span",{"class":"ip_address"}).text.strip()
        print(ip_address)
    except:
        print('Issue with printing IP')

def get_html(url):
    html_content = ''
    try:
        req = Request(url, headers=hdr)
        html_page = urlopen(req).read()
        html_content = bs4.BeautifulSoup(html_page, "html.parser")
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
        stamp['title'] = name
    except:
        stamp['title'] = None

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
            stamp['sold'] = 1
            stamp['number'] = 0
        else:
            stamp['sold'] = 0
            stamp['number']=None
    except:
        stamp['sold'] = None    

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
    
    try:
	    temp = stamp['title'].split(' ')
	    stamp['year'] = temp[1]
	    stamp['face_value'] = temp[2]
	    stamp['SG'] = temp[-1].replace('.','').replace('SG','')
    except:
        stamp['year']=None
        stamp['face_value']=None
        stamp['SG']=None

    # scrape date in format YYYY-MM-DD
    scrape_date = datetime.date.today().strftime('%Y-%m-%d')
    stamp['scrape_date'] = scrape_date
    
    # STUFF that detects if sold is on page
    # IF SOLD ON PAGE
    #   stamp['sold'] = 1
    #   stamp['number']=0
    # ELSE:
    #   stamp['sold']=None
    #   stamp['number']=None
    
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

def file_names(stamp):
    file_name = []
    rand_string = "RAND_"+str(randint(0,100000))
    file_name = [rand_string+"-" + str(i) + ".png" for i in range(len(stamp['image_urls']))]
    return(file_name)

def query_for_previous(stamp):
    # CHECKING IF Stamp IN DB
    os.chdir("/Volumes/stamps_copy/")
    conn1 = sqlite3.connect('Reference_data.db')
    c = conn1.cursor()
    col_nm = 'url'
    col_nm2 = 'raw_text'
    unique = stamp['url']
    unique2 = stamp['raw_text']
    c.execute('SELECT * FROM kayatana WHERE "{col_nm}" LIKE "{unique}%" AND "{col_nm2}" LIKE "{unique2}%"')
    all_rows = c.fetchall()
    conn1.close()
    price_update=[]
    price_update.append((stamp['url'],
    stamp['raw_text'],
    stamp['scrape_date'], 
    stamp['price'], 
    stamp['currency'],
    stamp['sold'],
    stamp['number']))
    
    if len(all_rows) > 0:
        print ("This is in the database already")
        conn1 = sqlite3.connect('Reference_data.db')
        c = conn1.cursor()
        c.executemany("""INSERT INTO price_list (url, raw_text, scrape_date, price, currency, sold, number) VALUES(?,?,?,?,?,?,?)""", price_update)
        conn1.commit()
        conn1.close()
        print (" ")
        #url_count(count)
        sleep(randint(10,25))
        pass
    else:
        os.chdir("/Volumes/stamps_copy/")
        conn2 = sqlite3.connect('Reference_data.db')
        c2 = conn2.cursor()
        c2.executemany("""INSERT INTO price_list (url, raw_text, scrape_date, price, currency, sold, number) VALUES(?,?,?,?,?,?,?)""", price_update)
        conn2.commit()
        conn2.close()
    print("Price Updated")
    
def db_update_image_download(stamp):  
    req = requests.Session()
    directory = "/Volumes/stamps_copy/stamps/kayatana/" + str(datetime.datetime.today().strftime('%Y-%m-%d')) +"/"
    image_paths = []
    f_names = file_names(stamp)
    image_paths = [directory + f_names[i] for i in range(len(f_names))]
    print("image paths", image_paths)
    if not os.path.exists(directory):
        os.makedirs(directory)
    os.chdir(directory)
    for item in range(0,len(f_names)):
        print (stamp['image_urls'][item])
        try:
            imgRequest1=req.get(stamp['image_urls'][item],headers=hdr, timeout=60, stream=True)
        except:
            print ("waiting...")
            sleep(randint(3000,6000))
            print ("...")
            imgRequest1=req.get(stamp['image_urls'][item], headers=hdr, timeout=60, stream=True)
        if imgRequest1.status_code==200:
            with open(f_names[item],'wb') as localFile:
                imgRequest1.raw.decode_content = True
                shutil.copyfileobj(imgRequest1.raw, localFile)
                sleep(randint(18,30))
    stamp['image_paths']=", ".join(image_paths)
    #url_count += len(image_paths)
    database_update =[]

    # PUTTING NEW STAMPS IN DB
    database_update.append((
        stamp['url'],
        stamp['raw_text'],
        stamp['title'],
        stamp['sku'],
        stamp['SG'],
        stamp['country'],
        stamp['year'],
        stamp['face_value'],
        stamp['scrape_date'],
        stamp['image_paths']))
    os.chdir("/Volumes/stamps_copy/")
    conn = sqlite3.connect('Reference_data.db')
    conn.text_factory = str
    cur = conn.cursor()
    cur.executemany("""INSERT INTO kayatana ('url','raw_text', 'title','sku','SG', 'country', 'year', 'face_value', 
    'scrape_date','image_paths') VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", database_update)
    conn.commit()
    conn.close()
    print ("all updated")
    print ("++++++++++++")
    print (" ")
    sleep(randint(45,115))

# start url
start_url = 'http://kayatana.com'

connectTor()
showmyip()
req = requests.Session()

# loop through all countries
count = 0
countries = get_countries(start_url, 'category-top')
for country in countries:
	count += 1
	countries2 = get_countries(country, 'category-products')
	for country2 in countries2:
		while(country2):
			count += 1
			page_items, country2, country_name = get_page_items(country2)
			# loop through all items on current page
			for page_item in page_items:
				count += 1
				if count > randint(75,156):
					sleep(randint(500,2000))
					connectTor()
					showmyip()
					count = 0
				else:
					pass
				stamp = get_details(page_item, country_name)
				query_for_previous(stamp)
				db_update_image_download(stamp)