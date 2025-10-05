# entrada_dados.py

import pandas as pd
import crud_produtos
import crud_asin
import crud_dados
import os
from database import session, Distributor, Product

# ... (o código das funções processar_csv_distribuidor e processar_pasta_distribuidores permanece o mesmo) ...
def processar_csv_distribuidor(caminho_arquivo: str):
    """
    Processa um arquivo CSV de um distribuidor, adicionando ou atualizando dados no banco.
    - Esta versão foi modificada para NÃO processar a coluna 'asin'.
    - O foco é adicionar produtos (se não existirem) e atualizar os dados do distribuidor (preço, estoque).
    """
    try:
        try:
            df = pd.read_csv(caminho_arquivo, delimiter=',')
        except Exception:
            df = pd.read_csv(caminho_arquivo, delimiter=';')
        
        df.dropna(how='all', inplace=True)
        if df.empty:
            print(f"Arquivo '{os.path.basename(caminho_arquivo)}' está vazio. Pulando.")
            return

        print(f"Lendo {len(df)} linhas do arquivo {os.path.basename(caminho_arquivo)}...")
    except FileNotFoundError:
        print(f"Erro: Arquivo não encontrado em '{caminho_arquivo}'.")
        return
    except Exception as e:
        print(f"Erro ao ler o arquivo CSV: {e}")
        return
        
    mapeamento_colunas = {
        'Original Part': 'partNumber',
        'Quantity': 'pack',
        'Stock': 'stock',
        'Subtotal': 'price',
        'Order List': 'sku',
        'Supplier Name': 'distributor_name',
        'Supplier Order Quantity': 'moq'
    }
    
    df = df.rename(columns=mapeamento_colunas)

    colunas_necessarias = ['partNumber', 'pack', 'stock', 'price', 'distributor_name', 'moq']
    if not all(coluna in df.columns for coluna in colunas_necessarias):
        print(f"ERRO: O arquivo CSV '{caminho_arquivo}' deve conter as colunas: 'Original Part', 'Quantity', 'Stock', 'Subtotal', 'Supplier Name', 'Supplier Order Quantity'")
        return
    
    distributor_name_from_file = None
    primeiro_indice_valido = df['distributor_name'].first_valid_index()
    
    if primeiro_indice_valido is not None:
        distributor_name_from_file = str(df.at[primeiro_indice_valido, 'distributor_name']).strip()
    
    if not distributor_name_from_file:
        print(f"Erro no arquivo '{os.path.basename(caminho_arquivo)}': Não foi possível encontrar um nome de distribuidor. Arquivo não processado.")
        return

    print(f"Distribuidor identificado para este arquivo: '{distributor_name_from_file}'")

    distribuidor_obj = session.query(Distributor).filter_by(name=distributor_name_from_file).first()
    if not distribuidor_obj:
        print(f"ERRO FATAL: O distribuidor '{distributor_name_from_file}' não está cadastrado. Cadastre-o e tente novamente.")
        return

    sucessos = 0
    falhas = 0

    for index, row in df.iterrows():
        try:
            partNumber = str(row['partNumber']).strip() if pd.notna(row['partNumber']) else ""
            
            if not partNumber:
                falhas += 1
                continue
            
            pack_val = pd.to_numeric(row['pack'], errors='coerce')
            if pd.isna(pack_val):
                falhas += 1
                continue
            pack = int(pack_val)
            
            price = 0.0
            stock = 0
            moq_val = pd.to_numeric(row['moq'], errors='coerce')

            if pd.notna(moq_val) and pack == int(moq_val):
                price_val_from_file = pd.to_numeric(row.get('price'), errors='coerce')
                if pd.notna(price_val_from_file):
                    price = float(price_val_from_file)
                    stock_val_from_file = pd.to_numeric(row.get('stock'), errors='coerce')
                    stock = int(stock_val_from_file) if pd.notna(stock_val_from_file) else 0
            
            sku = None
            if 'sku' in df.columns and pd.notna(row['sku']):
                sku_bruto = str(row['sku']).strip()
                partes_sku = sku_bruto.split()
                if len(partes_sku) > 1 and partes_sku[0].lower() == distributor_name_from_file.lower():
                    sku = " ".join(partes_sku[1:])
                else:
                    sku = sku_bruto
            
            produto = crud_produtos.adicionar_produto(partNumber=partNumber, pack=pack, brand=None, quiet=True)
            if not produto:
                falhas += 1
                continue
                
            dados = crud_dados.adicionar_dados_distribuidor(
                distributor_name=distributor_name_from_file,
                partNumber=partNumber,
                pack=pack,
                price=price,
                stock=stock,
                sku=sku,
                quiet=True
            )

            if dados:
                sucessos += 1
            else:
                falhas += 1

        except Exception as e:
            print(f"Linha {index + 2}: Erro inesperado durante o processamento - {e}. Pulando.")
            falhas += 1
            
    print(f"\n--- Processamento de '{os.path.basename(caminho_arquivo)}' Concluído ---")
    print(f"Registros de preço/estoque processados com sucesso: {sucessos}")
    print(f"Linhas com falha ou puladas: {falhas}")


