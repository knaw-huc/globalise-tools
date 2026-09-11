#!/usr/bin/env python3
import argparse
import os
from copy import deepcopy

from loguru import logger
from openai import OpenAI

import globalise_tools.io_tools as rw

CHARACTERS_TO_STRIP = ",'„&():;=-–—_./#^"

# see https://github.com/globalise-huygens/glob-portal-infomodel/issues/85

class EmbeddingsGenerator:

    def __init__(self, index_file: str):
        self.index_path = index_file
        self.index = rw.read_json(index_file)
        self.client = OpenAI(
            base_url="https://api.scaleway.ai/v1",  # Scaleway's Generative APIs service URL
            api_key=os.environ['SCW_SECRET_KEY']    # Your unique API key from Scaleway
        )
        self.chunks_processed = 0

    def add_embeddings(self):
        documents = self.index["documents"]
        new_documents = []
        total = len(documents)
        for i, document in enumerate(documents):
            logger.info(f"processing document {i + 1}/{total}")
            new_document = deepcopy(document)
            fields = document["fields"]
            textfield = [f for f in fields if f['name'] == 'content'][0]
            text = textfield['value']
            chunks = self._chunk_text(text)
            logger.info(f"{len(chunks)} chunks")
            embeddings = [self._get_embeddings(chunk) for chunk in chunks]
            self.chunks_processed += len(chunks)
            new_document["embeddings"] = embeddings
            new_documents.append(new_document)
        new_index = deepcopy(self.index)
        new_index["documents"] = new_documents
        rw.write_json(self.index_path, new_index)
        logger.info(f"chunks processed: {self.chunks_processed}")

    @staticmethod
    def _chunk_text(text: str, chunk_size: int = 300, overlap: int = 75) -> list[str]:
        trimmed_words = [w.strip().strip(CHARACTERS_TO_STRIP) for w in text.split(" ")]
        words = [w for w in trimmed_words if len(w) > 0]
        step = chunk_size - overlap
        chunks = []
        size = len(words)
        for i in range(0, size, step):
            chunk = " ".join(trimmed_words[i:i + chunk_size])
            chunks.append(chunk)
            if i + chunk_size >= size:
                break
        return chunks

    def _get_embeddings(self, chunk: str) -> list[float]:
        embedding_response = self.client.embeddings.create(
            input=chunk,
            model="qwen3-embedding-8b"
        )
        return embedding_response.data[0].embedding


def get_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Calculate embeddings for text chunks of the documents of the given inventory index, and add them to it.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-i", "--inventory-index-file",
                        help="The index.json file",
                        type=str,
                        required=True,
                        )
    return parser.parse_args()


@logger.catch(reraise=True)
def main():
    args = get_arguments()
    EmbeddingsGenerator(args.inventory_index_file).add_embeddings()


if __name__ == '__main__':
    main()
