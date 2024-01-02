from collections import namedtuple
import csv
import datetime
import os
from typing import Dict, List


class Transaction():

    DATE_FORMATS = ['%d/%m/%Y', '%d/%m/%y', '%Y-%m-%d', '%d.%m.%Y', '%d.%m.%y', '%d %b %Y', '%d %b %y']

    def parse_date(self, date: str) -> datetime:
        "Parse a date string into a datetime object as datetime object" 
        for format in Transaction.DATE_FORMATS:
            try:
                return datetime.datetime.strptime(date, format)
            except ValueError:
                pass

        raise Exception(f'Could not parse date {date}')
    

    def parse_amount(self, amount: str) -> float:
        "Parse an amount string into a float"
        return float(amount.strip())

    def __init__(self, date: str, amount: str, description: str) -> None:
        self.date: datetime.datetime = self.parse_date(date)
        self.amount = amount
        self.description = description

    def __repr__(self) -> str:
        return f'Transaction({self.date}, {self.amount}, {self.description})'

class CSVMapper():
    def __init__(self) -> None:
        # maps a column name to a list of possible column indices
        self.column_mappings: Dict[str, List[int]] = {}

    def auto_detect_columns(self, csv_data: List[List[str]]) -> None:
        prefixes = {
            'date': ['תאריך', 'date'],
            'amount': ['סכום', 'amount'],
            'description': ['תיאור', 'description', 'פעולה', 'action', 'הערות']
        }
        
        # detect the columns and map them to column indices
        for i in range(len(csv_data[0])):
            col_name = csv_data[0][i].strip()
            print ([ord(c) for c in col_name])
            found = False
            for prefix, options in prefixes.items():
                if any(col_name.startswith(option) for option in options):
                    self.column_mappings[prefix] = self.column_mappings.get(prefix, []) + [i]
                    found = True

            if not found:
                print(f'Column {col_name} was not recognized')

        # sanity check
        for role, cols in self.column_mappings.items():
            # only the description column can have multiple columns
            if role == 'description':
                continue

            if len(cols) > 1:
                raise Exception(f'Column {role} was found in multiple columns: {cols}')
            
        print ([ord(c) for c in "פעולה"])

Configuration = namedtuple('Configuration', ['balance', 'username', 'database_path', 'csv_file_path'])

def parse_command_line_args():
    import argparse

    parser = argparse.ArgumentParser(description='Import new user from a CSV file')
    parser.add_argument('-b', '--adjust_balance', type=int, help='Adjust balance', required=False)
    parser.add_argument('-c', '--create', action='store_true', help='Create a new database', required=False)
    parser.add_argument('username', type=str, help='Username to be used in the database')
    parser.add_argument('database_path', type=str, help='Path to the database')
    parser.add_argument('csv_file_path', type=str, help='Path to the CSV file')

    parsing_result =  parser.parse_args()
    
    return Configuration(balance=parsing_result.adjust_balance, 
        username=parsing_result.username, database_path=parsing_result.database_path, 
        csv_file_path=parsing_result.csv_file_path)

def read_csv_file(path: str) -> List[List[str]]:
    # check if file exists and is readable
    if not os.path.isfile(path):
        raise Exception(f'File {path} does not exist')
    
    if not os.access(path, os.R_OK):
        raise Exception(f'File {path} is not readable')
    
    # read file
    with open(path, 'r', encoding='utf-8-sig') as f: # utf-8-sig is used to remove the BOM
        csv_reader = csv.reader(f, delimiter=',')
        l = list(csv_reader)
        print(f"Completed reading {len(l)} lines from {path}")
        return l

def main(config: Configuration):
    print(f'Importing user {config.username} with balance {config.balance} to database {config.database_path}')
    # read csv file
    csv_data = read_csv_file(config.csv_file_path)
    print(csv_data[0:3]) # print first 3 lines XXX debug
    
    # detect columns
    mapper = CSVMapper()
    mapper.auto_detect_columns(csv_data)
    print(mapper.column_mappings) # XXX debug

    # convert columns to objects and validate
    transactions = []
    for i in range(1, len(csv_data)):
        row = csv_data[i]
        date = row[mapper.column_mappings['date'][0]]
        amount = row[mapper.column_mappings['amount'][0]]
        description = " - ".join([row[j].strip() for j in mapper.column_mappings['description'] if row[j].strip() != '' ])
        try: 
            transactions.append(Transaction(date, amount, description))
        except Exception as e:
            print(f'Error parsing row {i}: {e}')
            print(row)
            return

    for t in transactions:
        print(t)
    # add user to database

    # add transactions to database








if __name__ == '__main__':
    main(parse_command_line_args())