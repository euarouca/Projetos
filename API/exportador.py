# exportador.py

import os
import csv
from database import session, Product

def exportar_produtos_em_lote(caminho_pasta: str):
    """
    Exporta todos os produtos da tabela 'product' para arquivos CSV.
    As colunas são: Original Part, Quantity.
    """
    print("\n--- INICIANDO EXPORTAÇÃO DE PRODUTOS ---")

    try:
        os.makedirs(caminho_pasta, exist_ok=True)
    except OSError as e:
        print(f"Erro ao criar o diretório '{caminho_pasta}': {e}")
        return

    offset = 0
    limit = 1000  # Mantém o processamento em lotes para eficiência
    file_number = 1
    registros_exportados = 0
    headers = ['Original Part', 'Quantity']

    while True:
        # A consulta agora é simples, diretamente na tabela Product
        lote_produtos = session.query(Product).order_by(Product.id).offset(offset).limit(limit).all()

        if not lote_produtos:
            print("\nNenhum produto a mais para exportar.")
            break

        nome_arquivo = os.path.join(caminho_pasta, f"export_produtos_{file_number}.csv")
        print(f"Exportando {len(lote_produtos)} produtos para o arquivo: {nome_arquivo}")

        try:
            with open(nome_arquivo, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(headers)

                # Itera sobre o lote de produtos e escreve no CSV
                for produto in lote_produtos:
                    writer.writerow([produto.partNumber, produto.pack])
            
            registros_exportados += len(lote_produtos)

        except IOError as e:
            print(f"Erro ao escrever no arquivo '{nome_arquivo}': {e}")
            break
            
        offset += limit
        file_number += 1

    print("\n--- EXPORTAÇÃO CONCLUÍDA ---")
    print(f"Total de produtos exportados: {registros_exportados}")
    print(f"Arquivos salvos em: {os.path.abspath(caminho_pasta)}")