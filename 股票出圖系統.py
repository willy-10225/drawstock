import numpy as np
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
import requests
import yfinance as yf
import sqlite3
import matplotlib.pyplot as plt
import tkinter as tk
import tkinter.messagebox
import os
import seaborn as sns
import random

## 爬蟲網上股票代碼
if os.path.isfile('.\stock.db'):
    print('已有股票資料庫')
else:
    api_url='https://tw.stock.yahoo.com/h/kimosel.php?tse=1&cat=%A5b%BE%C9%C5%E9&form=menu&form_id=stock_id&form_name=stock_name&domain=0'
    def stocktitle(api_url):
        data=[]
        for i in range(2):
            form_data={
                'tse': f'{i+1}',
                'cat': '(unable to decode value)',
                'form': 'menu',
                'form_id': 'stock_id',
                'form_name': 'stock_name',
                'domain': '0'
            }
            resp=requests.post(api_url,data=form_data)
            soup=BeautifulSoup(resp.text,'lxml')
            a=soup.find_all('a')
            data.append([i.text.strip() for i in a])
        return data
    data=stocktitle(api_url)     
    data[0].remove('上櫃')
    data[0].remove('詳細說明')
    data[1].remove('上市')
    data[1].remove('詳細說明')
    data
    datas=[]
    
    for i in range(2):
        for stock in data[i]:
            try:
                form_data={
                        'tse': f'{i+1}',
                        'cat': f'{stock}',
                        'form': 'menu',
                        'form_id': 'stock_id',
                        'form_name': 'stock_name',
                        'domain': '0'
                    }
                resp=requests.post(api_url,data=form_data)
                soup=BeautifulSoup(resp.text,'lxml')
            except:
                pass
            [datas.append(a.text.strip()) for a in soup.find_all('a')]
    datas=list(set(datas))
    title=stocktitle(api_url)
    df_stockname=pd.DataFrame([i.split(' ')[:2] for i in datas],columns=['symbol','name'])
    ### 建立股票資料庫
    con=sqlite3.connect('stock.db')
    cur=con.cursor()
    sqlstr='''
    create table if not exists stock(
        symbol varchar(50) PRIMARY KEY,
        name test
    );
    '''
    cur.execute(sqlstr)
    con.commit()
    con=sqlite3.connect('stock.db')
    df_stockname.to_sql('stock',con,if_exists='append',index=False)
    con.close()
    
con=sqlite3.connect('stock.db')
cur = con.cursor()
datas=cur.execute("SELECT * FROM stock")
datas=[data for data in datas]
df_stockname=pd.DataFrame(datas,columns=['symbol','name'])
con.close()

def getSoupWithChrome(url,path='c:/webdriver/chromedriver',hide=False):  
    option=webdriver.ChromeOptions()     
    if hide:        
        option.add_argument('--headless') 

    try:
        chrome=webdriver.Chrome(path,options=option)
        chrome.implicitly_wait(10)
        chrome.get(url)        
    except:
        return 'get webdriver error.'
     
    soup=None
    if chrome!=None:
        soup=BeautifulSoup(chrome.page_source,'lxml')    
        chrome.quit()
    return soup  

### 建立股票成交量前十
def stock_top(number=10):
    soup=getSoupWithChrome('https://tw.stock.yahoo.com/rank/volume/',path='c:/webdriver/chromedriver',hide=True)
    top100_html=[i.text.strip() for i in soup.find(class_="M(0) P(0) List(n)").find_all('div')]
    top100=[]
    for i in range(len(top100_html)):
        if (i%17==6) | (i%17==7):
            top100.append(top100_html[i])
    df_top100=pd.DataFrame(np.array(top100).reshape(int(len(top100)/2),2))
    return df_top100[:number]

symbol=[]
day=''
name=""     


def Radiobutton_event(widget):
    global output
    choice  = radioValue.get()
    if choice:
        output=widget['text']
    return  output

def choose_stock():
    global output,symbol
    a = entry1.get()
    if  len(set(symbol))>3:
        tkinter.messagebox.showerror(title = "錯誤", message = '股票數超過四張') 
    elif a in df_stockname['symbol'].values :
        tkinter.messagebox.showinfo(title = '完成', message = "輸入成功") 
        symbol.append(f'{a}{output}')
        symbol=list(set(symbol))
        var.set(symbol)
    else:
        tkinter.messagebox.showerror(title = "錯誤", message = '資料庫無此號股票') 
        
