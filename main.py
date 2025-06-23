import os
import textwrap
from sqlalchemy import create_engine, Column, String, Integer, Float, ForeignKey, UniqueConstraint, Boolean
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from time import sleep
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.support.ui import Select
import pandas as pd
import PySimpleGUI as sg
import pyperclip

# --- 1. CONFIGURAÇÃO DO BANCO DE DADOS ---
try:
    script_dir = os.path.dirname(os.path.abspath(__file__))
except NameError:
    script_dir = os.getcwd()

db_path = os.path.join(script_dir, 'maguire.db')
db_connection_string = f'sqlite:///{db_path}'
db = create_engine(db_connection_string)

Session = sessionmaker(bind=db)
session = Session()
Base = declarative_base()

# --- 2. DEFINIÇÃO DAS CLASSES ORM ---
class Product(Base):
    __tablename__ = 'produtos'
    __table_args__ = (UniqueConstraint('partNumber', 'pack', name='uix_partnumber_pack'),)
    id = Column(Integer, primary_key=True, autoincrement=True)
    brand = Column(String)
    partNumber = Column(String, index=True, nullable=False)
    pack = Column(Integer, nullable=False)
    fbms = relationship("FBM", back_populates="product")

class FBM(Base):
    __tablename__ = 'fbm'
    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey('produtos.id'), nullable=False)
    asin = Column(String, index=True, unique=True, nullable=False)
    last_price = Column(Float)
    current_price = Column(Float)
    supplier = Column(String)
    stock = Column(Integer)
    prime_stock = Column(Integer)
    all_stock = Column(Integer)
    gap_stock = Column(Integer)
    promotion = Column(String)
    product = relationship("Product", back_populates="fbms")

class Distributor(Base):
    __tablename__ = 'distribuidores'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, index=True, unique=True, nullable=False)
    prime = Column(Boolean, default=False, nullable=False)

class DistributorData(Base):
    __tablename__ = 'dados_distribuidor'
    __table_args__ = (UniqueConstraint('distributor_name', 'partNumber', 'pack', name='uix_dist_partnumber_pack'),)
    id = Column(Integer, primary_key=True, autoincrement=True)
    distributor_name = Column(String, ForeignKey('distribuidores.name', ondelete='CASCADE', onupdate='CASCADE'), index=True, nullable=False)
    sku = Column(String)
    partNumber = Column(String, nullable=False)
    pack = Column(Integer, nullable=False)
    price = Column(Float)
    stock = Column(Integer)
    distributor_relationship = relationship("Distributor", backref="data_entries")

# --- 3. LÓGICA DE CÁLCULO E CONSULTA ---
def calcular_valor_venda_ideal(valor_compra, entrega):
    if valor_compra is None or entrega is None: return 0.0
    gasto_fixo = 7 + float(entrega)
    percentual_gasto_adicional = 0.12
    lucro_desejado = 0.22
    valor_venda = (float(valor_compra) + gasto_fixo) / (1 - percentual_gasto_adicional - lucro_desejado)
    return valor_venda

def obter_entrega_do_excel(asin_entrada, df_fbm):
    for linha, asin_planilha in enumerate(df_fbm['ASIN']):
        if asin_entrada in str(asin_planilha):
            return df_fbm.loc[linha][df_fbm.columns[20]]
    return None

