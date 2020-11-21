from bs4 import BeautifulSoup
from urllib import request,response
import requests
from selenium import webdriver
import pandas as pd
import time
tt = time.strftime('%Y-%m-%d', time.localtime(time.time()))


driver_path = "/users/sanghyeok/desktop/chromedriver"
url = "https://kr.investing.com/portfolio/?portfolioID=Y2c1YG4%2FYj5iNjw1YjI0Pg%3D%3D"
headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36'}

driver = webdriver.Chrome(driver_path)
driver.get(url)
time.sleep(0.3)

username = 'slsnsi@naver.com'
password = 'tkD282538*'


### 로그인 -> 내 포트폴리오 -> 가격이 가장 많이 내려간 순서대로 나열 ###
time.sleep(1.5)
driver.find_element_by_xpath('//*[@id="loginFormUser_email"]').send_keys(username)
driver.find_element_by_xpath('//*[@id="loginForm_password"]').send_keys(password)
driver.find_element_by_xpath('//*[@id="signup"]/a').click()
time.sleep(1.5)
driver.find_element_by_xpath('//*[@id="navMenu"]/ul/li[10]/a').click()
time.sleep(1.5)
driver.find_element_by_xpath('//*[@id="portfolioData_16702538"]/div/table/thead/tr/th[16]').click()
time.sleep(1.5)


###포트폴리오 속 주식들의 이름(NAME), 페이지링크(HREF), 고유 pair-id값(PAIRID) 수집###
pp_stocks = driver.find_elements_by_xpath('//*[@id]/td[3]/span[1]/a')
NAME = []
HREF = []
PAIRID = []

NAME = []; CLOSE = []; PE95 = []; CHG = []; CHG_RATIO = []; OPEN = []; JJ_L_H = []

for i in range(len(pp_stocks)):
    href = pp_stocks[i].get_attribute('href')
    pairid = pp_stocks[i].get_attribute('data-pairid')
    HREF.append(href)
    PAIRID.append(pairid)


for i in range(len(pp_stocks)):
    name = driver.find_element_by_xpath('//*[@id="sort_{}"]/td[4]/a'.format(PAIRID[i]))
    n = name.get_attribute('text')
    NAME.append(n)

#print(HREF)
#print(PAIRID)
#print(NAME)

def get_text_append(k, j):
    k = k.get_text().strip()
    j.append(k)

### 수집한 href를 따라 들어가서, 고유 pair-id값을 통해 원하는 정보들 수집 ###

for i in range(len(pp_stocks)):
    request_url = requests.get(HREF[i], headers = headers)
    soup = BeautifulSoup(request_url.content, 'html.parser')
    print('{}의 정보를 파싱중입니다...'.format(NAME[i]))

#오픈
    opening_price = soup.select_one('div:nth-child(4) > span.float_lang_base_2.bold')
    get_text_append(opening_price, OPEN)

#종가
    closing_price = soup.select_one('div:nth-child(1) > span.float_lang_base_2.bold')
    get_text_append(closing_price, CLOSE)

#per*eps*0.95
    try:
        per = soup.select_one('div:nth-child(11) > span.float_lang_base_2.bold')
        eps = soup.select_one('div:nth-child(6) > span.float_lang_base_2.bold')
        per = per.get_text().strip(); eps = eps.get_text().strip()
        p_e_95 = round(float(per) * float(eps) * 0.95, 2)
        PE95.append(p_e_95)
    except:
        PE95.append('N/A')

#변동
    try:
        fluctuation = soup.select_one('span.arial_20.redFont.pid-{}-pc'.format(PAIRID[i]))
        get_text_append(fluctuation, CHG)
    except:
        fluctuation = soup.select_one('span.arial_20.greenFont.pid-{}-pc'.format(PAIRID[i]))
        get_text_append(fluctuation, CHG)

#변동(%)
    try:
        fluctuation_ratio = soup.select_one('span.arial_20.redFont.pid-{}-pcp.parentheses'.format(PAIRID[i]))
        get_text_append(fluctuation_ratio, CHG_RATIO)
    except:
        fluctuation_ratio = soup.select_one('span.arial_20.greenFont.pid-{}-pcp.parentheses'.format(PAIRID[i]))
        get_text_append(fluctuation_ratio, CHG_RATIO)
        
#장중 변동(최저가 - 최고가)
    L_to_H = soup.select_one('div:nth-child(2) > span.float_lang_base_2.bold')
    get_text_append(L_to_H, JJ_L_H)






### pandas 데이터프레임 만들기 ###
df = pd.DataFrame({"NAME" : NAME, \
                    "OPEN" : OPEN, \
                    "CLOSE" : CLOSE, \
                    "P*E*(.95)" : PE95, \
                    "Chg." : CHG, \
                    "Chg. %" : CHG_RATIO, \
                    "Low - High" : JJ_L_H})                   
print(df)



### 만든 데이터프레임 csv파일로 저장하고, 크롬창 닫기 ###
df.to_csv('/users/sanghyeok/desktop/Investing.csv', mode = 'w', encoding = 'cp949')
driver.close()



### 만들어진 csv파일을 메일로 전송하기 ###
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders


### 메일 세션생성 & 로그인 ###
s = smtplib.SMTP('smtp.gmail.com', 587)
s.starttls()
s.login('slsnsi1212@gmail.com', 'ijesmhehsdnopohk')


### 제목 & 본문 작성 ###
msg = MIMEMultipart()
msg['Subject'] = '제목입니다'
msg.attach(MIMEText('본문입니다\nhttps://kr.investing.com/news/forex-news/article-523621', 'plain'))


### 파일 첨부 ###
attachment = open('/Users/sanghyeok/Desktop/Investing.csv', 'rb')
part = MIMEBase('application', 'octet-stream')
part.set_payload((attachment).read())
encoders.encode_base64(part)
part.add_header('Content-Disposition', "attachment; filename= " + '{}report.csv'.format(tt))
msg.attach(part)


### 메일 전송 ###
s.sendmail("slsnsi1212@gmail.com", "slsnsi1212@gmail.com", msg.as_string())
s.quit()