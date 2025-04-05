import requests
import csv
import os

def upload_to_sheets(scriptdir, key, log_func=print, column:str='2', sheet_tab:str='dumpster', sheet_link:str='https://docs.google.com/spreadsheets/d/1eb5lkWkPnqGi8KLqYscoZekyKhHtvmZYG0PNK_Kt2dY/edit'):
    log_func(f'logging match {key}...')

    with open(f'{scriptdir}/matches/{key}/{key}_cycles.csv', mode='r', encoding='utf-8') as file:
        reader = csv.reader(file)  # Read CSV as raw rows
        next(reader)  # Skip the header row
        csv_data = [",".join(row) for row in reader]

    for row in csv_data:
        your_data_here = row
        url = f'https://script.google.com/macros/s/AKfycbxj9pjLFR1K_3bG3mgi50MYmYha7iH2D8bIUcsHXfz8l8Kq1_h8o3KikmPb6JDyFEgv3Q/exec?csvData={your_data_here}&sheetURL={sheet_link}&sheetName={sheet_tab}&colNumber={column}'
        response = requests.get(url)
        # log_func(response.text)


# if __name__ == "__main__":
#     scriptdir = os.path.dirname(os.path.abspath(__file__))
#     with open(f'{scriptdir}/data/current.txt') as file:
#         key = file.read()
#     upload_to_sheets(scriptdir, key)

