import json
import os
import re
import textwrap
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup, element


class Parse:

    CONFIG_PATH = '{}{}'.format(
                        os.path.dirname(os.path.abspath(__file__)),
                        '/config.json')
    LINE_WIDTH = 80

    def __init__(self, url, config=CONFIG_PATH):

        self.url = urlparse(url)
        self.domain = self.url.netloc
        self.alowed_tags = ['p', 'a', 'b', 'i', 'ul', 'li', 'span']

        self.default = {
            "title_search": {
                            "name": "h"
                        },

            "body_search": {
                            "name": "p"
                            }
                        }
        with open(config, 'r') as f:
            self.config = json.load(f)

        self.get_post()

    def __repr__(self):
        return '<Page {}>'.format(self.url.geturl)

    def get_post(self):

        page = requests.get(self.url.geturl())
        if page.status_code != 200:
            raise ValueError('Страница не загружается')

        soup = BeautifulSoup(page.content, 'html.parser')

        search_pattern = [d for d in self.config['sites']
                          if d['site'] == self.domain]
        if search_pattern:
            title_search_pattern = search_pattern[0]['search_pattern']['title_search']
            body_search_pattern = search_pattern[0]['search_pattern']['body_search']

            title = self.find_title(soup, **title_search_pattern)
            body = self.find_body(soup, **body_search_pattern)

        else:
            title, body = self.search_text(soup)
        self.save_post([{'tag': 'h', 'line': title}]+body)

    def find_body(self, soup, **kwargs):
        raw = soup.find(**kwargs)
        if raw:
            return self.format_post(raw)

    def find_title(self, soup, **kwargs):
        title = ''
        text = soup.find(**kwargs)
        if text:
            title = re.sub(r'\s', ' ', text.get_text(strip=True))
        return title

#   ищет блоки текст по стандартному паттерну
    def search_text(self, soup):

        containers = []
        headlines = []
#       Цикл собирает родителей у тегов
        for p in soup.find_all(**self.default['body_search']):
            try:
                if len(p.get_text(strip=True)) > 100:
                    if p.parent not in containers:
                        containers.append(p.parent)
            except ValueError as e:
                print(e)

#       Ищем блоки H1-H6, которые ближе всего к контейнерам
        for container in containers:
            search = True
            post = container
            while search:
                if post is not None:
                    headers = post.find_all_previous(re.compile(r'^h[12]$'))
                    for header in headers:
                        if len(header.get_text(strip=True).split()) > 2:

                                search = False
                                headlines.append(header.get_text(strip=True))
                    post = post.parent
                else:
                    headlines.append('')
                    search = False
#       Если текста в блоке больше по медиане то вероятней всего это статья,
#          а не другие блоки
        body = [p for idx, p in enumerate(containers)
                if len(p.get_text(strip=True)) > 120 and headlines[idx]]

        a = []
        for b in body:
            a += self.format_post(b)

        return max(headlines, key=len), a

#   Сохраняет линии в файл
    def save_post(self, lines, filename=None):
        if filename is None:
            filename = '{}\\{}'.format(os.getcwd(),
                                       self.url_to_filename(self.url)
                                       )
            directory, file = os.path.split(filename)
            os.makedirs(directory, exist_ok=True)

        with open(filename, 'w', encoding='utf-8') as file:
            for line in lines:
                if line['tag'] == 'p':
                    file.write(textwrap.fill(
                        line['line'], width=self.LINE_WIDTH))
                    file.write("\n\n")
                if line['tag'] == 'h':
                    file.write(textwrap.fill(
                        line['line'], width=self.LINE_WIDTH))
                    file.write("\n\n")
                if line['tag'] == 'li':
                    file.write(textwrap.fill(
                        line['line'], width=self.LINE_WIDTH))
                    file.write("\n")
                if line['tag'] == 'blackquote':
                    file.write(textwrap.fill(
                        line['line'], width=self.LINE_WIDTH))
                    file.write("\n\n")

        print('Новость сохранена в {}'.format(filename))

#   преобразует URL в путь к файлу
    def url_to_filename(self, url, extension='txt'):
        # path = urlparse(url)
        return '{}{}.{}'.format(
                                url.netloc,
                                url.path,
                                extension
                            ).replace('/', '\\')


#    форматирует текст для записи в файл

    def format_post(self, body):
        lines = []
        for tag in body.children:
            if tag.name in self.alowed_tags:
                for a in tag.select('a'):
                    s = '{} [{}]'.format(a.get_text(strip=True), a['href'])
                    a.replace_with(s)
                line = tag.get_text().replace('\xa0', ' ')
                line = ' '.join(line.split())
                if tag.name == 'p':
                    lines += [{'tag': 'p',
                               'line': line}]
                if tag.name == 'ul':
                    for li in tag.find_all('li'):
                        line = '- '+li.get_text(strip=True)+'\n'
                        lines += [{'tag': 'li',
                                   'line': line}]
                if re.match(r'^h\d$', tag.name):
                    lines += [{'tag': 'h',
                               'line': line}]
                if tag.name == 'blockquote':
                    lines += [{'tag': 'blockquote',
                               'line': line}]
        return lines


#    проверяет допустим ли тег для записи
    def tag_allowed(self, element):
        if element.name in self.alowed_tags:
            return True
        if isinstance(element, element.Comment):
            return False
        return True
