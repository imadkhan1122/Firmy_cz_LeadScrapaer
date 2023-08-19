# =============================================================================
#                           import Packages
# =============================================================================
# Parsing an HTML File
from bs4 import BeautifulSoup
from tqdm import tqdm
import csv, os
from unidecode import unidecode

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import re,time


# =============================================================================
#               Parent Class That Return HTML page content
# =============================================================================
class GET_CONTENT(object):
    # class constructor
    def __init__(self, url):
        self.url = url
        
    # page content generator
    def content(self):
        url = self.url
        
        # send request and put dalay in case max retries
        session = requests.Session()
        retry = Retry(connect=3, backoff_factor=0.5)
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        
        r = session.get(url)
        # check request status
        while r.status_code != 200:
            r = requests.get(url)
        # return content
        return BeautifulSoup(r.content, 'html.parser')

# =============================================================================
#                   Child Class For Geting Required Data
# =============================================================================
class GET_ALL(GET_CONTENT):
    def __init__(self):
        # main website url
        self.url = 'https://www.firmy.cz/detail/2180997-firmy-cz-praha-smichov.html'
        # output path if not exist create first
        self.outPth = 'Results/'
        if not os.path.exists(self.outPth):
            os.mkdir(self.outPth)
        self.main()
    
    # Iterating through services and extract categories urls
    def GET_CATS(self, URL):
        # call parent class
        Cat_Cont = GET_CONTENT(URL).content()
        
        # locating service on main page
        MainCats = Cat_Cont.find('ul', class_='list').find_all('li')
        
        SERVICES = []
        print('[INFO] Collecting Services Urls....')
        for cat in MainCats:
            H3 = cat.find('h3')
            if H3 != None:
                # append all services to SERVICES variable
                SERVICES.append((H3.text, H3.find('a')['href']))
        
        
        # iterate over services and extract categories
        ALL_CATS = []
        print('[INFO] Collecting Each Service Categories Urls.... ')
        for service in SERVICES:
            SubCat_Cont = GET_CONTENT(service[1]).content()
            # locating categories
            SubCat = SubCat_Cont.find('div', class_='categories').find_all('a')
            # iterate over categories
            for subcat in SubCat:
                dic = {'CATEGORY':service[0], 'SUB CATEGORY':subcat.text, 'SubCatURL':subcat['href']}
                # append all categories to ALL_CATS variable
                ALL_CATS.append(dic)
        
        print('Extracted All Services all Categories Urls.')
 
        return ALL_CATS
      
    # Extract companies per category
    def GET_COM_LINKS(self, dic):
        COMPANIES = []
        
        print('\n','Extracting companies Links from Category......')
        
        # extract given category page content
        page = GET_CONTENT(dic['SubCatURL']).content()
        # list all companies on first page
        premiseList = page.find('div', class_='premiseList')
        premises = premiseList.find_all('div')
        for premise in premises:
            try:
                if premises[0]['data-dot'] == 'premise':
                    h3 = premise.find('h3').find('a')
                    # append companies links and related data to variable
                    COMPANIES.append({'CATEGORY':dic['CATEGORY'], 'SUB CATEGORY':dic['SUB CATEGORY'], 
                                      'comp_url': h3['href']})
            except:
                pass
        
        # paginating untill last page for given category
        _str = ''
        n = 2
        while _str == '':
            # time.sleep(5)
            str_ = dic['SubCatURL']
            row = str_.split('?', 1)
            url = row[0]+f'?page={n}&'+row[-1]
            page = GET_CONTENT(url).content()
            try:
                _str = page.find('div', class_='premisesNotFound').text
                page = []
            except:
                n+=1
            
            if page != []:
                premiseList = page.find('div', class_='premiseList')
                premises = premiseList.find_all('div')
                
                for premise in premises:
                    try:
                        if premises[0]['data-dot'] == 'premise':
                            h3 = premise.find('h3').find('a')     
                            COMPANIES.append({'CATEGORY':dic['CATEGORY'], 'SUB CATEGORY':dic['SUB CATEGORY'], 
                                              'comp_url': h3['href']})
                    except:
                        pass
                    
        return COMPANIES
    
    # Extract required data from each company
    def GET_COMP_DATA(self, dic):
        DATA = {}
        page = GET_CONTENT(dic['comp_url']).content()
        name, email, add, phone, web = [""]*5
        
        try:
            name = page.find('h1', class_='detailPrimaryTitle').text
            name = name.strip()
        except:
            pass
        
        try:
            add = page.find('div', class_='detailAddress').text
            add = add.strip()
        except:
            pass
        
        try:
            web = page.find('a', class_='value detailWebUrl url companyUrl').text
            web = web.strip()
        except:
            pass
        
        try:
            phone = page.find('div', class_='value detailPhone detailPhonePrimary').text
            phone = phone.strip()
        except:
            pass
        
        try:
            email = page.find('div', class_='value detailEmail').text
            email = email.strip()
        except:
            reg_pat = r'\S+@\S+\.\S+'
            emails = re.findall(reg_pat ,page.text,re.IGNORECASE) 
            if emails != []:
                email = emails[0]
        finally:
            pass
        
       
        DATA = {'E-mail':email, 'Company':name, 'Category':dic['SUB CATEGORY'], 
                'Sevice':dic['CATEGORY'], 'Location':add, 'Phone':phone, 'Website':web}
        
        return DATA
        
    # hard encoding list of data
    def encoding(self, lst):
        encoded_l = [e.encode() for e in lst]
        decoded_l = [unidecode(e.decode('utf-8')) for e in encoded_l]
    
        return decoded_l
    
    # main function call all other functions and create csv
    def main(self):
        
        CATS_DIC = self.GET_CATS(self.url)
        
        header = ['E-mail', 'Company', 'Category', 'Sevice', 'Location', 'Phone', 'Website']
        out_pth = self.outPth+"/"+'CompaniesData2.csv'
        with open(out_pth, 'w', encoding='UTF-8', newline = '') as output:
            # initialize rows writer
            csv_writer = csv.writer(output)
            # write headers to the file
            csv_writer.writerow(header)
            for dic in tqdm(CATS_DIC):
                Companies = self.GET_COM_LINKS(dic)
                print('Collectiong Companies data....')
                for dic in tqdm(Companies):
                    # time.sleep(.5)
                    lst = list(self.GET_COMP_DATA(dic).values())
                    if lst != []:
                        csv_writer.writerow(self.encoding(lst))
        
        return
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