def buscar_informacoes_fornecedores(asin_alvo: str, df_fbm: pd.DataFrame) -> str:
    fbm_entry = session.query(FBM).filter(FBM.asin == asin_alvo).first()
    if not fbm_entry or not fbm_entry.product:
        return f"ASIN '{asin_alvo}' não encontrado ou não associado a um produto no banco de dados."

    produto = fbm_entry.product
    fornecedor_escolhido_nome = fbm_entry.supplier

    custo_entrega = obter_entrega_do_excel(asin_alvo, df_fbm)
    if custo_entrega is None:
        return f"Não foi possível encontrar o custo de entrega para o ASIN '{asin_alvo}' na planilha fbm.xlsx."

    dados_fornecedores = session.query(DistributorData).join(Distributor).filter(
        DistributorData.partNumber == produto.partNumber,
        DistributorData.pack == produto.pack,
        DistributorData.stock > 0
    ).all()

    if not dados_fornecedores:
        return f"Nenhum fornecedor com estoque encontrado para o produto PartNumber: {produto.partNumber}."

    dados_fornecedores_ordenados = sorted(dados_fornecedores, key=lambda f: f.stock, reverse=True)

    info_fornecedor_escolhido = "Fornecedor escolhido não encontrado com estoque."
    fornecedores_prime = []
    fornecedores_normais = []

    # --- MUDANÇA AQUI: Lógica de separação corrigida e simplificada ---
    for dado in dados_fornecedores_ordenados:
        preco_ideal = calcular_valor_venda_ideal(dado.price, custo_entrega)
        
        nome_str = f"{(dado.distributor_name + ':'):<40}"
        preco_compra_str = f"{f'${dado.price:.2f}':>12}"
        estoque_str = f"{f'{dado.stock}':>10}"
        preco_ideal_str = f"{f'S${preco_ideal:.0f}':>9}"
        
        info_str = f"{nome_str} {preco_compra_str} - {estoque_str} - {preco_ideal_str}"

        # Lógica corrigida para garantir que nenhum fornecedor seja omitido
        if dado.distributor_name == fornecedor_escolhido_nome:
            info_fornecedor_escolhido = info_str
        elif dado.distributor_relationship.prime:
            fornecedores_prime.append(info_str)
        else:
            fornecedores_normais.append(info_str)

    # --- MUDANÇA AQUI: Constrói a lista final sem os títulos ---
    lista_final_texto = []
    lista_final_texto.append(info_fornecedor_escolhido)
    
    # Adiciona uma linha em branco se houver outros fornecedores
    if fornecedores_prime or fornecedores_normais:
        lista_final_texto.append('') 

    # Adiciona os outros fornecedores (prime primeiro, depois normais)
    lista_final_texto.extend(fornecedores_prime)
    lista_final_texto.extend(fornecedores_normais)

    return "\n".join(lista_final_texto)


# --- 4. AUTOMAÇÃO DO NAVEGADOR ---
XPATH_SAVE = '/html/body/div[2]/div/section/section/article/div[2]/div/div[1]/div/div/div[2]/div'
url_base = 'https://www.profitprotectorpro.com/app/'

