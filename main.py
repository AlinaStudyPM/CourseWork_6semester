import os
import io
import pandas as pd
from PyPDF2 import PdfReader, PdfWriter
from pdfminer.high_level import extract_pages, extract_text
from pdfminer.layout import LTTextContainer, LTChar, LTRect, LTFigure
import pdfplumber
from PIL import Image
from pdf2image import convert_from_path 
import pytesseract
import requests
from langdetect import detect

def get_pdfs_paths_from_folder(folder_url:str):
    paths_to_files = []

    if not os.path.exists(folder_url):
        raise FileNotFoundError(f"Папка {folder_url} не найдена.")
    
    for filename in os.listdir(folder_url):
        if filename.endswith(".pdf"):
            paths_to_files.append(os.path.join(folder_url, filename))
    return paths_to_files

def convert_pdf_to_text(file_path:str):
    with open(file_path, 'rb') as pdf_file:
        reader = PdfReader(pdf_file)
        texts = []
        for page in reader.pages:
            # Извлечение текста
            page_text = page.extract_text()
            if page_text:
                texts.append(page_text.replace("\n", " "))
            # Извлечение изображений и их распознавание с помощью OCR
            if '/XObject' in page['/Resources']:
                xObject = page['/Resources']['/XObject'].get_object()
                for obj in xObject:
                    if xObject[obj]['/Subtype'] == '/Image':
                        image = xObject[obj]
                        image_data = image.get_data()
                        img = Image.open(io.BytesIO(image_data))

                        ocr_text = pytesseract.image_to_string(img, lang='rus+eng')
                        texts.append(ocr_text.replace("\n", " "))
        '''  
        # Извлечение таблиц с использованием pdfplumber
        with pdfplumber.open(pdf_file.stream) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables()
                for table in tables:
                    # Преобразование таблицы в текстовый формат
                    table_text = "\n".join(["\t".join(row) for row in table])
                    texts.append(table_text)
        '''
    return texts

if __name__ == "__main__":
    #pdf_path = 'InputFiles/1955_Смирнов СС_Зона окисления сульфидных месторожденийgeokniga-smirnov-cc-zona-okisleniya-sulfidnyh-mestorozhdeniy-1955.pdf'
    folder_path = 'InputFiles'
    for file_path in get_pdfs_paths_from_folder(folder_path):
        print(f"ФАЙЛ {file_path}\n")
        texts = simple_convert_pdf_to_text(file_path)
        print(texts)
