from itertools import combinations
from defines import DEBT, CRED, UNKNOWN


class MoneyDirectionChoicer:
    def __init__(self, values: dict, sum_debt: float, sum_cred: float, date):
        self.date = date
        self.values_dict = values
        self.values_ordered_lst = [x for x in self.values_dict.values()]
        self.sum_debt = float(sum_debt)
        self.sum_cred = float(sum_cred)
        self.comb_range = len(self.values_dict)
        self.error = bool(self.check_sum_assertion())

    def calculate(self):
        if self.sum_cred == 0.00:  # all records are debt
            return {x: DEBT for x in range(self.comb_range)}
        elif self.sum_debt == 0.00:  # all records are cred
            return {x: CRED for x in range(self.comb_range)}
        elif self.check_single():  # only one record has another direction
            res_single_check = self.check_single()
            if res_single_check:  # [0] - position, [1] - aim type, [2] - other type
                position = res_single_check[0]
                aim_type = res_single_check[1]
                other_values_type = res_single_check[2]
                dict_prep = {x: other_values_type for x in range(self.comb_range)}
                dict_single_part = {int(position): int(aim_type)}
                dict_prep.update(dict_single_part)
                return dict_prep
        elif self.check_combinations():  # mixed directions in day
            res = self.check_combinations()
            lst = list([round(x, 2) for x in res[0]])
            aim_value = res[1]
            other_values = res[2]
            res_dict = {x: other_values for x in range(self.comb_range)}
            for item in lst:
                for key_count in range(len(res_dict)):
                    if self.values_dict[key_count] == item:
                        res_dict.update({key_count: aim_value})
                        break
            return res_dict
        return {x: UNKNOWN for x in range(self.comb_range)}

    def check_sum_assertion(self):
        """
        Equality check of sum records' amount to day debt and cred result.

        :return: True - assertion error, None - assertion ok
        """
        operations_summary = round(sum(self.values_dict.values()), 2)
        day_results_summary = round(self.sum_debt + self.sum_cred, 2)
        if operations_summary != day_results_summary:
            print(f'Assertion alert in day - {self.date}')
            print(operations_summary)
            print(day_results_summary)
            return True

    def check_single(self):
        for element in range(len(self.values_ordered_lst)):
            if self.values_ordered_lst[element] == self.sum_debt:
                return [element, DEBT, CRED]
            if self.values_ordered_lst[element] == self.sum_cred:
                return [element, CRED, DEBT]
        return None

    def check_combinations(self):
        if self.comb_range <= 2:
            return None
        else:
            for digits_count in range(2, self.comb_range - 1):
                for comb in combinations(self.values_ordered_lst, digits_count):
                    if round(sum(comb), 2) == self.sum_cred:
                        return [comb, CRED, DEBT]
                    if sum(comb) == self.sum_debt:
                        return [comb, DEBT, CRED]
