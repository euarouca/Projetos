import pandas as pd
from time import sleep
from bs4 import BeautifulSoup
from selenium import webdriver
from amazoncaptcha import AmazonCaptcha
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

TITULO_CARD = 'a-link-normal s-underline-text s-underline-link-text s-link-style a-text-normal'
DOGS = "Sorry! Something went wrong on our end. Please go back and try again or go to Amazon's home page."

class BaseAmazon:
    def __init__(self, email, senha):
        # Iniciar o navegador
        # Logar no asinzen
        # Validar captcha
        
        # servico = Service(ChromeDriverManager().install())
        chrome_option = Options()
        chrome_option.add_extension('vendas_asinzen/arquivos/extensao/asinzen.crx')
        self.driver = webdriver.Chrome(options=chrome_option)
        self.driver.maximize_window()
        self.validar_captcha()
        self.logar_asinzen(email, senha)
        
    def logar_asinzen(self, email, senha):
        # Fazer o login na conta do asinzen
        url_login = 'https://www.amazon.com/World-Percy-Jackson-Sun-Star/dp/1368081150/ref=sr_1_1_sspa?keywords=percy+jackson&qid=1678418217&sr=8-1-spons&psc=1&spLa=ZW5jcnlwdGVkUXVhbGlmaWVyPUEyUTU3NFQzTkFTUk9IJmVuY3J5cHRlZElkPUEwODc4MTEyMVIxSDJKQ0UwRjg5RSZlbmNyeXB0ZWRBZElkPUEwMzEzNDc4M0hISUg5SUczNjA3TSZ3aWRnZXROYW1lPXNwX2F0ZiZhY3Rpb249Y2xpY2tSZWRpcmVjdCZkb05vdExvZ0NsaWNrPXRydWU='
        self.driver.get(url_login)
        
        sleep(4)
        caixa_email1 = self.driver.find_element('xpath', '//*[@id="az-app-container"]/div/div[2]/form/div[1]/div/input') # caixa de email
        caixa_email1.send_keys(email)
        botaoNext1 = self.driver.find_element('xpath', '//*[@id="az-app-container"]/div/div[2]/form/div[2]/input').click() # botao de next
        caixa_password1 = self.driver.find_element('xpath', '//*[@id="az-app-container"]/div/div[2]/form/div[2]/div/input') # caixa de senha
        caixa_password1.send_keys(senha)
        botaoLogin1 = self.driver.find_element('xpath', '//*[@id="az-app-container"]/div/div[2]/form/div[4]/input').click() # botao logar
        sleep(2)
        self.driver.close() # fechar aba da extensao 
        self.driver.switch_to.window(self.driver.window_handles[0])  # mudar para aba principal  
        
    def validar_captcha(self):
        # Função para validar o captcha e não ficar dando erro que aparecem cachorros
        
        self.driver.get('https://www.amazon.com/errors/validateCaptcha')
        link = self.driver.find_element(By.XPATH, "//div[@class = 'a-row a-text-center']//img").get_attribute('src')
        captcha = AmazonCaptcha.fromlink(link)
        captcha_value = AmazonCaptcha.solve(captcha)
        input_field = self.driver.find_element(By.ID, "captchacharacters").send_keys(captcha_value)
        button = self.driver.find_element(By.CLASS_NAME, "a-button-text").click()
        
    def stop_dogs(self):
        # Parar os dogs
        error = BeautifulSoup(self.driver.page_source, 'html.parser')
        error = error.find('img', attrs={'alt': DOGS})
        
        contador = 0
        if error is not None:
            while True:
                sleep(60) # Esperar 60 segundos
                contador += 1 # Tentar 5 vezes a pagina e passar pra próxima
                self.driver.refresh() # da reload na pagina
                error = BeautifulSoup(self.driver.page_source, 'html.parser') # verificar o erro 
                error = error.find('img', attrs={'alt': DOGS})
                if error is None or contador == 5: # 
                    break