def Clearstock():
    global symbol,day
    symbol=[]
    var.set(symbol)

def Delstock():
    global symbol
    try:
        symbol.remove(symbol[len(symbol)-1])
        var.set(symbol)
    except:
        tkinter.messagebox.showerror(title = "錯誤", message = '無股票') 
    
def show():
    global symbol,day
    try:
        if entry2.get()=='':
            day='30'
        else:
            day=int(entry2.get())
    except:
        tkinter.messagebox.showerror(title = "錯誤", message = '輸入錯誤') 
    
    if symbol==[]:
        symbol=stock_top()[1]
    for code in symbol:
        draw(code,day)
        plt.show()
        
def draw(code,day):
    global name
    prices = yf.download(
    f'{code}',
    # 1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max
    period = f'{day}d',
    progress=False
    )
    name=df_stockname.loc[df_stockname['symbol']==code.split('.')[0]]['name'].values[0]
    plt.figure(figsize=(24,24))
    plt.subplot(2,1,1)   
    colors = [("#"+''.join([random.choice('0123456789ABCDEF') for i in range(6)]))for j in range(5)]
    for i,j in enumerate(prices.columns[:4]):
        sns.lineplot(x = prices.index, y = prices[f'{j}'], data = prices, color = colors[i])
    plt.legend(labels = prices.columns[:4])
    plt.title(f'{code}',fontsize=16)
    plt.subplot(2,1,2)
    plt.bar(prices.index,prices['Volume'])
    plt.title(f'{code}_Volume',fontsize=16)

def save():
    global path,name,day,symbol
    path=entry3.get()
    if day=='':
        day='30'
    if symbol==[]:
        symbol=stock_top()[1]
    if path=='':
        path='.'
    for code in symbol:
        draw(code,day)
        try:
            os.mkdir(f'{path}\\img')
            plt.savefig(f'{path}\\img\\{name}.jpg')
        except FileExistsError:
            plt.savefig(f'{path}\\img\\{name}.jpg')
        except:
            tkinter.messagebox.showerror(title = "錯誤", message = '地址輸入錯誤') 

window = tk.Tk()
radioValue = tk.IntVar() 
var = tk.StringVar()

window.title('window')
window.geometry('300x300')
# 標示文字
label1 = tk.Label(window, text = '股票號數(最多四張,一次只能輸入一張)')
label2 = tk.Label(window, text = '註:如果空值顯示今日成交量前十股票')
entry1 = tk.Entry(window) # 輸入欄位的寬度
rdioOne =tk.Radiobutton(window, width=8, text='.TWO',variable=radioValue,value=1,command=lambda: Radiobutton_event(rdioOne)) 
rdioTwo =tk.Radiobutton(window, width=8, text='.TW',variable=radioValue,value=2,command=lambda: Radiobutton_event(rdioTwo)) 
label3 = tk.Label(window, textvariable=var, bg='white', fg='black', font=('Arial', 12), width=30,height=2)
button1 = tk.Button(window, width=10, text = "股票儲存", command = choose_stock)
button2 = tk.Button(window, width=10, text = "股票清空", command = Clearstock)
button3 = tk.Button(window, width=10, text = "刪除", command = Delstock)
label4 = tk.Label(window, text = '股票所需日數(天數,預設30天)')
entry2 = tk.Entry(window,width = 15) # 輸入欄位的寬度
button4 = tk.Button(window, text = "出圖", command =show,width =30)
label5 = tk.Label(window, text = '存圖位置')
entry3 = tk.Entry(window)
button5 = tk.Button(window, text = "存圖", command =save,width =30)

label1.pack()
label2.pack()
entry1.pack()
x1=50
rdioOne.place(x=x1+30,y=60)
rdioTwo.place(x=x1+100,y=60)
label3.place(x=15,y=90)
button1.place(x=5,y=140)
button2.place(x=x1+50,y=140)
button3.place(x=x1+150,y=140)
label4.place(x=0,y=170)
entry2.place(x=180,y=170)
button4.place(x=45,y=195)
label5.place(x=5,y=225)
entry3.place(x=65,y=225)
button5.place(x=45,y=250)

window.mainloop()