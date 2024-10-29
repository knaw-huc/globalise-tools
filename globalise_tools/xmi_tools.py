import json

from cassis import cas
from loguru import logger


class XMIProcessorFactory:

    def __init__(self, typesystem_path: str):
        logger.info(f"<= {typesystem_path}")
        with open(typesystem_path, 'rb') as f:
            self.typesystem = cas.load_typesystem(f)
        self.document_data = self._read_document_data()
        self.commit_id = self._read_current_commit_id()

    def get_xmi_processor(self, xmi_path: str) -> XMIProcessor:
        return XMIProcessor(self.typesystem, self.document_data, self.commit_id, xmi_path)

    @staticmethod
    def _read_document_data() -> dict[str, any]:
        path = "data/document_data.json"
        logger.info(f"<= {path}")
        with open(path) as f:
            return json.load(f)

    @staticmethod
    def _read_current_commit_id():
        if git.there_are_uncommitted_changes():
            logger.warning("Uncommitted changes! Do a `git commit` first!")
        return git.read_current_commit_id()
