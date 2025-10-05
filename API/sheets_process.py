# sheets_process.py

import pandas as pd
from database import session, FBM, Product
import google_sheets # Importa sua biblioteca de conexão com o Sheets

def atualizar_planilha_fbm():
    """
    Busca os dados da tabela FBM, formata-os e os envia para a planilha do Google Sheets.
    Esta função encapsula a lógica que estava no seu arquivo 'teste.py'.
    """
    print("Iniciando processo de atualização do Google Sheets...")
    
    try:
        # 1. Buscar os dados do banco de dados local
        print("Buscando dados da tabela FBM no banco de dados local...")
        query = session.query(FBM, Product).join(Product, FBM.product_id == Product.id)
        resultados = query.all()
        
        if not resultados:
            print("Nenhum dado encontrado na tabela FBM para atualizar.")
            return

        # 2. Preparar os dados para o formato de DataFrame do Pandas
        dados_para_df = []
        for fbm, produto in resultados:
            dados_para_df.append({
                'asin': fbm.asin,
                'partNumber': produto.partNumber,
                'pack': produto.pack,
                'current_price': fbm.current_price,
                'supplier': fbm.supplier,
                'stock': fbm.stock,
                'prime_stock': fbm.prime_stock,
                'all_stock': fbm.all_stock,
                'promotion': fbm.promotion,
                # Adicione quaisquer outros campos do FBM ou Produto que desejar
            })
            
        df = pd.DataFrame(dados_para_df)
        print(f"{len(df)} registros preparados para envio.")

        # 3. Definir os nomes da planilha e da aba (worksheet)
        # IMPORTANTE: Altere estes nomes se forem diferentes na sua conta Google
        NOME_PLANILHA = 'Controle de Estoque'
        NOME_ABA = 'FBM'

        # 4. Enviar o DataFrame para o Google Sheets usando sua função
        print(f"Enviando dados para a planilha '{NOME_PLANILHA}', aba '{NOME_ABA}'...")
        google_sheets.update_worksheet_from_dataframe(df, NOME_PLANILHA, NOME_ABA)
        
        print("Atualização do Google Sheets concluída com sucesso!")

    except Exception as e:
        print(f"Ocorreu um erro durante a atualização do Google Sheets: {e}")