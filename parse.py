from parse import Parse
import sys
import re
from urllib.parse import urlparse


def main():
    if len(sys.argv) < 2:
        print("Нет ссылки на статью")
        exit()
    if len(sys.argv) == 2:
        url = urlparse(sys.argv[1])
        if url.netloc:
            try:
                Parse(url.geturl())
            except ValueError as e:
                print('Ошибка: '+str(e))
        else:
            print('В аргументе не ссылка')


if __name__ == "__main__":
    main()
