from typing import List, Any, Type, Callable, NoReturn

from openpyxl import Workbook


class ExcelWriter(object):
    filename: str
    headers: List[Any]
    values: List[List[Any]]
    formatting: Type[Callable]

    def __init__(
            self,
            filename: str,
            headers: List[Any],
            values: List[List[Any]],
            formatting: Type[Callable],
    ):
        self.filename = filename
        self.headers = headers
        self.values = values
        self.formatting = formatting

    def create(self) -> NoReturn:
        workbook = Workbook()
        worksheet = workbook.active
        worksheet.append(self.headers)
        for values in self.values:
            worksheet.append(values)
        if self.formatting:
            self.formatting(
                worksheet=worksheet,
                excel_writer=self,
            )
        workbook.save(f"generated_probabilities/{self.filename}.xlsx")


def excel_writer_of(
        filename: Any,
        values: List[List[Any]],
        headers: List[Any] = None,
        formatting: Type[Callable] = None,
) -> ExcelWriter:
    filename = str(filename)
    return ExcelWriter(
        filename=filename,
        headers=headers,
        values=values,
        formatting=formatting,
    )
