import pandas as pd

def ChemicalPercentageComposition(report_path, list_chemistry_path, mode='full'):
    
    #Читаем исходные данные
    full_list_chemistry = pd.read_excel(list_chemistry_path)
    report_data = pd.read_excel(report_path, index_col = 0)
    
    valid_modes = {"full", "partial"}
    if mode not in valid_modes:
        raise ValueError(f"mode должен быть одним из: {valid_modes}")

    #Создаем новую таблицу и группируем минералы
    minerals_data = report_data.groupby('Minerals', as_index=False)['Size'].sum()
    minerals_data['Other'] = 0.0
    total_size = 0.0

    #Ищем химический состав для каждого минерала
    for mineral in minerals_data['Minerals']:
        find_mineral = full_list_chemistry.loc[full_list_chemistry['Mineral Name (plain)'] == mineral]
        if len(find_mineral) > 0:
            elements = find_mineral['Chemistry Elements'].values[0].split()
            for element in elements:
                if element not in minerals_data.columns:
                    minerals_data[element] = 0.0
                element_amount = full_list_chemistry.loc[full_list_chemistry['Mineral Name (plain)'] == mineral, element].values[0] #переименовать
                minerals_data.loc[minerals_data['Minerals'] == mineral, element] = element_amount
        else:
            minerals_data.loc[minerals_data['Minerals'] == mineral, "Other"] = 100

    #При частичном анализе отбрасываем нераспознанные минералы
    if mode == 'partial':
        minerals_data = minerals_data[minerals_data['Other'] == 0]
        minerals_data = minerals_data.drop(columns=['Other'])
        
    #Считаем проценты
    total_size = minerals_data['Size'].sum()
    minerals_data['Size'] = minerals_data['Size'] / total_size * 100
    for element in minerals_data.columns[2:]:
        minerals_data[element] = minerals_data[element] * minerals_data['Size'] / 100        

    #Создание строчки с общим составом
    total_row = pd.DataFrame()
    total_row['Minerals'] = ['Total']
    for column in minerals_data.columns:
        if column != 'Minerals':
            total_row[column] = minerals_data[column].sum()
    minerals_data = pd.concat([minerals_data, total_row], ignore_index=True)

    #Округление       
    minerals_data = minerals_data.round(3)

    #Сортировка химических элементов
    all_columns = list(minerals_data.columns)
    first_two_columns = all_columns[:2]
    elements_columns = sorted([col for col in all_columns[2:] if len(col) <= 2])
    remaining_columns = sorted([col for col in all_columns[2:] if len(col) > 2])
    final_columns_order = first_two_columns + elements_columns + remaining_columns
    minerals_data = minerals_data.reindex(columns=final_columns_order)

    #Запись результата в файл
    with pd.ExcelWriter(report_path, engine='openpyxl', mode='a') as writer:
        workbook = writer.book
        if 'Sheet2' in workbook.sheetnames:
                workbook.remove(workbook['Sheet2'])
        minerals_data.to_excel(writer, sheet_name='Sheet2', index=True)
        worksheet = writer.sheets['Sheet2']
        worksheet.column_dimensions['B'].width = 20

if __name__ == '__main__':
    ChemicalPercentageComposition('Report.xlsx', 'Full_list_chemistry.xlsx', 'full')
