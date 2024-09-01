import pyautogui
from time import sleep
from bs4 import BeautifulSoup
from print import tirar_print
from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from escaner import reconhecer


XPATH_SAVE = '/html/body/div[2]/div/section/section/article/div[2]/div/div[1]/div/div/div[3]/div'

url_base = 'https://www.profitprotectorpro.com/app/'
# servico = Service(ChromeDriverManager().install())
driver = webdriver.Chrome()
driver.maximize_window()

class Profit:
    def __init__(self):
        self.login()
        self.indice_pais_atual = 1
        self.xpaths = {
            'um_pais':{
                'preco_minimo': '/html/body/div[2]/div/section/section/article/div[2]/div/div[1]/div/div/span/div/div/div/div/div/div[5]/div/div[10]/div[2]/div[1]/input',
                'preco_maximo': '/html/body/div[2]/div/section/section/article/div[2]/div/div[1]/div/div/span/div/div/div/div/div/div[5]/div/div[11]/div[2]/div[1]/input',
                'estrategia': '/html/body/div[2]/div/section/section/article/div[2]/div/div[1]/div/div/span/div/div/div/div/div/div[5]/div/div[12]/div[2]/select',
                'on_off': '/html/body/div[2]/div/section/section/article/div[2]/div/div[1]/div/div/span/div/div/div/div/div/div[3]/div/div[3]/div[1]/div/div[1]/input'
            },
            'dois_paises': {
                'preco_minimo': f'/html/body/div[2]/div/section/section/article/div[2]/div/div[1]/div/div/span/div[{self.indice_pais_atual}]/div/div/div/div/div[5]/div/div[10]/div[2]/div[1]/input',
                'preco_maximo': f'/html/body/div[2]/div/section/section/article/div[2]/div/div[1]/div/div/span/div[{self.indice_pais_atual}]/div/div/div/div/div[5]/div/div[11]/div[2]/div[1]/input',
                'estrategia': f'/html/body/div[2]/div/section/section/article/div[2]/div/div[1]/div/div/span/div[{self.indice_pais_atual}]/div/div/div/div/div[5]/div/div[12]/div[2]/select',
                'on_off': f'/html/body/div[2]/div/section/section/article/div[2]/div/div[1]/div/div/span/div[{self.indice_pais_atual}]/div/div/div/div/div[3]/div/div[3]/div[1]/div/div[1]/input',
                'pais_dois': '/html/body/div[2]/div/section/section/article/div[2]/div/div[1]/div/div/span/div[1]/div/div/div/div/div[1]/div[3]/div[2]'            
            },
        }
    
    def mudar_indice_pais(self, indice):
        self.indice_pais_atual = indice
        self.xpaths = {
            'um_pais':{
                'preco_minimo': '/html/body/div[2]/div/section/section/article/div[2]/div/div[1]/div/div/span/div/div/div/div/div/div[5]/div/div[10]/div[2]/div[1]/input',
                'preco_maximo': '/html/body/div[2]/div/section/section/article/div[2]/div/div[1]/div/div/span/div/div/div/div/div/div[5]/div/div[11]/div[2]/div[1]/input',
                'estrategia': '/html/body/div[2]/div/section/section/article/div[2]/div/div[1]/div/div/span/div/div/div/div/div/div[5]/div/div[12]/div[2]/select',
                'on_off': '/html/body/div[2]/div/section/section/article/div[2]/div/div[1]/div/div/span/div/div/div/div/div/div[3]/div/div[3]/div[1]/div/div[1]/input'
            },
            'dois_paises': {
                'preco_minimo': f'/html/body/div[2]/div/section/section/article/div[2]/div/div[1]/div/div/span/div[{self.indice_pais_atual}]/div/div/div/div/div[5]/div/div[10]/div[2]/div[1]/input',
                'preco_maximo': f'/html/body/div[2]/div/section/section/article/div[2]/div/div[1]/div/div/span/div[{self.indice_pais_atual}]/div/div/div/div/div[5]/div/div[11]/div[2]/div[1]/input',
                'estrategia': f'/html/body/div[2]/div/section/section/article/div[2]/div/div[1]/div/div/span/div[{self.indice_pais_atual}]/div/div/div/div/div[5]/div/div[12]/div[2]/select',
                'on_off': f'/html/body/div[2]/div/section/section/article/div[2]/div/div[1]/div/div/span/div[{self.indice_pais_atual}]/div/div/div/div/div[3]/div/div[3]/div[1]/div/div[1]/input',
                'pais_dois': '/html/body/div[2]/div/section/section/article/div[2]/div/div[1]/div/div/span/div[1]/div/div/div/div/div[1]/div[3]/div[2]'            
            },
        }
        
    def login(self):
        driver.get(url_base + 'login.php')
        email = driver.find_element('xpath', '/html/body/div[1]/div/section[2]/div/div/div/form/div[1]/input')
        email.send_keys('contact@maguirestore.net')
        senha = driver.find_element('xpath', '/html/body/div[1]/div/section[2]/div/div/div/form/div[2]/input')
        senha.send_keys('Lucascintra@97')
        sign_in = driver.find_element('xpath', '/html/body/div[1]/div/section[2]/div/div/div/form/button').click()
        sleep(1)
        
    def procurar_produto(self, asin):
        asin = str(asin).upper().strip()
        driver.get(url_base + 'repricing.php?search=' + asin)
        self.teste()
        
    def inserir_preco(self, preco_minimo, preco_maximo, xpath_minimo, xpath_maximo):
        entrada_preco_minimo = driver.find_element('xpath', xpath_minimo)
        entrada_preco_maximo = driver.find_element('xpath', xpath_maximo)
        
       
        try:
            sleep(1)
            entrada_preco_minimo.clear()
            entrada_preco_minimo.send_keys(str(preco_minimo))
        except:
            sleep(1)
            self.mudar_indice_pais(3)
            entrada_preco_minimo = driver.find_element('xpath',  self.xpaths['dois_paises']['preco_minimo'])
            entrada_preco_minimo.clear()
            entrada_preco_minimo.send_keys(str(preco_minimo))
            
        
          
        try:
            sleep(1)
            entrada_preco_maximo.clear()
            entrada_preco_maximo.send_keys(str(preco_maximo))
        except:  
            sleep(1)  
            self.mudar_indice_pais(3)
            entrada_preco_maximo = driver.find_element('xpath', self.xpaths['dois_paises']['preco_maximo'])
            entrada_preco_maximo.clear()
            entrada_preco_maximo.send_keys(str(preco_maximo))
                
    def estrategia(self, xpath_estrategia):
        sleep(1)
        select = Select(driver.find_element('xpath', xpath_estrategia))
        select.select_by_value('21')
    
    def reavaliacao(self, xpath_on_off):
        aux = reconhecer()
        if aux == False:
            sleep(1)
            on_off = driver.find_element('xpath', xpath_on_off).click()
            
        sleep(0.5)
        
    def save(self):
        sleep(2)
        save = driver.find_element('xpath', XPATH_SAVE).click()
        
    def estados_unidos(self, preco_minimo, preco_maximo, xpath_minimo, xpath_maximo, xpath_estrategia, xpath_on_off):
        sleep(2)
        self.inserir_preco(preco_minimo, preco_maximo, xpath_minimo, xpath_maximo)
        self.estrategia(xpath_estrategia)
        self.save()
        self.reavaliacao(xpath_on_off)
        tirar_print(self.asin, 'US')
    
    def canada(self, preco_minimo, preco_maximo, xpath_minimo, xpath_maximo, xpath_estrategia, xpath_on_off):
        sleep(2)
        self.inserir_preco(preco_minimo, preco_maximo, xpath_minimo, xpath_maximo)
        self.estrategia(xpath_estrategia)
        self.save()
        self.reavaliacao(xpath_on_off)    
        tirar_print(self.asin, 'CA')
        
    def teste(self):
        self.lista_paises = list()
        html = BeautifulSoup(driver.page_source, 'html.parser')
        paises = html.findAll('div', attrs={'class': 'float-start ps-2 pe-1 mkt-name'})
        for pais in paises:
            if 'CA' in pais.text:
                self.lista_paises.append('CA')
            if 'US' in pais.text:
                self.lista_paises.append('US')
            
        
    def opcoes_paises(self, valores):
        self.asin = valores[8]
        
        #canada
        if 'CA' in self.lista_paises and 'US' not in self.lista_paises:
            self.canada(valores[6],
                        valores[7],
                        self.xpaths['um_pais']['preco_minimo'],
                        self.xpaths['um_pais']['preco_maximo'],
                        self.xpaths['um_pais']['estrategia'],
                        self.xpaths['um_pais']['on_off'],
                        )
               
        
        #estados unidos
        if 'US' in self.lista_paises and 'CA' not in self.lista_paises:
            self.estados_unidos(valores[0],
                                valores[1],
                                self.xpaths['um_pais']['preco_minimo'],
                                self.xpaths['um_pais']['preco_maximo'],
                                self.xpaths['um_pais']['estrategia'],
                                self.xpaths['um_pais']['on_off'],
                                )
                  
              
        #canada e estados unidos
        if 'CA' in self.lista_paises and 'US' in self.lista_paises:
            self.mudar_indice_pais(1)
            self.canada(valores[6],
                        valores[7],
                        self.xpaths['dois_paises']['preco_minimo'],
                        self.xpaths['dois_paises']['preco_maximo'],
                        self.xpaths['dois_paises']['estrategia'],
                        self.xpaths['dois_paises']['on_off']
                        )
            self.mudar_indice_pais(2)
            trocar_pais = driver.find_element('xpath', self.xpaths['dois_paises']['pais_dois']).click()
            sleep(1)
            self.estados_unidos(valores[0],
                                valores[1],
                                self.xpaths['dois_paises']['preco_minimo'],
                                self.xpaths['dois_paises']['preco_maximo'],
                                self.xpaths['dois_paises']['estrategia'],
                                self.xpaths['dois_paises']['on_off']
                                )

        

        
        

        
        
        
    