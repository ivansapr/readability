import requests
import os
import json
import re
from bs4 import BeautifulSoup
import bs4

import textwrap
 

class Parse:

    def __init__(self, url, config=os.path.dirname(os.path.abspath(__file__))+'/config.json'):
        
        self.line_width = 80
        self.url = url
        self.domain = re.match(r'(?:http[s]?:\/\/)?([\w\d-]+\.[\w\d-]+)',url).group(1)
        self.alowed_tags = ['p', 'a', 'b', 'i','ul','li', 'span']
        
        self.default =  {"title_search": {
                                "name": "h"
                            },

                            "body_search": {
                                "name": "p"
                            },
                            "line_width": 80
                        }
        with open(config, 'r') as f:
            self.config = json.load(f)  
            
        self.get_post()
            
    def __repr__(self):
        return '<Page {}>'.format(self.url)

    def get_post(self):

        url = self.url     
        page = requests.get(url)
        if page.status_code != 200:  
            raise Exception('Страница не загружается')
            
        soup = BeautifulSoup(page.content, 'html.parser')        
        
        search_pattern = [d for d in self.config['sites'] if d['site'] == self.domain]
        if search_pattern:
            title_search_pattern = search_pattern[0]['search_pattern']['title_search']
            body_search_pattern = search_pattern[0]['search_pattern']['body_search']
            
            title = self.find_title(soup, **title_search_pattern)
            body = self.find_body(soup, **body_search_pattern)
 
        else:
            title, body = self.search_text(soup)
        self.save_post([{'tag':'h','line':title}]+body)
 
    
    def find_body(self, soup, **kwargs):
        raw = soup.find(**kwargs)    
        if raw:
            return self.format_post(raw)   

    def find_title(self, soup, **kwargs):
        title = ''
        text = soup.find(**kwargs)
        if text:
            title = re.sub(r'\s',' ',text.get_text(strip=True))
        return title
 
    #ищет блоки текст по стандартному паттерну
    def search_text(self, soup):
        
        containers = []
        headlines = []
        #Цикл собирает родителей у тегов 
        for p in soup.find_all(**self.default['body_search']):
            try:
                if len(p.get_text(strip=True)) > 100:
                    if p.parent not in containers:
                        containers.append(p.parent)
            except Exception as e:
                print(e)

#       Ищем блоки H1-H6, которые ближе всего к контейнерам
        for container in containers:
            search = True
            post = container
            while search:
                if post is not None:
                    headers = post.find_all_previous(re.compile(r'^h[12]$'))
                    if headers:
                        for header in headers:
                            if len(header.get_text(strip=True).split()) > 2:
                                 
                                    search = False
                                    headlines.append(header.get_text(strip=True))
                    post = post.parent
                else:
                    headlines.append('')
                    search = False
        #Если текста в блоке больше по медиане то вероятней всего это статья, а не другие блоки
        body = [p for idx, p in enumerate(containers) 
                            if len(p.get_text(strip=True)) > 120 and headlines[idx]]
        
        
        a = []
        for b in body:
            a += self.format_post(b)
            
        return max(headlines,key=len), a
 
    #Сохраняет линии в файл
    def save_post(self, lines, filename=None):
        if filename is None:
            filename = os.getcwd()+'\\'+self.url_to_filename(self.url)
            directory, file = os.path.split(filename)
            os.makedirs(directory,exist_ok=True)
            
        with open(filename, 'w', encoding='utf-8') as file:
#            print('s:'+str(lines))
            for line in lines:
                if line['tag'] == 'p':
                    file.write(textwrap.fill(line['line'],width=self.default['line_width']))    
                    file.write("\n\n")   
                if line['tag'] == 'h':
                    file.write(textwrap.fill(line['line'],width=self.default['line_width']))    
                    file.write("\n\n")   
                if line['tag'] == 'li':
                    file.write(textwrap.fill(line['line'],width=self.default['line_width']))    
                    file.write("\n")   
                if line['tag'] == 'blackquote':
                    file.write(textwrap.fill(line['line'],width=self.default['line_width']))    
                    file.write("\n\n")   
     
        
        print('Новость сохранена в {}'.format(filename))
        
    #преобразует URL в путь к файлу
    def url_to_filename(self, url,extension='txt'):
        r = re.compile(r'https?:\/\/(?:www\.)?([\w\d\-]*\.\w*(?:\/[\w\d\-]+)*([\d\w]*))')
        return str(re.match(r, url)[1]).replace('/','\\')+'.'+extension


#    форматирует текст для записи в файл
    def format_post(self, body):
        lines = []
        for tag in body.children:
            if tag.name in self.alowed_tags:
                for a in tag.select('a'):
                    s = '{} [{}]'.format(a.get_text(strip=True), a['href'])
#                    s = ' LINK!!! '
                    a.replace_with(s)
#                print(tag)  
                line = tag.get_text().replace('\xa0', ' ')
                line = ' '.join(line.split())
                if tag.name == 'p':     
                    lines += [{'tag':'p',
                               'line':line}]
                    continue
                if tag.name == 'ul':
                    for li in tag.find_all('li'):
                        line = '- '+li.get_text(strip=True)+'\n'
                        lines += [{'tag':'li',
                               'line':line}]
                    continue
                if re.match(r'^h\d$',tag.name):
                    lines += [{'tag':'h',
                               'line':line}]
                    continue
                if tag.name == 'blockquote':
                    lines += [{'tag':'blockquote',
                               'line':line}]
                    continue
        return lines
 
            
#    проверяет допустим ли тег для записи
    def tag_allowed(self, element): 
        if element.name in self:
            return True
        if isinstance(element, bs4.element.Comment):
            return False
        return True 
 
