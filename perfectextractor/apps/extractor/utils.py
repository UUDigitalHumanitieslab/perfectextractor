import contextlib
import csv

from xlsxwriter import Workbook

# Output formats for the results
TXT = 'txt'
XML = 'xml'

# Output format for the file
CSV = 'csv'
XLSX = 'xlsx'


def get_adjacent_line_number(segment_number, i):
    """
    Returns the next segment number + i.
    Segment numbers have the form "pN.sM", where N/M are positive integers.
    """
    split = segment_number.split('s')
    adj = int(split[1]) + i
    return split[0] + 's' + str(adj)


class ExcelWriter:
    """
    Writes xlsx files while mimicking the CSV writer interface.
    """
    def __init__(self, filename):
        self._workbook = Workbook(filename)
        self._worksheet = self._workbook.add_worksheet()  # this assumes an empty file
        self._row = 0

    def writerow(self, contents, is_header=False):
        cell_format = None

        # Add bold formatting and an autofilter
        if is_header:
            cell_format = self._workbook.add_format({'bold': True})
            self._worksheet.autofilter(self._row, 0, 0, len(contents) - 1)

        self._worksheet.write_row(self._row, 0, contents, cell_format)
        self._row += 1

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)

    def close(self):
        self._workbook.close()


@contextlib.contextmanager
def open_csv(filename):
    with open(filename, 'w') as fileobj:
        fileobj.write('\uFEFF')  # the UTF-8 BOM to hint Excel we are using that...
        yield csv.writer(fileobj, delimiter=';')


@contextlib.contextmanager
def open_xlsx(filename):
    writer = ExcelWriter(filename)
    yield writer
    writer.close()
