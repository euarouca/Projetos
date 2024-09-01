import pandas as pd

def calcular_valor_venda(valor_compra, entrega):
    # Gasto fixo
    if '$' in valor_compra:
        valor_compra = valor_compra.replace('$', '').strip()
        valor_compra = valor_compra.replace(',','.')
        if len(valor_compra) > 6:
            valor_compra = list (valor_compra)
            valor_compra[-7] = ''
            valor_compra = ''.join(valor_compra)
        valor_compra= float(valor_compra)
    
    if '$' in entrega:
        entrega = entrega.replace('$', '').strip()
        entrega = entrega.replace(',','.')
        entrega= int(float(entrega))
        
    gasto_fixo = 7 + entrega

    # Porcentagem do valor da venda como gasto adicional
    percentual_gasto_adicional = 0.12

    # Lucro desejado
    lucro_desejado = 0.22

    # Cálculo do valor de venda necessário para atingir o lucro desejado
    valor_venda = (valor_compra + gasto_fixo) / (1 - percentual_gasto_adicional - lucro_desejado)

    return valor_venda

df = pd.read_excel('profit/arquivos/fbm.xlsx')

def asin(asin_entrada):
    for linha, asin_planilha in enumerate(df['ASIN']):
        if asin_entrada in str(asin_planilha):
            valor_venda_minimo = calcular_valor_venda(df.loc[linha][0], df.loc[linha][2])
            return(round(valor_venda_minimo) + 0.99)