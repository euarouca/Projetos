# google_sheets.py

import gspread
from gspread_dataframe import set_with_dataframe
import pandas as pd

# Define o escopo da API e o caminho para o arquivo de credenciais
SCOPE = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]
SERVICE_ACCOUNT_FILE = 'service_account.json'

def get_connection():
    """
    Estabelece conexão com a API do Google Sheets usando as credenciais.
    """
    try:
        gc = gspread.service_account(filename=SERVICE_ACCOUNT_FILE, scopes=SCOPE)
        return gc
    except FileNotFoundError:
        print(f"Erro: Arquivo de credenciais '{SERVICE_ACCOUNT_FILE}' não encontrado.")
        print("Certifique-se de que o arquivo está no mesmo diretório do projeto.")
        return None
    except Exception as e:
        print(f"Erro ao conectar com a API do Google: {e}")
        return None

def update_worksheet_from_dataframe(df: pd.DataFrame, spreadsheet_name: str, worksheet_name: str):
    """
    Limpa uma aba específica de uma planilha e a preenche com os dados de um DataFrame.
    """
    gc = get_connection()
    if not gc:
        return

    try:
        # Abre a planilha pelo nome
        spreadsheet = gc.open(spreadsheet_name)
        
        # Seleciona a aba (worksheet) pelo nome
        try:
            worksheet = spreadsheet.worksheet(worksheet_name)
        except gspread.WorksheetNotFound:
            # Se a aba não existe, cria uma nova
            print(f"Aba '{worksheet_name}' não encontrada. Criando uma nova...")
            worksheet = spreadsheet.add_worksheet(title=worksheet_name, rows="1000", cols="20")

        # Limpa todos os dados existentes na aba
        print(f"Limpando dados da aba '{worksheet_name}'...")
        worksheet.clear()
        
        # Escreve o DataFrame na aba, começando da célula A1
        print("Preenchendo a aba com os novos dados...")
        set_with_dataframe(worksheet, df, include_index=False, allow_formulas=True)
        
        print("Dados escritos com sucesso no Google Sheets.")
        
    except gspread.SpreadsheetNotFound:
        print(f"Erro: Planilha com o nome '{spreadsheet_name}' não foi encontrada na sua conta Google Drive.")
    except Exception as e:
        print(f"Um erro ocorreu ao interagir com a planilha: {e}")