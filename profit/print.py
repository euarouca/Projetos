import pyautogui  
import os
from datetime import datetime

def tirar_print(asin, pais):
    directory_path = r"C:\Users\lucas\OneDrive\Imagens\prints\{}\{}".format(datetime.now().date(), asin)

    # Verifique se o diretório já existe, se não, crie-o
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)

    # Tire uma captura de tela
    shot = pyautogui.screenshot()

    # Salve a captura de tela dentro do diretório criado
    file_path = os.path.join(directory_path, f'{pais}.png')
    if os.path.exists(file_path):
        file_path = os.path.join(directory_path, f'2_{pais}.png')
        if os.path.exists(file_path):
            file_path = os.path.join(directory_path, f'3_{pais}.png')
            if os.path.exists(file_path):
                file_path = os.path.join(directory_path, f'4_{pais}.png')
    shot.save(file_path)

def tirar_print_unico(asin, pais):
    if pais[2]:
        sigla_pais = 'CA'
    if pais[4]:
        sigla_pais = 'MX'
    if pais[6]:
        sigla_pais = 'EU'
    
    directory_path = r"C:\Users\lucas\OneDrive\Imagens\prints\{}\{}".format(datetime.now().date(), asin)

    # Verifique se o diretório já existe, se não, crie-o
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)

    # Tire uma captura de tela
    shot = pyautogui.screenshot()

    # Salve a captura de tela dentro do diretório criado
    file_path = os.path.join(directory_path, f'{sigla_pais}.png')
    if os.path.exists(file_path):
        file_path = os.path.join(directory_path, f'2_{sigla_pais}.png')
        if os.path.exists(file_path):
            file_path = os.path.join(directory_path, f'3_{sigla_pais}.png')
            if os.path.exists(file_path):
                file_path = os.path.join(directory_path, f'4_{sigla_pais}.png')
    shot.save(file_path)
    

def tirar_eua(asin):
    
    directory_path = r"C:\Users\lucas\OneDrive\Imagens\prints\{}\{}".format(datetime.now().date(), asin)

    # Verifique se o diretório já existe, se não, crie-o
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)

    # Tire uma captura de tela
    shot = pyautogui.screenshot()

    # Salve a captura de tela dentro do diretório criado
    file_path = os.path.join(directory_path, f'EU.png')
    if os.path.exists(file_path):
        file_path = os.path.join(directory_path, f'2_EU.png')
        if os.path.exists(file_path):
            file_path = os.path.join(directory_path, f'3_EU.png')
            if os.path.exists(file_path):
                file_path = os.path.join(directory_path, f'4_EU.png')
    shot.save(file_path)
    
def tirar_can(asin):
    
    directory_path = r"C:\Users\lucas\OneDrive\Imagens\prints\{}\{}".format(datetime.now().date(), asin)

    # Verifique se o diretório já existe, se não, crie-o
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)

    # Tire uma captura de tela
    shot = pyautogui.screenshot()

    # Salve a captura de tela dentro do diretório criado
    file_path = os.path.join(directory_path, f'CA.png')
    if os.path.exists(file_path):
        file_path = os.path.join(directory_path, f'2_CA.png')
        if os.path.exists(file_path):
            file_path = os.path.join(directory_path, f'3_CA.png')
            if os.path.exists(file_path):
                file_path = os.path.join(directory_path, f'4_CA.png')
    shot.save(file_path)