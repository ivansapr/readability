from parse import Parse
import sys
import re

def main():
    
    if len(sys.argv) < 2:
        print("Нет ссылки на статью")
        exit()
    if len(sys.argv) == 2:
        url = sys.argv[1]
        r = re.match(r'(?:http[s]?:\/\/)?([\w\d-]+\.[\w\d-]+)',url)
        if r:
            try:
                r = Parse(url)
            except Exception as e:
                print('Ошибка: '+str(e))  
#                print('Error on line {}'.format(sys.exc_info()[-1].tb_lineno))
        else:
            print('В аргументе не ссылка')
            
            
if __name__ == "__main__":
    main()