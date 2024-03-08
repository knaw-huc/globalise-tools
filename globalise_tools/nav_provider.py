import json
import os
from typing import Dict

from loguru import logger


class NavProvider:

    def __init__(self):
        self.inv_nr = None
        self.index_path = None
        self.index = {}

    def load_index(self, inv_nr):
        self.inv_nr = inv_nr
        self.index_path = f'out/page_nav_idx_{inv_nr}.json'
        if os.path.exists(self.index_path):
            with open(self.index_path) as f:
                self.index = json.load(f)
        else:
            logger.error(f"file not found: {self.index_path}")
            self.index = {}

    def nav_fields(self, page_id: str) -> Dict[str, str]:
        try_match = True
        nav = {}
        while try_match:
            if page_id in self.index:
                nav = self.index[page_id]
                try_match = False
            else:
                inv_nr = page_id.split('_')[-2]
                if inv_nr == self.inv_nr:
                    logger.error(f'page_id {page_id} not found in {self.index_path}')
                    nav = self._deduced_nav(page_id)
                    try_match = False
                else:
                    self.load_index(inv_nr)
        x_nav = {}
        for k, v in nav.items():
            x_nav[f'{k}PageId'] = f'urn:globalise:{v}'
        return x_nav

    @staticmethod
    def _deduced_nav(page_id: str):
        nav = {}
        parts = page_id.split('_')
        base = '_'.join(parts[:-1])
        i = int(page_id.split('_')[-1])
        if i > 0:
            nav['prev'] = f'{base}_{(i - 1):04d}'
        nav['next'] = f'{base}_{(i + 1):04d}'
        return nav
