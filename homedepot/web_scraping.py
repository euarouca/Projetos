from selenium import webdriver
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from time import sleep
import re
import pandas as pd

class HomeDepot():
    def __init__(self):
        self.driver = webdriver.Chrome()
        self.driver.maximize_window()
        self.produtos = list()
    
    def gerar_planilha(self, categoria):
        prods = pd.DataFrame(self.produtos, columns=['Nome', 'Preço', 'Marca', 'TipoPlanilha'])
        prods.to_excel(f'homedepot/planilhas-geradas/{categoria}.xlsx', index=False)
    
    def extrair_valores(self):
        html = BeautifulSoup(self.driver.page_source, 'html.parser')
        # Itera sobre as seções e extrai informações dos cartões
        for i in range(1, 4):  # Aqui, vamos acessar as seções de 1 a 3
            section = html.find('section', attrs={'id': f'browse-search-pods-{i}'})
            if section:
                cards = section.findAll('div', attrs={'class': 'browse-search__pod col__12-12 col__6-12--xs col__4-12--sm col__3-12--md col__3-12--lg'})
                # Extrai as informações de cada cartão encontrado na seção
                for card in cards:
                    match = re.search(r'\$\d+(?:\.\d{2})', card.text)

                    # Se o preço for encontrado, atribui o valor; caso contrário, define como '0'
                    preco = match.group() if match else "$0"
                    if preco:
                        model = card.find('div', attrs={'class': 'sui-flex sui-text-xs sui-text-subtle sui-font-normal'}).text.strip()[7:]
                        marca_element = card.find('p', attrs={'class': 'sui-text-primary sui-font-w-bold sui-text-xs sui-leading-tight sui-mb-1'})
                        marca = marca_element.text if marca_element else 'None'
                        self.produtos.append([model, float(preco[1:]), marca.split()[0], 'PartNumber'])           

    def search(self, url, pagina):
        if pagina == 0:
            self.driver.get(url)
        else:
            self.driver.get(url + '?Nao=' + str(pagina))
        for i in range(4):  # Ajuste o número de rolagens conforme necessário
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            sleep(2)  # Dê tempo para que o conteúdo carregue
    
    def main(self, categoria):
        pag = 0
        for n in range(125):
            self.search(categoria, pag)
            self.extrair_valores()
            self.gerar_planilha('heating-venting-cooling')
            pag += 24
            print(pag)
        self.driver.quit() # fecha o navegador


x = 'https://www.homedepot.com/b/Heating-Venting-Cooling-HVAC-Supplies/N-5yc1vZc4nl'
teste = HomeDepot()
teste.main(x)