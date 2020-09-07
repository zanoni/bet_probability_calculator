import glob
from datetime import date
from typing import List, Any, NoReturn

from openpyxl.worksheet.table import Table, TableStyleInfo
from openpyxl.worksheet.worksheet import Worksheet
from pydantic import BaseModel

from src.utils.excel_writer import ExcelWriter
from src.utils.excel_writer import excel_writer_of

FORMAT_PERCENT = '0.00%'
FORMAT_CURRENCY_REAL = '"$" #,##0.00_-'

PROBABILITY_HEADER = 'Probability'
OUTCOME_HEADER = 'Outcome'


class ProbabilityAndOutcome(BaseModel):
    probability: float
    outcome: float

    def get_probability(self):
        return self.probability

    def get_outcome(self):
        return self.outcome


def probability_and_outcome_of(probability: float, outcome: float):
    return ProbabilityAndOutcome(probability=probability, outcome=outcome)


class Bet(BaseModel):
    true: ProbabilityAndOutcome
    false: ProbabilityAndOutcome


def bet_of(probability: float, outcome: float):
    if probability > 100 or probability < 0 or outcome < 0:
        raise Exception("Bet probability must no be below 0% or above 100%, and bet outcome must be above $ 0,00")
    return Bet(
        true=probability_and_outcome_of(probability=probability / 100, outcome=outcome),
        false=probability_and_outcome_of(probability=1 - probability / 100, outcome=0)
    )


class BetProbability(BaseModel):
    amount_to_make: float
    amount_of_bets: int
    max_outcome: float
    bets: List[Bet]

    def all_probabilities(self) -> List[ProbabilityAndOutcome]:
        all_probabilities = []
        bets = self.bets.copy()
        first_bet = bets.pop(0)
        all_probabilities.append(first_bet.true)
        all_probabilities.append(first_bet.false)
        if not len(bets):
            return all_probabilities
        for bet in bets:
            bet_possibilities_true = []
            bet_possibilities_false = []
            for probability in all_probabilities:
                bet_possibilities_true.append(probability_and_outcome_of(
                    probability=(bet.true.get_probability() * probability.get_probability()),
                    outcome=(bet.true.get_outcome() + probability.get_outcome()),
                ))
                bet_possibilities_false.append(probability_and_outcome_of(
                    probability=(bet.false.get_probability() * probability.get_probability()),
                    outcome=(bet.false.get_outcome() + probability.get_outcome()),
                ))
            all_probabilities.clear()
            for possibility in bet_possibilities_true:
                all_probabilities.append(possibility)
            for possibility in bet_possibilities_false:
                all_probabilities.append(possibility)
        return all_probabilities

    def calculate_and_print(self):
        probabilities = self.all_probabilities()
        print_spacer()
        if self.amount_to_make:
            possibilities = list(filter(lambda i: i.get_outcome() >= self.amount_to_make, probabilities))
            probability = round(sum([p.get_probability() for p in possibilities]) * 100, 2)
            print(f"Your probability to make more than $ {self.amount_to_make} is {probability}%")
            print_spacer()
        filename = get_filename()
        generate_excel(filename, probabilities)
        self.filter_and_print_probabilities_in_four_sections(probabilities)
        print(f"For a more detailed list of your probabilities go to -> generated_probabilities/{filename}.xlsx")
        print_spacer()

    def filter_and_print_probabilities_in_four_sections(self, probabilities):
        max_value = self.max_outcome
        first_possibilities = list(filter(
            lambda i: 0 <= i.get_outcome() <= max_value * 1 / 4,
            probabilities))
        first_probability = round(sum([p.get_probability() for p in first_possibilities]) * 100, 2)
        second_possibilities = list(filter(
            lambda i: max_value * 1 / 4 < i.get_outcome() <= max_value * 2 / 4,
            probabilities))
        second_probability = round(sum([p.get_probability() for p in second_possibilities]) * 100, 2)
        third_possibilities = list(filter(
            lambda i: max_value * 2 / 4 < i.get_outcome() <= max_value * 3 / 4,
            probabilities))
        third_probability = round(sum([p.get_probability() for p in third_possibilities]) * 100, 2)
        fourth_possibilities = list(filter(
            lambda i: max_value * 3 / 4 < i.get_outcome() <= self.max_outcome,
            probabilities))
        fourth_probability = round(sum([p.get_probability() for p in fourth_possibilities]) * 100, 2)
        print(f"{first_probability}% -> $ 0 <= x <= $ {max_value * 1 / 4}")
        print(
            f"{second_probability}% -> $ {max_value * 1 / 4} < x <= $ {max_value * 2 / 4}")
        print(
            f"{third_probability}% -> $ {max_value * 2 / 4} < x <= $ {max_value * 3 / 4}")
        print(
            f"{fourth_probability}% -> $ {max_value * 3 / 4} < x <= $ {max_value}")
        print_spacer()


