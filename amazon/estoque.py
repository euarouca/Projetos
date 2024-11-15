import pandas as pd

# Carregar os arquivos Excel
plan1 = pd.read_excel('produtos_restantes.xlsx', dtype={'Nome': str})
plan2 = pd.read_excel('Cutler-Hammer.xlsx', dtype={'Nome': str})

# Adicionar uma coluna de estoque em plan1, preenchida inicialmente com valores NaN
plan1['Estoque'] = None

# Preencher a coluna de estoque em plan1 com base na correspondência dos valores de 'Nome'
for index1, upc in plan1.iterrows():
    for index2, upc2 in plan2.iterrows():
        if upc['Nome'] in upc2['Nome']:
            # Copiar o valor de estoque de plan2 para plan1
            plan1.at[index1, 'Estoque'] = plan2.at[index2, 'Estoque']
            break  # Se encontrar a correspondência, pode parar de procurar

# Salvar o resultado de volta em um novo arquivo Excel
plan1.to_excel('produtos_restantes_com_estoque.xlsx', index=False)
