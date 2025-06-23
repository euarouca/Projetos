import pandas as pd
import crud_produtos
import crud_asin
import crud_dados
import os
from database import session, Distributor

def processar_csv_unificado(caminho_arquivo: str):
    """
    Processa um arquivo CSV unificado, adicionando ou atualizando dados no banco.
    - Lê o nome do distribuidor uma vez por arquivo.
    - Se 'pack' e 'moq' forem inválidos ou diferentes, preço e estoque são zerados.
    - Se 'Subtotal' estiver vazio, preço e estoque são zerados.
    - Captura o SKU da coluna 'Order List' (opcional) com tratamento especial.
    - Opera em modo silencioso.
    """
    try:
        # Tenta ler com diferentes delimitadores para maior flexibilidade
        try:
            df = pd.read_csv(caminho_arquivo, delimiter=',')
        except Exception:
            df = pd.read_csv(caminho_arquivo, delimiter=';')
        
        df.dropna(how='all', inplace=True)
        if df.empty:
            print(f"Arquivo '{os.path.basename(caminho_arquivo)}' está vazio ou contém apenas linhas em branco. Pulando.")
            return

        print(f"Lendo {len(df)} linhas do arquivo {os.path.basename(caminho_arquivo)}...")
    except FileNotFoundError:
        print(f"Erro: Arquivo não encontrado em '{caminho_arquivo}'.")
        return
    except Exception as e:
        print(f"Erro ao ler o arquivo CSV: {e}")
        return
        
    mapeamento_colunas = {
        'asin': 'asin',
        'Original Part': 'partNumber',
        'Quantity': 'pack',
        'Stock': 'stock',
        'Subtotal': 'price', # Atualizado de 'Total Price' para 'Subtotal'
        'Order List': 'sku',
        'Supplier Name': 'distributor_name',
        'Supplier Order Quantity': 'moq'
    }
    
    df = df.rename(columns=mapeamento_colunas)

    colunas_necessarias = ['asin', 'partNumber', 'pack', 'stock', 'price', 'distributor_name', 'moq']
    if not all(coluna in df.columns for coluna in colunas_necessarias):
        # Mensagem de erro atualizada para refletir a nova coluna
        print(f"ERRO: O arquivo CSV '{caminho_arquivo}' deve conter as colunas: 'asin', 'Original Part', 'Quantity', 'Stock', 'Subtotal', 'Supplier Name', 'Supplier Order Quantity'")
        return
    
    distributor_name_from_file = None
    primeiro_indice_valido = df['distributor_name'].first_valid_index()
    
    if primeiro_indice_valido is not None:
        distributor_name_from_file = str(df.at[primeiro_indice_valido, 'distributor_name']).strip()
    
    if not distributor_name_from_file:
        print(f"Erro no arquivo '{os.path.basename(caminho_arquivo)}': Não foi possível encontrar um nome de distribuidor ('Supplier Name') válido. Arquivo não processado.")
        return

    print(f"Distribuidor identificado para este arquivo: '{distributor_name_from_file}'")

    distribuidor_obj = session.query(Distributor).filter_by(name=distributor_name_from_file).first()
    if not distribuidor_obj:
        print(f"ERRO FATAL: O distribuidor '{distributor_name_from_file}' não está cadastrado no sistema.")
        print("Cadastre o distribuidor e tente novamente. O processamento deste arquivo foi abortado.")
        return

    sucessos = 0
    falhas = 0

    # --- Itera sobre cada linha do arquivo ---
    for index, row in df.iterrows():
        try:
            partNumber = str(row['partNumber']).strip() if pd.notna(row['partNumber']) else ""
            asin = str(row['asin']).strip() if pd.notna(row['asin']) else ""
            
            if not all([partNumber, asin]):
                falhas += 1
                continue
            
            # --- Conversão robusta para inteiros ---
            pack_val = pd.to_numeric(row['pack'], errors='coerce')

            # 'pack' é essencial para definir o produto. Se for inválido, não podemos prosseguir com esta linha.
            if pd.isna(pack_val):
                falhas += 1
                continue
                
            pack = int(pack_val)
            
            # --- LÓGICA DE PREÇO E ESTOQUE BASEADA NA COMPARAÇÃO DE QUANTIDADES ---
            price = 0.0
            stock = 0

            moq_val = pd.to_numeric(row['moq'], errors='coerce')

            # A condição para obter preço/estoque é: moq deve ser um número válido E deve ser igual ao pack.
            if pd.notna(moq_val) and pack == int(moq_val):
                # Se forem válidos e iguais, processa o preço e estoque do arquivo
                price_val_from_file = pd.to_numeric(row.get('price'), errors='coerce')
                if pd.notna(price_val_from_file):
                    price = float(price_val_from_file)
                    stock_val_from_file = pd.to_numeric(row.get('stock'), errors='coerce')
                    stock = int(stock_val_from_file) if pd.notna(stock_val_from_file) else 0
            # Em todos os outros casos (moq inválido, pack != moq, ou preço vazio), price e stock permanecem 0.
            
            sku = None
            if 'sku' in df.columns and pd.notna(row['sku']):
                sku_bruto = str(row['sku']).strip()
                partes_sku = sku_bruto.split()
                if len(partes_sku) > 1 and partes_sku[0].lower() == distributor_name_from_file.lower():
                    sku = " ".join(partes_sku[1:])
                else:
                    sku = sku_bruto
            
            # Adicionar produto (quiet=True para menos logs)
            produto = crud_produtos.adicionar_produto(partNumber=partNumber, pack=pack, brand=None, quiet=True)
            if not produto:
                falhas += 1
                continue

            fbm = crud_asin.adicionar_asin(product_id=produto.id, asin=asin)
            if not fbm:
                falhas += 1
                continue
                
            # Adicionar/Atualizar dados do distribuidor (quiet=True para menos logs)
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
            # Captura exceções mais amplas para evitar que o loop pare
            print(f"Linha {index + 2}: Erro inesperado durante o processamento - {e}. Pulando.")
            falhas += 1
            
    print(f"\n--- Processamento de '{os.path.basename(caminho_arquivo)}' Concluído ---")
    print(f"Registros processados (criados ou atualizados) com sucesso: {sucessos}")
    print(f"Linhas com falha ou puladas: {falhas}")


def processar_pasta_unificada(caminho_da_pasta: str):
    """
    Varre uma pasta, encontra todos os arquivos .csv e os processa com a lógica unificada.
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
        processar_csv_unificado(caminho_completo)
