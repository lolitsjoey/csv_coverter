import os
import sys
import uuid

from munch import Munch
import numpy as np
import pandas as pd
import argparse
from pathlib import Path


class CSV_FORMAT:
    def __init__(self):
        self.HEADER_INDICATOR = 'Account Code'
        self.TOTAL_INDICATOR = 'Total'

        # Column Names
        self.ACCOUNT_CODE = 'Account Code'
        self.ACCOUNT = 'Account'
        self.CREDIT_COL = 'Credit - Year to date'
        self.DEBIT_COL = 'Debit - Year to date'
        self.ACCOUNT_TYPE = 'Account Type'

        self.COL_NAMES = [
            self.ACCOUNT_CODE,
            self.ACCOUNT,
            self.CREDIT_COL,
            self.DEBIT_COL,
            self.ACCOUNT_TYPE
        ]


csv_format = CSV_FORMAT()


def check_column_names_and_return_date(csv_obj):
    actual_column_names = csv_obj.columns

    assumed_date_column = None

    for defined_col_name in csv_format.COL_NAMES:
        if defined_col_name not in actual_column_names:
            print(f"Csv appears to be missing {defined_col_name}")

    for actual_column_name in actual_column_names:
        if actual_column_name not in csv_format.COL_NAMES:
            if assumed_date_column is None:
                assumed_date_column = actual_column_name
                print(f"Assuming the date columns is {assumed_date_column}")
            else:
                print(f"Csv appears to be extra columns {actual_column_name},"
                      f" Attempting to continue...")
    return assumed_date_column


def reads_csvs_from_folder_finding_header(input_folder):
    list_of_csvs = []
    list_of_csv_paths = []
    for csv_file_path in os.listdir(input_folder):
        csv_file_path_full = Path(input_folder, csv_file_path)
        list_of_csv_paths.append(str(csv_file_path_full))

        original_csv = pd.read_excel(csv_file_path_full)

        header_idx = None
        for idx, row in original_csv.iterrows():
            if csv_format.HEADER_INDICATOR in row.values:
                header_idx = idx
                break

        if header_idx is None:
            print(f"Cannot find header, no '{csv_format.HEADER_INDICATOR}' in rows, "
                  f"please change HEADER_INDICATOR in CSV_FORMAT class")
            sys.exit(1)

        original_csv = pd.read_excel(Path(input_folder, csv_file_path), header=header_idx)
        original_csv.columns = original_csv.iloc[0, :]
        original_csv = original_csv.iloc[1::, :].copy()
        list_of_csvs.append(original_csv)

    print(f"Found {list_of_csv_paths} csvs.")
    return list_of_csvs, list_of_csv_paths


def get_args():
    # Create an ArgumentParser object
    parser = argparse.ArgumentParser(description='Program to format csv files')

    # Add an example argument
    parser.add_argument('--input_folder', type=str, default='./files_to_format',
                        help='This is the relative path to the file')

    # Parse the command-line arguments
    args = parser.parse_args()
    args.input_folder = Path(args.input_folder)
    # Access the example argument and use it in your code
    return args


def format_csv(csv_list, csv_paths):
    output_csvs = []
    output_paths = []

    for csv_obj, csv_path in list(zip(csv_list, csv_paths)):
        check_column_names_and_return_date(csv_obj)

        # Remove NaNs
        csv_obj[csv_format.DEBIT_COL] = csv_obj[csv_format.DEBIT_COL].fillna(0)
        csv_obj[csv_format.CREDIT_COL] = csv_obj[csv_format.CREDIT_COL].fillna(0)

        csv_obj['output_value'] = csv_obj[csv_format.DEBIT_COL] + -1 * csv_obj[csv_format.CREDIT_COL]
        csv_obj['output_value'] = csv_obj['output_value'].round(2)

        total_idx = None
        for idx, row in csv_obj.iterrows():
            if csv_format.TOTAL_INDICATOR in row.values:
                total_idx = idx
                break

        if total_idx is None:
            print(f"Cannot find total, no '{csv_format.TOTAL_INDICATOR}' in rows, "
                  f"please change TOTAL_INDICATOR in CSV_FORMAT class")
            sys.exit(1)

        csv_obj.drop(total_idx, inplace=True)

        if sum(csv_obj['output_value']) > 0.001:
            print(f"Credit and Debit don't sum to zero, can't format {csv_path}")
            continue

        output_csvs.append(csv_obj)
        output_paths.append(csv_path)

    print(f"Successfully formatted: \n{output_paths}")
    return output_csvs, output_paths


def build_output(f_csvs, f_paths):
    output_csvs = []

    for f_csv, f_path in zip(f_csvs, f_paths):
        first_column = f_csv['output_value']
        second_column = np.full(len(f_csv), np.nan)
        third_column = f_csv[csv_format.ACCOUNT]
        fourth_column = np.full(len(f_csv), np.nan)
        fifth_column = f_csv[csv_format.ACCOUNT_CODE]

        output_csv = pd.DataFrame()
        output_csv['first_column'] = first_column
        output_csv['second_column'] = second_column
        output_csv['third_column'] = third_column
        output_csv['fourth_column'] = fourth_column
        output_csv['fifth_column'] = fifth_column

        output_csv.to_excel(
            Path(
                f"./formatted_files/{Path(f_path).name}",
            ),
            index=False,
            header=False,
        )
        output_csvs.append(output_csv)
    return output_csvs


def main(input_folder):
    csv_list, csv_paths = reads_csvs_from_folder_finding_header(input_folder)
    formatted_csvs, formatted_csv_paths = format_csv(csv_list, csv_paths)
    output_csvs = build_output(formatted_csvs, formatted_csv_paths)
    return output_csvs


if __name__ == '__main__':
    # args = Munch(input_folder="./test/test_input")
    # print("Running Test Case")
    # main(args.input_folder)
    #
    # test_input = "./test/test_input/test_input.xlsx"
    # test_output = "./test/test_output/test_output.xlsx"
    #
    # input_df = pd.read_excel(test_input)
    # output_df = pd.read_excel(test_output)
    # assert input_df.equals(output_df)
    # print("Successfully ran Test Case")

    args = get_args()
    main(args.input_folder)
