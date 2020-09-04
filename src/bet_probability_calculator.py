from typing import List, Any, NoReturn

from openpyxl.worksheet.table import Table, TableStyleInfo
from openpyxl.worksheet.worksheet import Worksheet
from pydantic import BaseModel

from src.utils.excel_writer import ExcelWriter
from src.utils.excel_writer import excel_writer_of

DHO_EXCEL_FILENAME = 'all_probabilities'

FORMAT_PERCENT = '0.00%'
FORMAT_CURRENCY_REAL = '"R$" #,##0.00_-'

PROBABILITY_HEADER = 'Probability'
RETURN_HEADER = 'Return'


class ProbabilityAndReturn(BaseModel):
    bet_probability: float
    bet_return: float

    def get_bet_probability(self):
        return self.bet_probability

    def get_bet_return(self):
        return self.bet_return

    def __str__(self):
        bet_probability = round((self.get_bet_probability() * 100), 2)
        bet_return = round(self.get_bet_return(), 2)
        return f"Probability {bet_probability}% -> R$ {bet_return}"


def probability_and_return_of(bet_probability: float, bet_return: float):
    return ProbabilityAndReturn(bet_probability=bet_probability, bet_return=bet_return)


class Bet(BaseModel):
    true: ProbabilityAndReturn
    false: ProbabilityAndReturn


def bet_of(bet_probability: float, bet_return: float):
    if bet_probability > 100 or bet_probability < 0 or bet_return < 0:
        raise Exception("Bet start must no be above 100% or below 0%, bet return must be above R$ 0,00")
    return Bet(
        true=probability_and_return_of(bet_probability=bet_probability / 100, bet_return=bet_return),
        false=probability_and_return_of(bet_probability=1 - bet_probability / 100, bet_return=0)
    )


class BetProbability(BaseModel):
    amount_to_make: float
    amount_of_bets: int
    bets: List[Bet]

    def all_probabilities(self) -> List[ProbabilityAndReturn]:
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
                bet_possibilities_true.append(probability_and_return_of(
                    bet_probability=(bet.true.get_bet_probability() * probability.get_bet_probability()),
                    bet_return=(bet.true.get_bet_return() + probability.get_bet_return()),
                ))
                bet_possibilities_false.append(probability_and_return_of(
                    bet_probability=(bet.false.get_bet_probability() * probability.get_bet_probability()),
                    bet_return=(bet.false.get_bet_return() + probability.get_bet_return()),
                ))
            all_probabilities.clear()
            for possibility in bet_possibilities_true:
                all_probabilities.append(possibility)
            for possibility in bet_possibilities_false:
                all_probabilities.append(possibility)
        return all_probabilities

    def start(self):
        probabilities = self.all_probabilities()
        possibilities = list(filter(lambda i: i.get_bet_return() >= self.amount_to_make, probabilities))
        probability = round(sum([p.get_bet_probability() for p in possibilities]) * 100, 2)
        generate_excel(probabilities)
        return f"Your probability to make more than R$ {self.amount_to_make} is {probability}%"


def bet_probability_of(amount_to_make: float, amount_of_bets: float, bets: list):
    return BetProbability(amount_to_make=amount_to_make, amount_of_bets=amount_of_bets, bets=bets)


def bet_probability_calculation():
    print("-" * 50)
    amount_to_make = float(input("Amount to make: "))
    amount_of_bets = int(input("Amount of bets: "))
    bets = []
    if amount_of_bets < 1:
        raise Exception("Amount of bets must be at least 1")
    for i in range(amount_of_bets):
        bet_probability = float(input(f"Bet {i + 1} probability: "))
        bet_return = float(input(f"Bet {i + 1} return: "))
        bets.append(bet_of(bet_probability=bet_probability, bet_return=bet_return))
    bet_probability = bet_probability_of(amount_to_make=amount_to_make, amount_of_bets=amount_of_bets, bets=bets)
    print("-" * 50)
    print(bet_probability.start())
    print("-" * 50)


def get_excel_headers() -> List[str]:
    return [
        PROBABILITY_HEADER,
        RETURN_HEADER,
    ]


def get_excel_values(data: List[ProbabilityAndReturn]) -> List[List[Any]]:
    return [[i.get_bet_probability(), i.get_bet_return()] for i in data]


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


def generate_excel(probabilities):
    excel_writer = excel_writer_of(
        filename=DHO_EXCEL_FILENAME,
        values=get_excel_values(probabilities),
        headers=get_excel_headers(),
        formatting=get_excel_formatting,
    )
    excel_writer.create()
