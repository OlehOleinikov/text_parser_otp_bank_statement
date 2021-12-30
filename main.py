import os
from FileWorker import FileWorker


if __name__ == '__main__':
    files_list = [x for x in os.listdir() if x.endswith('.txt')]  # load pre_parsed text files
    for file in files_list:
        current_file = FileWorker(file)
        df = current_file.extract_pandas()
        df.to_excel(f"{file.split('.')[0]}.xlsx")


