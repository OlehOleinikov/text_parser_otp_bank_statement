from dataclasses import dataclass, field
from datetime import datetime
from typing import List
import pandas as pd

from defines import DOC_TYPES, UNKNOWN


@dataclass
class SingleRecord:
    """
    Single record parser.
    Gets list of strings (text file rows) from DayWorker.
    """
    data: List[str] = field(repr=False)
    date: datetime
    amount: float = field(default=0.00)  # money sum
    doc_type: str = field(default='')  # payment document type
    doc_number: str = field(default='')  # payment document id
    ca_name: str = field(default='')  # counterparty description
    ca_code: str = field(default='')  # counterparty tax identification number
    ca_bank: str = field(default='')  # counterparty bank code
    ca_acc: str = field(default='')  # counterparty bank account number
    description: str = field(default='')  # counterparty payment description
    direction: int = field(default=UNKNOWN)  # money direction (debt/cred)
    pivot_row: int = field(default=None, repr=None)  # time row position (helps to find other attrs' positions)
    row_docname: int = field(default=None)  # document name position (helps to find end of data)

    def __post_init__(self):
        self._set_pivot()
        if self.pivot_row:
            self._set_time()
            self._set_description()
            self._set_amount()
            self._set_doc_number()
            self._set_doctype()
            self._set_ca_tax_info()
            self._set_ca_name()

    def _set_pivot(self):
        """Gets pivot for find other attributes"""
        for pos in range(len(self.data)):
            if self.data[pos].startswith('Проведено банком'):
                self.pivot_row = pos
                break

    def _set_doc_number(self):
        """Parses payment document id number"""
        self.doc_number = self.data[self.pivot_row - 1].split(' ', maxsplit=1)[0]

    def _set_amount(self):
        """Sets amount and payment description"""
        try:
            string = self.data[self.pivot_row - 1].split(' ', maxsplit=1)[1].strip()
            first_point = string.find('.')  # check float data present
            if first_point == -1:
                self.amount = 0.00  # fill zero if not float data
                print(f'WARNING: no data in amount position:'
                      f'\n\t{self.date}'
                      f'\n\t{self.data[self.pivot_row - 1]}')
            elif len(string) > first_point+2:
                self.description += string[first_point+3:]  # append payment description to attrs
                self.amount = float(string[:first_point+3].replace(' ', '').strip())  # get money amount
        except ValueError:
            print(f'WARNING: unexpected data in amount position:'
                  f'\n\t{self.date}'
                  f'\n\t{self.data[self.pivot_row - 1]}')
            self.amount = 0.00

    def _set_time(self):
        """Update date attribute with day time value"""
        time_string = self.data[self.pivot_row].replace('Проведено банком', '').strip()
        try:
            time = pd.to_timedelta(time_string, errors='raise')
        except ValueError:
            time = pd.to_timedelta("00:00:00")
            print(f'WARNING: unexpected data in time position:'
                  f'\n\t{self.date}'
                  f'\n\t{self.data[self.pivot_row]}')
        self.date += time

    def _set_doctype(self):
        type_pos = None
        for row_pos in range(len(self.data)):  # search row with payment document type
            if self.data[row_pos].strip() in DOC_TYPES:
                type_pos = row_pos
                break
        if type_pos:
            self.doc_type = self.data[type_pos].strip() + ' ' + self.data[type_pos + 1].strip()  # combine from 2 rows
            self.row_docname = type_pos

    def _set_ca_tax_info(self):
        """Parses row with counterparty info:

        - counterparty account number
        - counterparty tax identification code
        - counterparty bank code"""
        info_string = self.data[self.pivot_row + 1].strip().replace(' / ', ' ').replace(' 000000000 ', ' ').split(' ')
        self.ca_acc = info_string[-3]
        self.ca_code = info_string[-2]
        self.ca_bank = info_string[-1]

    def _set_ca_name(self):
        """Parse counterparty name (mixed company name with used bank)"""
        start_row = self.pivot_row + 2
        end_row = self.row_docname
        if (end_row - start_row) > 0:
            ca_name_part = self.data[start_row:end_row]
            self.ca_name = ' '.join([x.strip() for x in ca_name_part])

    def _set_description(self):
        """Sets payment description"""
        desc_part = self.data[0:self.pivot_row - 1]
        self.description = ' '.join([x.strip() for x in desc_part])

    def set_direction(self, direction: int):
        """Sets payment money direction (debt/cred).

        :param direction:  0-UNKNOWN/1-DEBT/2-CRED
        :return: None. Updates self.direction
        """
        self.direction = direction

    def get_record_lst(self):
        """
        Combine attributes to dataframe representation.

        :return: list of payment record attributes
        """
        return (self.date,
                self.amount,
                self.direction,
                self.description,
                self.doc_type,
                self.doc_number,
                self.ca_name,
                self.ca_code,
                self.ca_bank,
                self.ca_acc)
