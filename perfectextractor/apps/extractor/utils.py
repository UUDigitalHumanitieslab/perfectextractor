import contextlib
import configparser
import csv
from typing import Dict, List, Tuple, Union

from xlsxwriter import Workbook  # type: ignore

# Output formats for the results
TXT = 'txt'
XML = 'xml'

# Output format for the file
CSV = 'csv'
XLSX = 'xlsx'


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


class CachedConfig:
    """
    Caches the parsed config to save time when doing the lookups.
    """
    def __init__(self, config: configparser.ConfigParser) -> None:
        self.cache: Dict[Tuple[str, str], Union[str, bool]] = dict()
        self.config = config

    def setdefault(self, key: Tuple[str, str], func):
        if key in self.cache:
            return self.cache[key]
        return self.cache.setdefault(key, func())

    def get(self, section: str, key: str, **kwargs) -> str:
        return self.setdefault((section, key), lambda: self.config.get(section, key, **kwargs))

    def getboolean(self, section: str, key: str, **kwargs) -> bool:
        return self.setdefault((section, key), lambda: self.config.getboolean(section, key, **kwargs))

    def sections(self) -> List[str]:
        return self.config.sections()

    def __getitem__(self, key: str) -> configparser.SectionProxy:
        return self.config[key]
