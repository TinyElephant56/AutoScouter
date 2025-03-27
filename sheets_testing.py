import requests
import csv
import os
scriptdir = os.path.dirname(os.path.abspath(__file__))
with open(f'{scriptdir}/current.txt') as file:
    key = file.read()

column = '2'
sheet_tab = 'dumpster'
sheet_link = 'https://docs.google.com/spreadsheets/d/1eb5lkWkPnqGi8KLqYscoZekyKhHtvmZYG0PNK_Kt2dY/edit'

with open(f'{scriptdir}/{key}_cycles.csv', mode='r', encoding='utf-8') as file:
    reader = csv.reader(file)  # Read CSV as raw rows
    next(reader)  # Skip the header row
    csv_data = [",".join(row) for row in reader]

for row in csv_data:
    your_data_here = row
    url = f'https://script.google.com/macros/s/AKfycbxj9pjLFR1K_3bG3mgi50MYmYha7iH2D8bIUcsHXfz8l8Kq1_h8o3KikmPb6JDyFEgv3Q/exec?csvData={your_data_here}&sheetURL={sheet_link}&sheetName={sheet_tab}&colNumber={column}'
    response = requests.get(url)
    print(response.text)