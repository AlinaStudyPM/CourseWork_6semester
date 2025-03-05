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

def crop_image(element, pageObj):
    [image_left, image_top, image_right, image_bottom] = [element.x0,element.y0,element.x1,element.y1] 
    pageObj.mediabox.lower_left = (image_left, image_bottom)
    pageObj.mediabox.upper_right = (image_right, image_top)
    cropped_pdf_writer = PdfWriter()
    cropped_pdf_writer.add_page(pageObj)
    with open('cropped_image.pdf', 'wb') as cropped_pdf_file:
        cropped_pdf_writer.write(cropped_pdf_file)
def convert_to_images(input_file):
    images = convert_from_path(input_file)
    image = images[0]
    output_file = "PDF_image.png"
    image.save(output_file, "PNG")
def image_to_text(image_path):
    img = Image.open(image_path)
    text = pytesseract.image_to_string(img, lang='rus+eng')
    return text

def extract_table(pdf_path, page_num, table_num):
    pdf = pdfplumber.open(pdf_path)
    table_page = pdf.pages[page_num]
    table = table_page.extract_tables()[table_num]
    return table
def table_converter(table):
    table_string = ''
    for row_num in range(len(table)):
        row = table[row_num]
        cleaned_row = [item.replace('\n', ' ') if item is not None and '\n' in item else 'None' if item is None else item for item in row]
        table_string+=('|'+'|'.join(cleaned_row)+'|'+'\n')
    table_string = table_string[:-1]
    return table_string

def convert_pdf_to_text(file_path:str):
    texts = []
    with open(file_path, 'rb') as pdfFileObj:
        pdfReaded = PdfReader(pdfFileObj)
        for pagenum, page in enumerate(extract_pages(file_path)):
            pageObj = pdfReaded.pages[pagenum]

            # Находим таблицы
            table_num = 0
            first_element= True
            table_extraction_flag= False
            pdf = pdfplumber.open(file_path)
            page_tables = pdf.pages[pagenum]
            tables = page_tables.find_tables()

            page_elements = []
            for element in page._objs:
                y_coordinate = element.y1
                page_elements.append((y_coordinate, element))
            page_elements.sort(key=lambda item: item[0], reverse=True)

            for i,component in enumerate(page_elements):
                pos= component[0]
                element = component[1]
                # Обрабатываем текстовые элементы
                if isinstance(element, LTTextContainer):
                    if table_extraction_flag == False:
                        text = element.get_text().replace("\n", " ")
                        texts.append(text)
                    else:
                        # Пропускаем текст, находящийся в таблице
                        pass
                # Обрабатываем изображения
                if isinstance(element, LTFigure):
                    crop_image(element, pageObj)
                    convert_to_images('cropped_image.pdf')
                    image_text = image_to_text('PDF_image.png').replace("\n", " ")
                    texts.append(image_text)
                # Обрабатываем таблицы
                if isinstance(element, LTRect):
                    # Если первый прямоугольный элемент
                    if first_element == True and (table_num+1) <= len(tables):
                        lower_side = page.bbox[3] - tables[table_num].bbox[3]
                        upper_side = element.y1 
                        table = extract_table(file_path, pagenum, table_num)
                        table_string = table_converter(table).replace("\n", " ")
                        texts.append(table_string)
                    # Проверяем, извлекли ли мы уже таблицы из этой страницы
                    if element.y0 >= lower_side and element.y1 <= upper_side:
                        pass
                    elif not isinstance(page_elements[i+1][1], LTRect):
                        table_extraction_flag = False
                        first_element = True
                        table_num+=1
    return texts

if __name__ == "__main__":
    #pdf_path = 'InputFiles/1955_Смирнов СС_Зона окисления сульфидных месторожденийgeokniga-smirnov-cc-zona-okisleniya-sulfidnyh-mestorozhdeniy-1955.pdf'
    folder_path = 'InputFiles'
    for file_path in get_pdfs_paths_from_folder(folder_path):
        print(f"ФАЙЛ {file_path}\n")
        texts = convert_pdf_to_text(file_path)
        print(texts)
