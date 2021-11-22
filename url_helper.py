import requests


class TflUrlHelper:

    def __init__(self):
        self.valid_ids = self.get_valid_ids()

    def get_valid_ids(self) -> set:
        url = f"https://api.tfl.gov.uk/Line/Mode/tube"
        resp = requests.get(url)
        valid_ids = set()
        for r in resp.json():
            valid_ids.add(r['id'])
        return valid_ids

    def is_valid_lines(self, lines: list) -> bool:
        if lines:
            return set(lines) <= self.valid_ids
        return False

    def construct_lines_from_raw_lines(self, raw_lines: str) -> list:
        return raw_lines.split(',')
        

    def construct_url_from_lines(self, raw_lines: list) -> str:
        lines = self.construct_lines_from_raw_lines(raw_lines)
        if self.is_valid_lines(lines):
            fmt_lines = ','.join(lines)
            return f"https://api.tfl.gov.uk/Line/{fmt_lines}/Disruption"
        else:
            raise ValueError("Lines are invalid")
