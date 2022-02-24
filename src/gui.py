from tkinter import OptionMenu, Label, LabelFrame, Entry, Tk, StringVar, Button
from typing import Callable

from pydantic import BaseModel

from bet_probability_calculator import bet_of, bet_probability_of

window = Tk()
window.title('Bet Probability Calculator')

main_frame = LabelFrame(window, padx=10, pady=10)
main_frame.pack(padx=10, pady=10)

probabilities = []
bet_values = []
odds = []
outcomes = []


def label_and_input(frame, row, name):
    label = Label(frame, text=name)
    label.grid(row=row, column=0)
    entry = Entry(frame)
    entry.grid(row=row, column=1)
    return entry


def bet_label_and_input(frame, column, name):
    label = Label(frame, text=name)
    label.grid(row=0, column=column * 2)
    entry = Entry(frame)
    entry.grid(row=0, column=column * 2 + 1)
    return entry


def pvo_bet_inputs(number):
    bet_frame = LabelFrame(main_frame, text=f"Bet {number + 1}", padx=10)
    bet_frame.grid(row=number + 1)
    probabilities.append(bet_label_and_input(bet_frame, 0, "Probability"))
    bet_values.append(bet_label_and_input(bet_frame, 1, "Bet value"))
    odds.append(bet_label_and_input(bet_frame, 2, "Odds"))


def pvo_bet_constructor():
    l, max_outcome = [], 0
    for n in range(int(number_of_bets.get())):
        outcome = float(odds[n].get()) * float(bet_values[n].get())
        max_outcome += outcome
        l.append(bet_of(probability=float(probabilities[n].get()), outcome=outcome))
    return l, max_outcome


def po_bet_inputs(number):
    bet_frame = LabelFrame(main_frame, text=f"Bet {number + 1}", padx=10)
    bet_frame.grid(row=number)
    probabilities[number] = bet_label_and_input(bet_frame, 0, "Probability")
    outcomes[number] = bet_label_and_input(bet_frame, 1, "Outcome")


def po_bet_constructor():
    l, max_outcome = [], 0
    for n in range(int(number_of_bets.get())):
        max_outcome += float(outcomes[n].get())
        l.append(bet_of(probability=float(probabilities[n].get()), outcome=float(outcomes[n].get())))
    return l, max_outcome


def vo_bet_inputs(number):
    bet_frame = LabelFrame(main_frame, text=f"Bet {number + 1}", padx=10)
    bet_frame.grid(row=number)
    bet_values[number] = bet_label_and_input(bet_frame, 0, "Bet Value")
    odds[number] = bet_label_and_input(bet_frame, 1, "Odds")


def vo_bet_constructor():
    l, max_outcome = [], 0
    for n in range(int(number_of_bets.get())):
        probability = 1 / float(odds[n].get()) * 100
        outcome = float(bet_values[n].get()) * float(odds[n].get())
        max_outcome += outcome
        l.append(bet_of(probability=probability, outcome=outcome))
    return l, max_outcome


class CalculationMethod(BaseModel):
    exec_func: Callable
    calculate_func: Callable

    def create_bets_input(self):
        for n in range(int(number_of_bets.get())):
            self.exec_func(n)
        calc_button = Button(main_frame, text="Calculate", command=self.calculate)
        calc_button.grid(row=int(number_of_bets.get()) + 1, column=0)

    def calculate(self):
        bets, max_outcome = self.calculate_func()
        probability = bet_probability_of(amount_to_make=float(amount_to_make.get()),
                                         amount_of_bets=int(number_of_bets.get()),
                                         bets=bets,
                                         max_outcome=max_outcome)
        probability.calculate_and_print()


pvo_label = "Probability / Bet value / Odds"
po_label = "Probability / Outcome"
vo_label = "Bet value / Odds"

calc_methods_labels = [pvo_label, po_label, vo_label]

calc_methods = [
    {"label": pvo_label, "exec_func": pvo_bet_inputs, "calculate_func": pvo_bet_constructor},
    {"label": po_label, "exec_func": po_bet_inputs, "calculate_func": po_bet_constructor},
    {"label": vo_label, "exec_func": vo_bet_inputs, "calculate_func": vo_bet_constructor},
]


def submit_click():
    calc_method = [d for d in calc_methods if d["label"] == str(calc_method_clicked.get())][0]
    calc_obj = CalculationMethod(exec_func=calc_method["exec_func"], calculate_func=calc_method["calculate_func"])
    calc_obj.create_bets_input()


presets_frame = LabelFrame(main_frame, text=f"Presets", padx=10, pady=10)
presets_frame.grid(row=0)

calc_method_clicked = StringVar()
calc_method_clicked.set(calc_methods_labels[0])
calc_method_label = Label(presets_frame, text="Calculation method")
calc_method_label.grid(row=0, column=0)
drop = OptionMenu(presets_frame, calc_method_clicked, *calc_methods_labels)
drop.grid(row=0, column=1)

number_of_bets = label_and_input(presets_frame, 1, "Number of bets")

amount_to_make = label_and_input(presets_frame, 2, "Value you want to make")

submit_presets_button = Button(presets_frame, text="Submit", command=submit_click)
submit_presets_button.grid(row=3, column=1)
