from collections import namedtuple
import csv
import os
from typing import List

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
    with open(path, 'r', encoding='utf-8') as f:
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

    # convert columns to objects and validate

    # add user to database

    # add transactions to database








if __name__ == '__main__':
    main(parse_command_line_args())