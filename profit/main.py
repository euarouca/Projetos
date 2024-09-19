from auxiliar import Profit
import PySimpleGUI as sg
import pyperclip
from calculadora_lucro import asin
import pandas as pd
import pyperclip
from print import tirar_eua, tirar_can   

df = pd.read_excel('profit/arquivos/asin.xlsx')
contador_asin = 0

def conversor_moedas(valores):
    precos_convertidos = dict()
    precos_convertidos['preço canadá minímo'] = round(((float(valores[0]))* 2.04)) 
    if precos_convertidos['preço canadá minímo'] % 100 <= 10:
        auxiliar_minimo = precos_convertidos['preço canadá minímo'] % 10
        diferenca =  auxiliar_minimo + 1 
        precos_convertidos['preço canadá minímo'] = precos_convertidos['preço canadá minímo'] - diferenca + 0.99
    else:
        auxiliar_minimo = precos_convertidos['preço canadá minímo'] % 10
        diferenca = 9 - auxiliar_minimo + 0.99
        precos_convertidos['preço canadá minímo'] += diferenca
    
    precos_convertidos['preço canadá máximo'] = round(((float(valores[0])) * 2.448)) 
    if precos_convertidos['preço canadá máximo'] % 100 <= 10:
        auxiliar_minimo = precos_convertidos['preço canadá máximo'] % 10
        diferenca =  auxiliar_minimo + 1 
        precos_convertidos['preço canadá máximo'] = precos_convertidos['preço canadá máximo'] - diferenca + 0.99
    else:
        auxiliar_minimo = precos_convertidos['preço canadá máximo'] % 10
        diferenca = 9 - auxiliar_minimo + 0.99
        precos_convertidos['preço canadá máximo'] += diferenca
                
    return precos_convertidos

sg.theme('Dark')

layout = [
    [sg.Text('100-129     150-199     170-229     200-269     250-329     300-369       |||'), sg.Text('min-> ', key='min') ],
    [sg.Text('350-429     400-499     450-569     500-629     550-699     600-769       |||'), sg.Text('Preço min -> '), sg.Input(size=(6, 6)), sg.Text('Preço Canadá min-> ', key='canadamin')],
    [sg.Text('650-799     700-869     750-969     800-999     850-1099    900-1199     |||'), sg.Text('Preço max -> '), sg.Input(size=(6, 6)), sg.Text('Preço Canadá max-> ', key='canadamax')],
    [sg.Text('1000-1299   1100-1499   1200-1699   1300-1799   1400-1899               |||'),sg.Button('ASIN'), sg.Button('PRINTCA'),sg.Button('PRINTEUA'), sg.OK(), sg.Button('Enviar')],

    ]

window = sg.Window('Conversor', layout)
profit = Profit()

while True:
    event, valores = window.read()

    if event == sg.WINDOW_CLOSED:
        break
    
    if event == 'PRINTCA':
        tirar_can(df["ASIN"][contador_asin-1])
        
    if event == 'PRINTEUA':
        tirar_eua(df["ASIN"][contador_asin-1])
    
    if event == 'ASIN':
        window['min'].update(f'min-> {asin(df["ASIN"][contador_asin])}')
        profit.procurar_produto(df["ASIN"][contador_asin])
        pyperclip.copy(df["ASIN"][contador_asin])
        contador_asin += 1
        
    if event == 'OK':
        precos = conversor_moedas(valores)
        valores[0] = float(valores[0]) + 0.99
        valores[1] = float(valores[1]) + 0.99
        valores[6] = precos["preço canadá minímo"]
        valores[7] = precos["preço canadá máximo"]
        window['canadamin'].update(f'Preço Canadá -> {valores[6]}')
        window['canadamax'].update(f'Preço Canadá -> {valores[7]}')

    if event == 'Enviar':
        valores[0] = float(valores[0]) + 0.99
        valores[1] = float(valores[1]) + 0.99
        valores[6] = precos["preço canadá minímo"]
        valores[7] = precos["preço canadá máximo"]
        valores[8] = df["ASIN"][contador_asin-1]
        window['canadamin'].update(f'Preço Canadá -> {valores[6]}')
        window['canadamax'].update(f'Preço Canadá -> {valores[7]}')
        profit.opcoes_paises(valores)
            
window.close()