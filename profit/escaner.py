import cv2
import os
import pyautogui
import pytesseract
from PIL import Image


def tirar_print():
    directory_path = r"C:\Users\lucas\OneDrive\Documentos\Projetos\profit\scan"
    # Tire uma captura de tela
    shot = pyautogui.screenshot()
    # Salve a captura de tela dentro do diretório criado
    file_path = os.path.join(directory_path, 'print.png')
    shot.save(file_path)

def reconhecer():
    tirar_print()
    # ler imagem
    imagem = cv2.imread(r'profit\scan\print.png')

    # extrair texto da imagem
    caminho = r'C:\Users\lucas\AppData\Local\Programs\Tesseract-OCR'
    pytesseract.pytesseract.tesseract_cmd = caminho + r'\tesseract.exe'
    texto =  pytesseract.image_to_string(imagem)
    
    if 'Repricing Compete' in texto:
        return False
    
    else:
        return True
