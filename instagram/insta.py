import pandas as pd
seguindo = list()
seguidores = list()
cusao = list()

with open(f'instagram/seguindo.txt', 'r', encoding='utf-8') as arquivo:
        linhas = arquivo.readlines()
        for c, linha in enumerate(linhas):
            if 'Foto do perfil' in linha:
               nome = linha.split(' ')
               nome = nome[-1]
               seguindo.append(nome)        

with open(f'instagram/seguidores.txt', 'r', encoding='utf-8') as arquivo:
        linhas = arquivo.readlines()
        for c, linha in enumerate(linhas):
            if 'Foto do perfil' in linha:
               nome = linha.split(' ')
               nome = nome[-1]
               seguidores.append(nome) 
               
for nome in seguindo:
    if nome not in seguidores:
        cusao.append(nome)


df_final = pd.DataFrame(cusao, columns=['Falsos'])
    
df_final.to_excel('instagram/falsos.xlsx', index=False)