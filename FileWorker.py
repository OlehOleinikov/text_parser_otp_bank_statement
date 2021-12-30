import pandas as pd

from DayWorker import DayWorker
from defines import ORIGIN_HEADERS, PAGE_SEPARATOR, UNKNOWN, DEBT, CRED


class FileWorker:
    """
    - Parse file data
    - Gather acc owner info
    - Clean tech and rudiment rows
    - Divide rows to day-data parts
    """
    def __init__(self, path):
        self.path = path
        self.data = None
        self.owner_name = None
        self.owner_id_number = None
        self.owner_iban = None
        self.owner_account = None
        self.currency = None

        self.load_file_data()
        self.clean_data()
        self.gather_owner_info()

        self.days_positions = self.get_days_borders()
        self.days_instances = []
        self.covert_all_days()

    def load_file_data(self):
        """
        Loads file contents as list of strings (row-by-row). ANSI encoding expected.
        Updates an instance data attribute.
        """
        with open(self.path) as file:
            self.data = file.readlines()

    def clean_data(self):
        """
        Removes rows with signs of garbage.
        Updates an instance data attribute.
        """
        self.data = [x for x in self.data if x.strip() not in ORIGIN_HEADERS]  # remove rudiment headers

        for row_num in range(len(self.data)):
            find_status = str(self.data[row_num]).find(PAGE_SEPARATOR)  # find running title to remove
            if find_status != (-1):
                self.data[row_num] = "DELETE"  # mark row index to remove
        self.data = [x for x in self.data if not x.startswith('DELETE')]

    def gather_owner_info(self):
        """
        Gathers account owner title info. Based on the relative position of the attributes in the text.
        Updates instance attributes:

        - owner's name
        - owner's tax identification number
        - owner's IBAN
        - owner's bank account number
        """
        for pos in range(len(self.data)):
            if self.data[pos].startswith('Адреса кліента / Customer address:'):
                self.owner_name = self.data[pos+1].strip()
                break
        for pos in range(len(self.data)):
            if self.data[pos].startswith('Ідентифікаційний код / Тах ID:'):
                self.owner_id_number = (self.data[pos].strip()).split(' ')[-1]
                break
        for pos in range(len(self.data)):
            if self.data[pos].startswith('IBAN:'):
                self.owner_iban = (self.data[pos].strip()).split(' ')[-1]
                break
        for pos in range(len(self.data)):
            if self.data[pos].startswith('Рахунок / Account:'):
                self.owner_account = (self.data[pos].strip()).split(' ')[-2]
                self.currency = (self.data[pos].strip()).split(' ')[-1]
                break

    def get_days_borders(self):
        """
        Get rows' indexes with border signs to divide data by days

        :return: list of integers (rows positions)
        """
        border_signs = []
        for ix in range(len(self.data)):
            if self.data[ix].startswith('Дата / Date:') or self.data[ix].startswith('Залишок на кінець дня'):
                border_signs.append(ix)
        return border_signs

    def covert_all_days(self):
        """
        Create DayWorker instances for all days and appending instances to FileWorker attributes (listed).
        Based on previously defined row numbers with signs of day boundaries (self.days_positions)
        """
        for pos in range(len(self.days_positions) - 1):
            if (self.days_positions[pos+1] - self.days_positions[pos]) < 6:  # skip space between days
                continue
            current_day = DayWorker(self.data[self.days_positions[pos]:self.days_positions[pos+1]])
            current_day.convert_day_records()
            self.days_instances.append(current_day)

    def extract_pandas(self):
        """
        Concat all day dataframes and append columns with account owner title info

        :return: Pandas dataframe with money transaction records
        """
        df = pd.DataFrame()  # init empty dataframe
        for inst in self.days_instances:  # get dataframes from each day
            new_df = inst.create_day_df()
            df = pd.concat([df, new_df], ignore_index=True, sort=False)  # append day dataframe to main dataframe
        df.reset_index(inplace=True, drop=True)
        df['owner_name'] = self.owner_name  # add common attributes as columns with same values
        df['owner_id_number'] = self.owner_id_number
        df['owner_iban'] = self.owner_iban
        df['owner_account'] = self.owner_account
        df['currency'] = self.currency
        direction_dict = {UNKNOWN: 'unknown',
                          DEBT: 'debit',
                          CRED: 'credit'}
        df['direction'] = df['direction'].map(direction_dict)
        return df