def processar_pasta_distribuidores(caminho_da_pasta: str):
    """
    Varre uma pasta, encontra todos os arquivos .csv e os processa
    com a lógica de importação de dados de distribuidor (sem ASIN).
    """
    if not os.path.isdir(caminho_da_pasta):
        print(f"ERRO: O caminho '{caminho_da_pasta}' não é uma pasta válida.")
        return
    
    arquivos_csv = [f for f in os.listdir(caminho_da_pasta) if f.lower().endswith('.csv')]
    
    if not arquivos_csv:
        print(f"Nenhum arquivo .csv encontrado na pasta '{caminho_da_pasta}'.")
        return
        
    print(f"Encontrados {len(arquivos_csv)} arquivos CSV na pasta '{caminho_da_pasta}'.")
    
    for nome_arquivo in arquivos_csv:
        caminho_completo = os.path.join(caminho_da_pasta, nome_arquivo)
        print(f"\n========================================================")
        print(f"INICIANDO PROCESSAMENTO DO ARQUIVO: {nome_arquivo}")
        print(f"========================================================")
        processar_csv_distribuidor(caminho_completo)

# ===================================================================
#      FUNÇÃO DE IMPORTAÇÃO DE ASINs EM LOTE (MODIFICADA)
# ===================================================================

def processar_csv_asins(caminho_ou_buffer):
    """
    Processa um arquivo CSV contendo 'asin', 'partNumber' e 'pack'
    para adicionar novos ASINs e, se necessário, novos produtos.
    Retorna uma tupla com (sucessos, falhas, produtos_criados, ja_existiam).
    """
    try:
        df = pd.read_csv(caminho_ou_buffer, delimiter=',')
    except Exception:
        try:
            df = pd.read_csv(caminho_ou_buffer, delimiter=';')
        except Exception as e:
            print(f"Erro ao ler o arquivo CSV: {e}")
            return (0, 0, 0, 0)

    df.dropna(how='all', inplace=True)
    if df.empty:
        print("Arquivo CSV está vazio ou contém apenas linhas em branco.")
        return (0, 0, 0, 0)

    total_linhas = len(df)
    print(f"Lendo {total_linhas} linhas do arquivo...")
    
    mapeamento_colunas = { 'asin': 'asin', 'partNumber': 'partNumber', 'pack': 'pack' }
    df = df.rename(columns=mapeamento_colunas)

    colunas_necessarias = ['asin', 'partNumber', 'pack']
    if not all(coluna in df.columns for coluna in colunas_necessarias):
        print(f"ERRO: O arquivo CSV deve conter as colunas: 'asin', 'partNumber', 'pack'")
        return (0, 0, 0, 0)

    sucessos = 0
    falhas = 0
    produtos_criados = 0
    ja_existiam = 0 # NOVO CONTADOR

    for index, row in df.iterrows():
        try:
            asin = str(row['asin']).strip() if pd.notna(row['asin']) else ""
            partNumber = str(row['partNumber']).strip() if pd.notna(row['partNumber']) else ""
            pack_val = pd.to_numeric(row['pack'], errors='coerce')

            if not all([asin, partNumber]) or pd.isna(pack_val):
                print(f"Linha {index + 2}: Dados inválidos ou ausentes. Pulando.")
                falhas += 1
                continue
            
            pack = int(pack_val)
            produto_id_final = None

            produto_existente = session.query(Product).filter_by(partNumber=partNumber, pack=pack).first()

            if produto_existente:
                produto_id_final = produto_existente.id
            else:
                # REATIVANDO O LOG DETALHADO QUE VOCÊ GOSTOU
                print(f"Linha {index + 2}: Produto '{partNumber}' (Pack: {pack}) não encontrado. Cadastrando...")
                novo_produto = crud_produtos.adicionar_produto(partNumber=partNumber, pack=pack, brand=None, quiet=True)
                if novo_produto and novo_produto.id:
                    produto_id_final = novo_produto.id
                    produtos_criados += 1
                else:
                    print(f"Linha {index + 2}: Falha ao cadastrar novo produto. Pulando.")
                    falhas += 1
                    continue
            
            if produto_id_final:
                # AGORA A FUNÇÃO RETORNA DOIS VALORES
                fbm_obj, foi_criado = crud_asin.adicionar_asin(
                    product_id=produto_id_final,
                    asin=asin
                )
                
                # USANDO A NOVA LÓGICA DE CONTAGEM
                if fbm_obj:
                    if foi_criado:
                        sucessos += 1
                    else:
                        ja_existiam += 1
                else:
                    falhas += 1

        except Exception as e:
            print(f"Linha {index + 2}: Erro inesperado durante o processamento - {e}. Pulando.")
            falhas += 1

    # RELATÓRIO FINAL COMPLETO
    print(f"\n--- Processamento de ASINs Concluído ---")
    print(f"Total de linhas lidas: {total_linhas}")
    print(f"Novos produtos cadastrados: {produtos_criados}")
    print(f"Novos ASINs associados: {sucessos}")
    print(f"ASINs que já existiam: {ja_existiam}")
    print(f"Linhas com falha: {falhas}")
    return (sucessos, falhas, produtos_criados, ja_existiam)