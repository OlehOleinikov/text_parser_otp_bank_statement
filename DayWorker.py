import pandas as pd
from SingleRecord import SingleRecord
from DirectionChoicer import MoneyDirectionChoicer
from defines import DOC_TYPES


class DayWorker:
    """
    Single day parser.
    Gets list of strings (text file rows) from FileWorker.
    """
    def __init__(self, data):
        self.data = data
        self.date = self._parse_date()
        self.operations_in_day = 0
        self.end_balance = 0.00
        self.debt_sum = 0.00  # need for money direction value recovery
        self.cred_sum = 0.00  # need for money direction value recovery
        self.records_positions = []  # rows indexes with records border signs
        self.records_instances = []  # list of SingleRecord instances
        self._parse_day_debt_credit_sums()
        self._count_today_operations()
        self._get_records_positions_signs()
        self.convert_day_records()

        self.amount_dict = self._gather_amount_dict()  # {row_index: amount} for money direction recovery
        self._choice_money_direction()

        self.records_lst = []  # list of tuple with single payment data (for dataframe creation)
        self._gather_records_lst()
        self.df = pd.DataFrame()  # init empty dataframe

    def _parse_date(self):
        date = None
        for row_string in self.data:
            if row_string.startswith('Дата / Date:'):
                date_string = row_string[13:].split(maxsplit=1)[0]
                date = pd.to_datetime(date_string, dayfirst=True, errors='coerce')
                break
        return date

    def _parse_day_debt_credit_sums(self):
        for row_string in self.data:
            if row_string.startswith('Усього оборотів за день'):
                draft = row_string[43:]
                draft = draft.strip().replace(' ', '')
                point = draft.find('.')
                self.debt_sum = draft[:point + 3]
                self.cred_sum = draft[point + 3:]

    def _count_today_operations(self):
        counter = 0
        for row_string in self.data:
            if row_string.strip() in DOC_TYPES:
                counter += 1
        self.operations_in_day = counter

    def _get_records_positions_signs(self):
        """Gathers positions with ends of each record part"""
        positions = [1]
        for pos in range(len(self.data)):
            if self.data[pos].strip() in DOC_TYPES:
                positions.append(pos + 2)
        self.records_positions = positions

    def _set_end_day_balance(self):
        for row_string in self.data:
            if row_string.startswith('Залишок на кінець дня'):
                self.end_balance = float(row_string[45:].strip().replace(' ', ''))

    def convert_day_records(self):
        """Create SingleRecord instances for each payment record"""
        recs = []
        for record_pos in range(len(self.records_positions) - 1):
            current_record = SingleRecord(data=self.data[self.records_positions[record_pos]:
                                                         self.records_positions[record_pos + 1]],
                                          date=self.date)
            recs.append(current_record)
        self.records_instances = recs

    def _gather_amount_dict(self):
        """
        Create dict with record instance position and record amount.

        :return: {int(record_index): float(amount)}
        """
        res_dict = {}
        for inst_num in range(len(self.records_instances)):
            res_dict.update({inst_num: self.records_instances[inst_num].amount})
        return res_dict

    def _choice_money_direction(self):
        """Recovery lost direction value (debt or cred).
        Based on known daily debit and credit values."""
        directions_dict = MoneyDirectionChoicer(self.amount_dict, self.debt_sum, self.cred_sum, self.date).calculate()
        for inst_num in range(len(self.records_instances)):
            self.records_instances[inst_num].set_direction(directions_dict[inst_num])

    def _gather_records_lst(self):
        """Combine records' data tuples to list for dataframe creation."""
        for rec in self.records_instances:
            self.records_lst.append(rec.get_record_lst())

    def create_day_df(self):
        columns = ["date_time",
                   "amount",
                   "direction",
                   "description",
                   "doc_type",
                   "doc_number",
                   "ca_name",
                   "ca_code",
                   "ca_bank",
                   "ca_acc"]
        df = pd.DataFrame(data=self.records_lst, columns=columns)
        return df