class Profit:
    def __init__(self):
        self.driver = webdriver.Chrome()
        self.driver.maximize_window()
        self.login()
        self.indice_pais_atual = 1
        self.xpaths = {}
        self.atualizar_xpaths()

    def atualizar_xpaths(self):
        self.xpaths = {
            'um_pais':{
                'preco_minimo': '/html/body/div[2]/div/section/section/article/div[2]/div/div[1]/div/div/span/div/div/div/div/div/div[5]/div/div[10]/div[2]/div[1]/input',
                'preco_maximo': '/html/body/div[2]/div/section/section/article/div[2]/div/div[1]/div/div/span/div/div/div/div/div/div[5]/div/div[11]/div[2]/div[1]/input',
                'estrategia': '/html/body/div[2]/div/section/section/article/div[2]/div/div[1]/div/div/span/div/div/div/div/div/div[5]/div/div[12]/div[2]/select',
            },
            'dois_paises': {
                'preco_minimo': f'/html/body/div[2]/div/section/section/article/div[2]/div/div[1]/div/div/span/div[{self.indice_pais_atual}]/div/div/div/div/div[5]/div/div[10]/div[2]/div[1]/input',
                'preco_maximo': f'/html/body/div[2]/div/section/section/article/div[2]/div/div[1]/div/div/span/div[{self.indice_pais_atual}]/div/div/div/div/div[5]/div/div[11]/div[2]/div[1]/input',
                'estrategia': f'/html/body/div[2]/div/section/section/article/div[2]/div/div[1]/div/div/span/div[{self.indice_pais_atual}]/div/div/div/div/div[5]/div/div[12]/div[2]/select',
                'pais_dois': '/html/body/div[2]/div/section/section/article/div[2]/div/div[1]/div/div/span/div[1]/div/div/div/div/div[1]/div[3]'
            },
        }

    def mudar_indice_pais(self, indice):
        self.indice_pais_atual = indice
        self.atualizar_xpaths()

    def login(self):
        self.driver.get(url_base + 'login.php')
        sleep(1)
        self.driver.find_element('xpath', '/html/body/div[1]/div/section[2]/div/div/div/form/div[1]/input').send_keys('contact@maguirestore.net')
        self.driver.find_element('xpath', '/html/body/div[1]/div/section[2]/div/div/div/form/div[2]/input').send_keys('Lucascintra@97')
        self.driver.find_element('xpath', '/html/body/div[1]/div/section[2]/div/div/div/form/button').click()
        sleep(2)

    def procurar_produto(self, asin):
        asin = str(asin).upper().strip()
        self.driver.get(url_base + 'repricing.php?search=' + asin)
        sleep(2)
        self.detectar_paises_listados()

    def inserir_preco(self, preco_minimo, preco_maximo, xpath_minimo, xpath_maximo):
        try:
            entrada_preco_minimo = self.driver.find_element('xpath', xpath_minimo)
            entrada_preco_minimo.clear()
            entrada_preco_minimo.send_keys(str(preco_minimo))
            sleep(0.5)
            entrada_preco_maximo = self.driver.find_element('xpath', xpath_maximo)
            entrada_preco_maximo.clear()
            entrada_preco_maximo.send_keys(str(preco_maximo))
        except Exception as e:
            print(f"Erro ao inserir preço: {e}")

    def estrategia(self, xpath_estrategia):
        try:
            select = Select(self.driver.find_element('xpath', xpath_estrategia))
            select.select_by_value('21')
        except Exception as e:
            print(f"Erro ao selecionar estratégia: {e}")

    def save(self):
        try:
            sleep(1)
            self.driver.find_element('xpath', XPATH_SAVE).click()
            sleep(2)
        except Exception as e:
            print(f"Erro ao salvar: {e}")

    def canada(self, preco_minimo, preco_maximo, xpath_minimo, xpath_maximo, xpath_estrategia):
        self.inserir_preco(preco_minimo, preco_maximo, xpath_minimo, xpath_maximo)
        self.estrategia(xpath_estrategia)
        self.save()

    def estados_unidos(self, preco_minimo, preco_maximo, xpath_minimo, xpath_maximo, xpath_estrategia):
        self.inserir_preco(preco_minimo, preco_maximo, xpath_minimo, xpath_maximo)
        self.estrategia(xpath_estrategia)
        self.save()

    def detectar_paises_listados(self):
        self.lista_paises = []
        html = BeautifulSoup(self.driver.page_source, 'html.parser')
        paises = html.findAll('div', attrs={'class': 'float-start ps-2 pe-1 mkt-name'})
        for pais in paises:
            if 'CA' in pais.text: self.lista_paises.append('CA')
            if 'US' in pais.text: self.lista_paises.append('US')

    def opcoes_paises(self, valores):
        if 'CA' in self.lista_paises and 'US' not in self.lista_paises:
            self.canada(valores[6], valores[7], self.xpaths['um_pais']['preco_minimo'], self.xpaths['um_pais']['preco_maximo'], self.xpaths['um_pais']['estrategia'])
        elif 'US' in self.lista_paises and 'CA' not in self.lista_paises:
            self.estados_unidos(valores[0], valores[1], self.xpaths['um_pais']['preco_minimo'], self.xpaths['um_pais']['preco_maximo'], self.xpaths['um_pais']['estrategia'])
        elif 'CA' in self.lista_paises and 'US' in self.lista_paises:
            self.mudar_indice_pais(1)
            self.canada(valores[6], valores[7], self.xpaths['dois_paises']['preco_minimo'], self.xpaths['dois_paises']['preco_maximo'], self.xpaths['dois_paises']['estrategia'])
            self.mudar_indice_pais(2)
            self.driver.find_element('xpath', self.xpaths['dois_paises']['pais_dois']).click()
            sleep(1)
            self.estados_unidos(valores[0], valores[1], self.xpaths['dois_paises']['preco_minimo'], self.xpaths['dois_paises']['preco_maximo'], self.xpaths['dois_paises']['estrategia'])
        else:
            sg.popup_error("Nenhum país (US ou CA) detectado na página do Profit Protector Pro.")

# --- 5. INTERFACE GRÁFICA E LÓGICA PRINCIPAL ---
def conversor_moedas(preco_min_us):
    """
    Lógica de conversão de preço que arredonda para valores 'psicológicos'
    terminados em 9.99, funcionando para qualquer magnitude de número.
    """
    precos_convertidos = {}
    
    preco_ca_min_arredondado = round(float(preco_min_us) * 2.04)
    
    if preco_ca_min_arredondado % 100 <= 10:
        auxiliar_minimo = preco_ca_min_arredondado % 10
        diferenca = auxiliar_minimo + 1 
        preco_final_min = preco_ca_min_arredondado - diferenca + 0.99
    else:
        auxiliar_minimo = preco_ca_min_arredondado % 10
        diferenca = 9 - auxiliar_minimo + 0.99
        preco_final_min = preco_ca_min_arredondado + diferenca
        
    precos_convertidos['preco_canada_minimo'] = preco_final_min

    preco_ca_max_arredondado = round(float(preco_min_us) * 2.448)
    
    if preco_ca_max_arredondado % 100 <= 10:
        auxiliar_maximo = preco_ca_max_arredondado % 10
        diferenca = auxiliar_maximo + 1 
        preco_final_max = preco_ca_max_arredondado - diferenca + 0.99
    else:
        auxiliar_maximo = preco_ca_max_arredondado % 10
        diferenca = 9 - auxiliar_maximo + 0.99
        preco_final_max = preco_ca_max_arredondado + diferenca

    precos_convertidos['preco_canada_maximo'] = preco_final_max

    return precos_convertidos