def bet_probability_of(amount_of_bets: float, bets: list, max_outcome: float, amount_to_make: float = 0):
    return BetProbability(amount_to_make=amount_to_make, amount_of_bets=amount_of_bets, bets=bets,
                          max_outcome=max_outcome)


def bet_probability_calculation():
    print_spacer()
    calculation_type = int(input(
        "How do you want to calculate your bets?\n"
        "1) Probability / Outcome\n"
        "2) Probability / Bet value / Odds\n"
        "3) Bet value / Odds (This will automatically set your probabilities, which will have a margin for error)\n"
    ))
    if not (calculation_type == 1 or calculation_type == 2 or calculation_type == 3):
        raise Exception("Please insert a value of 1, 2 or 3")
    amount_of_bets = int(input("Insert amount of bets: "))
    if amount_of_bets < 2:
        raise Exception("Amount of bets must be at least 2")
    max_outcome = 0
    bets = []
    if calculation_type == 1:
        for i in range(amount_of_bets):
            probability = float(input(f"Bet {i + 1} probability: "))
            outcome = float(input(f"Bet {i + 1} outcome: "))
            max_outcome += outcome
            bets.append(bet_of(probability=probability, outcome=outcome))
    if calculation_type == 2:
        for i in range(amount_of_bets):
            probability = float(input(f"Bet {i + 1} probability: "))
            value = float(input(f"Bet {i + 1} value: "))
            odd = float(input(f"Bet {i + 1} odds: "))
            outcome = value * odd
            max_outcome += outcome
            bets.append(bet_of(probability=probability, outcome=outcome))
    if calculation_type == 3:
        for i in range(amount_of_bets):
            value = float(input(f"Bet {i + 1} value: "))
            odd = float(input(f"Bet {i + 1} odds: "))
            probability = 1 / odd * 100
            outcome = value * odd
            max_outcome += outcome
            bets.append(bet_of(probability=probability, outcome=outcome))
    amount_to_make = float(input("Insert fixed value you want to make: "))
    probability = bet_probability_of(amount_to_make=amount_to_make, amount_of_bets=amount_of_bets, bets=bets,
                                     max_outcome=max_outcome)
    probability.calculate_and_print()


def get_excel_headers() -> List[str]:
    return [
        PROBABILITY_HEADER,
        OUTCOME_HEADER,
    ]


def get_excel_values(data: List[ProbabilityAndOutcome]) -> List[List[Any]]:
    return [[i.get_probability(), i.get_outcome()] for i in data]


def get_excel_formatting(
        worksheet: Worksheet,
        excel_writer: ExcelWriter,
) -> NoReturn:
    columns = ['A', 'B']
    column_a = worksheet['A:A']
    column_b = worksheet['B:B']
    tab = Table(displayName='Table1', ref=f'A1:B{len(excel_writer.values) + 1}')
    style = TableStyleInfo(name='TableStyleLight20', showRowStripes=True)
    tab.tableStyleInfo = style
    worksheet.add_table(tab)
    for cell in column_a:
        cell.number_format = FORMAT_PERCENT
    for cell in column_b:
        cell.number_format = FORMAT_CURRENCY_REAL
    for column in columns:
        worksheet.column_dimensions[column].width = 22


def generate_excel(filename, probabilities):
    excel_writer = excel_writer_of(
        filename=filename,
        values=get_excel_values(probabilities),
        headers=get_excel_headers(),
        formatting=get_excel_formatting,
    )
    excel_writer.create()


def get_filename():
    xlsx_files = glob.glob("./generated_probabilities/*.xlsx")
    return f"{date.today()}-{len(xlsx_files) + 1}"


def print_spacer():
    print("-" * 105)
