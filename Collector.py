from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

from bs4 import BeautifulSoup
import json
import time
import os


def timeChecker(year,date,time):
    def treatZero(word):
        if int(word) < 10 and str(word)[0] != '0' :
            return '0' + str(word) 
        else:
            return str(word)
    months = ['jan','feb','mar','apr','may','jun','jul','aug','sep','oct','nov','dec']
    months_dict = {}  
    for i in range(len(months)):
        months_dict[months[i]] = i+1
    month = treatZero(months_dict[date.split(' ')[0].lower()])
    day = treatZero(date.split(' ')[1])
    date = year+'-'+month+'-'+day
    time = time.split(' ')
    is_afternoon = time[1]
    hours , minutes = time[0].split(':')
    if is_afternoon == 'pm' and str(hours) != '12':
        hours = int(hours) + 12
    time = treatZero(str(hours))+':'+treatZero(minutes)+':00'
    return date+' '+time
def filteringforAirport(target):
    filterWords = {'Paris Orly' : 'ORY', 'Paris Charles de Gaulle' : 'CDG'}
    if(target in filterWords.keys()):
        return filterWords[target]
    else:
        return target
def oneWayflightsparser(data,src,dst,datetime):

    soup = BeautifulSoup(data,'html.parser')
    results= soup.find_all('div','resultWrapper')
    export_data= {}
    idx = 0 
    relatedflights= 1
    for i in range(len(results)):
        content_cards = results[i].find_all('div','content-card')
        price = results[i].find_all('span','price-text')[0].text.replace('$','')
        currency = 'USD'
        link = 'https://www.kayak.com'+ results[i].find_all('a','booking-link')[0].attrs['href']
        flight = {}
        for card in content_cards:
            segment_row = results[i].find_all('div','segment-row')
            for segment in segment_row:
                # Departure Date
                date = segment.find_all('div','date')[0].text.replace('\n','').split(', ')[1]
                year = datetime[:4]
                #operator 

                planeDetail = segment.find_all('div','planeDetails')[0].text.replace('\n','').split(' · ')
                flightsNumber = planeDetail[0].split(' ')[-1]
                if(flightsNumber == ''):
                    flightsNumber =  planeDetail[0].split(' ')[-2]
                operator = planeDetail[0].replace(flightsNumber,'')
                #Times
                times = segment.find_all('span','time')
                departure_time = times[0].text
                departure_date = timeChecker(year,date,departure_time)
                arrival_time = times[1].text

                arrival_date = segment.find_all('div','arrival-date-warning')
                if len(arrival_date) > 0:
                    arrival_date = arrival_date[0].text.split(', ')[1]
                    
                    arrival_date = (timeChecker(year,arrival_date,arrival_time))

                else:
                    arrival_date = (timeChecker(year,date,arrival_time))
                
                duration = segment.find_all('span','segmentDuration')[0].text.replace('h ',':').replace('m','').replace("\n",'')

                #Airport Information
                airports = segment.find_all('span','city')
                if len(segment.find_all('span','city')[0].text.split('(')) >=2:
                    departure = segment.find_all('span','city')[0].text.split('(')[1].replace(')','')
                    # Hot Uploaded Airport Names for Filetering
                    if(len(departure) > 3):
                        departure = filteringforAirport(departure)
                else: 
                    departure = segment.find_all('span','city')[0].text
                if len(segment.find_all('span','city')[1].text.split('(')) >=2:
                    arrival = segment.find_all('span','city')[1].text.split('(')[1].replace(')','')
                    # Hot Uploaded Airport Names for Filtering
                    if(len(arrival) > 3):
                        arrival = filterWords(arrival)
                else:
                    arrival = segment.find_all('span','city')[1].text
                export_data[idx] = {
                    'operator' : operator,
                    'flightsnumber' : flightsNumber,
                    'departure' : {
                        'airport' : departure,
                        'date' : departure_date
                    },
                    'arrival' : {
                        'airport' : arrival,
                        'date' : arrival_date
                    },
                    'duration' : duration,
                    'price' : price ,
                    "currency" : currency,
                    'link' : link,
                    'relativeflights' : relatedflights
                }
                idx+=1
        relatedflights+=1    
    if(len(export_data) > 0):
        try:
            os.mkdir(os.getcwd() +'/KayakCrwaler/Prices/{datetime}'.format(datetime=datetime))
        except FileExistsError:
            pass
        path = os.getcwd() + '/KayakCrwaler/''/Prices/' + str(datetime)+'/'+'{src}-{dst}-{datetime}.json'.format(src=src,dst=dst,datetime=datetime)
        htmlpath = os.getcwd() + '/KayakCrwaler/html/{src}-{dst}-{datetime}.html'.format(src=src,dst=dst,datetime=datetime)

        ptr = open(path,'w',encoding='utf-8')
        ptr.write(json.dumps(export_data,ensure_ascii=False))
        htmlptr = open(htmlpath,'w',encoding='utf-8')
        htmlptr.write(data)
        return export_data
    else:
        return 404

def Collector(src,dst,datetime):       
        print(src + '-' + dst + '-' + datetime)
        options = webdriver.FirefoxOptions()   
        options.add_argument('-headless')
        options.add_argument("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.125 Safari/537.36")    
        driver = webdriver.Firefox(executable_path = 'KayakCrwaler/geckodriver',firefox_options=options) 
        driver.get('https://www.kayak.com/flights/{src}-{dst}/{datetime}?sort=bestflight_a'.format(src=src,dst=dst,datetime=datetime.replace('_','-')))
        try:
            element = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CLASS_NAME, "resultsPaginator"))) 
            html = driver.page_source
            #html = open('./KayakCrwaler/html/ICN-DOM-2020_08_22.html','r').read()
            return oneWayflightsparser(html,src,dst,datetime)

        finally:
            driver.close()
            driver.quit()
       
## Test Codes
if __name__ == '__main__':
    #from itertools import permutations
    #seq = ['ICN','CJU','BKK','KUL','NRT','PEK','CDG','FRA','LHR','HAN','SFO','LAX','DEL','LIM','BOG']
    departure_datetime = '2020-08-30'
    #return_date = '2020-08-30'
    #seq = permutations(seq,2)
    #idx = 1 
    #for i in seq:
    #    src = i[0]
    #    dst = i[1]
    src = "ICN"
    dst = "NRT"
    Collector(src,dst,departure_datetime)
    #    idx+=1
    #    time.sleep(100*idx % 3
    print('Testcode')