class Amazon(BaseAmazon):
    def __init__(self, email, senha, nome_planilha):
        super().__init__(email, senha)
        self.planilha = self.dados_planilha(nome_planilha) # lendo os produtos da planilha
        self.tamanho_plan = len(self.planilha['ASIN']) # tamanho da planilha
        self.indice_atual = 0 # O ponto de partida onde vai começar a busca

    def dados_planilha(self, nome):
        # ler dados da planilha em excel
        return pd.read_excel('vendas_asinzen/arquivos/' + nome)
    
    def asin(self):
        # Procurando quando o produto for do tipo de UPC
        while self.indice_atual != (self.tamanho_plan):
            self.nome_produto = str(self.planilha['ASIN'][self.indice_atual]).upper() # Part Number do produto
            
            self.search() # Procurar o produto 
            self.stop_dogs() # parar de dar cachorro
            self.conteudo_pagina() # Pesquisa e entra na pagina do produto
            self.asinzen() # pega o historico de vendas do asinzen
            self.indice_atual += 1 # Passa pro próximo produto
            print('Indice Atual: ',self.indice_atual)
    
    def search(self):
        # Buscar o produto na amazon
        url = f'https://www.amazon.com/s?k={self.nome_produto}'
        self.driver.get(url)
        sleep(1)

    def conteudo_pagina(self):
        # Buscar as informações no HTML da página
        html = BeautifulSoup(self.driver.page_source, 'html.parser') # conteudo da pagina
        
        try:
            url_anuncio = 'https://www.amazon.com/' + html.find('a', attrs={'class': TITULO_CARD})['href']
            self.driver.get(url_anuncio)
            
        except:
            pass
        
    def asinzen(self):
        # Confere se o produto é da mesma marca que da planilha 
        self.pausa_asinzen()        
        if self.conferir_asin():
            try:
                html = BeautifulSoup(self.driver.page_source, 'html.parser')
                
                overlay = html.find('div', attrs={'class': 'Historical-Data'})
                overlay = html.find('div', attrs={'class': 'Overlay'})
                
                time = 0
                while True:
                    sleep(0.5) 
                    time += 1 # Tentar 40 vezes a pagina e passar pra próxima
                    html = BeautifulSoup(self.driver.page_source, 'html.parser')
                    overlay = html.find('div', attrs={'class': 'Historical-Data'})
                    overlay = html.find('div', attrs={'class': 'Overlay'})
                    if overlay is None or time == 40: # 
                        break
                
                if time == 40:
                    # Locate the input element by its ID
                    input_element = self.driver.find_element(By.ID, 'Sellprice-FBA')
                    # Get the value attribute
                    value = input_element.get_attribute('value')
                    self.vendas = {
                    'day30' :0,
                    'day90' : 0,
                    'day180' : 0,
                    'Preço' : value,
                }
                else:  
                    # Locate the input element by its ID
                    input_element = self.driver.find_element(By.ID, 'Sellprice-FBA')
                    # Get the value attribute
                    value = input_element.get_attribute('value')
                    historico = html.find('div', attrs={'class': 'keepa-data-table col-xl-12'})
                    itens = historico.find_all('div', attrs={'class', 'row'})
                    est_sales = itens[3]
                    meses = est_sales.find_all('div', attrs={'class': 'text-right col-3'})
                    self.vendas = {
                        'day30' : meses[0].text,
                        'day90' : meses[1].text,
                        'day180' : meses[2].text,
                        'Preço' : value,
                    }
                    self.gerar_planilha() # planilha final
            except:
                pass

    def conferir_asin(self):
        try:
            html = BeautifulSoup(self.driver.page_source, 'html.parser')
            html = html.find('div', attrs={'class': 'col-sm-6'})
            linhas = html.find_all('div', attrs={'class', 'col-12'})
            for linha in linhas:
                if self.planilha['ASIN'][self.indice_atual] in linha.text:
                    return True
            
            return False
        
        except:
            return False
        
    def pausa_asinzen(self):
        # Se excerder o limite de requisições em uma hora ele da uma pausa
        try:
            botao_next = self.driver.find_element('xpath', '//*[@id="az-app-container"]/div/div[2]/form/div[2]/input').click()
            botao_login = self.driver.find_element('xpath', '//*[@id="az-app-container"]/div/div[2]/form/div[4]/input').click()

            sleep(3)
            erro300 = BeautifulSoup(self.driver.page_source, 'html.parser')
            erro300 = erro300.find('div', attrs={'class': 'detail-app-container'})
            erro300 = erro300.find('strong').text

            if erro300 == 'Error 300': # Excedeu o limite de requisições por hora
                while True:
                    sleep(60)
                
                    botao_login = self.driver.find_element('xpath', '//*[@id="az-app-container"]/div/div[3]/form/div[4]/input').click()

                    erro300 = BeautifulSoup(self.driver.page_source, 'html.parser')
                    erro300 = erro300.find('div', attrs={'class': 'detail-app-container'})
                    erro300 = erro300.find('strong').text
                    
                    if erro300 is None:
                        break
                    
        except:
            pass
    
    def gerar_planilha(self):
        self.planilha.loc[self.indice_atual, 'Day 30'] = self.vendas['day30']
        self.planilha.loc[self.indice_atual, 'Day 90'] = self.vendas['day90']
        self.planilha.loc[self.indice_atual, 'Day 180'] = self.vendas['day180']
        self.planilha.loc[self.indice_atual, 'Preço'] = self.vendas['Preço']
        self.planilha.to_excel('vendas_asinzen/arquivos/teste.xlsx', index=False)

navegador = Amazon('lucasarouca2002@gmail.com', 'arouca123', 'teste.xlsx')
navegador.asin()