def main():
    try:
        df_asin = pd.read_excel('profit/arquivos/asin.xlsx')
        df_fbm = pd.read_excel('profit/arquivos/fbm.xlsx')
    except FileNotFoundError as e:
        sg.popup_error(f"Erro ao carregar planilhas: {e}\nVerifique se os arquivos estão na pasta 'profit/arquivos/'.")
        return

    contador_asin = 0
    sg.theme('DarkGrey14')
    
    info_column = [[sg.Text("Análise de Fornecedores", font=("Helvetica", 12, "bold"))],
                   [sg.Multiline("Clique em 'Próximo ASIN' para carregar os dados.", size=(80, 10), key='-INFO-', disabled=True, autoscroll=False, background_color='#333333', text_color='white', font=("Courier New", 10))]]

    control_column = [[sg.Text('Tabelas de Referência de Preço', font=("Helvetica", 10, "bold"))],
                      [sg.Text('100-129 | 150-199 | 170-229 | 200-269 | 250-329 | 300-369')],
                      [sg.Text('350-429 | 400-499 | 450-569 | 500-629 | 550-699 | 600-769')],
                      [sg.Text('_'*80)],
                      [sg.Text('Preço Mín US$:'), sg.Input(size=(8, 1), key='-MIN_US-'), sg.Text('Preço Máx US$:'), sg.Input(size=(8, 1), key='-MAX_US-')],
                      [sg.Text('Preço Mín CA:'), sg.Text('N/A', size=(8, 1), key='-MIN_CA-'), sg.Text('Preço Máx CA:'), sg.Text('N/A', size=(8, 1), key='-MAX_CA-')],
                      [sg.Text('_'*80)],
                      [sg.Button('Próximo ASIN', key='-ASIN-'), sg.Button('Calcular Preços', key='-CALC-'), sg.Button('Enviar para Web', key='-SEND-')],
                      [sg.Text(f"ASIN Atual: Nenhum", key='-CURRENT_ASIN-')]]

    layout = [[sg.Column(control_column), sg.VSeperator(), sg.Column(info_column)]]
    
    window = sg.Window('Repricer Maguire', layout, keep_on_top=True)
    
    profit = Profit()
    valores_envio = {}

    while True:
        event, values = window.read()

        if event == sg.WINDOW_CLOSED:
            profit.driver.quit()
            break

        if event == '-ASIN-':
            if contador_asin < len(df_asin):
                asin_atual = df_asin["ASIN"][contador_asin]
                window['-CURRENT_ASIN-'].update(f"ASIN Atual: {asin_atual}")
                pyperclip.copy(asin_atual)
                
                info_fornecedores = buscar_informacoes_fornecedores(asin_atual, df_fbm)
                window['-INFO-'].update(info_fornecedores)

                profit.procurar_produto(asin_atual)
                contador_asin += 1
            else:
                window['-INFO-'].update("Fim da lista de ASINs na planilha.")
                sg.popup("Fim da lista de ASINs!")

        if event == '-CALC-':
            try:
                min_us = float(values['-MIN_US-'])
                max_us = float(values['-MAX_US-'])
                precos_ca = conversor_moedas(min_us)
                min_ca = precos_ca['preco_canada_minimo']
                max_ca = precos_ca['preco_canada_maximo']
                window['-MIN_CA-'].update(f"{min_ca:.2f}")
                window['-MAX_CA-'].update(f"{max_ca:.2f}")
                valores_envio = {0: min_us + 0.99, 1: max_us + 0.99, 6: min_ca, 7: max_ca}
            except (ValueError, TypeError):
                sg.popup_error("Por favor, insira valores numéricos válidos para os preços nos EUA.")

        if event == '-SEND-':
            if not valores_envio:
                sg.popup_error("Calcule os preços primeiro usando o botão 'Calcular Preços'.")
                continue
            profit.opcoes_paises(valores_envio)

    window.close()
    session.close()

if __name__ == "__main__":
    Base.metadata.create_all(db)
    print("Banco de dados e tabelas verificados.")
    main()