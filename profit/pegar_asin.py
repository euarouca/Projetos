import pandas as pd
lista = list()

with open(f'profit/arquivos/asin.txt', 'r', encoding='utf-8') as arquivo:
        linhas = arquivo.readlines()
        for linha in linhas:
            if 'ASIN: ' in linha:
               asin = linha[6:-1]
               lista.append([asin])
               
               
df_final = pd.DataFrame(lista, columns=['ASIN'])
    
df_final.to_excel('profit/arquivos/asin.xlsx', index=False)