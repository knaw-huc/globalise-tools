#!/usr/bin/env python3
import argparse
import os
from copy import deepcopy

import globalise_tools.io_tools as rw
from loguru import logger
from openai import OpenAI
from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
)
import struct
import base64
from dataclasses import dataclass

CHARACTERS_TO_STRIP = ",'„&():;=-–—_./#^"


# see https://github.com/globalise-huygens/glob-portal-infomodel/issues/85

@dataclass
class TextEmbedding:
    text: str
    vector_as_base64: str


class EmbeddingsGenerator:

    def __init__(self, index_file: str, embeddings_folder: str):
        self.index_path = index_file
        self.embeddings_folder = embeddings_folder
        self.index = rw.read_json(index_file)
        self.client = OpenAI(
            base_url="https://api.scaleway.ai/v1",  # Scaleway's Generative APIs service URL
            api_key=os.environ['SCW_SECRET_KEY']  # Your unique API key from Scaleway
        )
        self.chunks_processed = 0

    def generate_embeddings(self):
        documents = self.index["documents"]
        new_documents = []
        total = len(documents)
        for i, document in enumerate(documents):
            logger.info(f"processing document {i + 1}/{total}")
            new_document = deepcopy(document)
            new_document.pop("embeddings", None)
            new_documents.append(new_document)
            fields = document["fields"]
            textfield = [f for f in fields if f['name'] == 'content'][0]
            text = textfield['value']
            name_field = [f for f in fields if f['name'] == 'name'][0]
            name = name_field['value']
            chunks = self._chunk_text(text)
            logger.info(f"{len(chunks)} chunks")
            embeddings = [self._get_embeddings(chunk) for chunk in chunks]
            self.chunks_processed += len(chunks)
            path = self.embeddings_folder + "/" + name + ".jsonl"
            rw.write_jsonl(path, embeddings)
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
            if len(chunk) < chunk_size < len(trimmed_words):
                chunk = " ".join(trimmed_words[-chunk_size:])
            chunks.append(chunk)
            if i + chunk_size >= size:
                break
        return chunks

    @retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(6))
    def _get_embeddings(self, chunk: str) -> TextEmbedding:
        embedding_response = self.client.embeddings.create(
            input=chunk,
            model="qwen3-embedding-8b"
        )
        return TextEmbedding(
            text=chunk,
            vector_as_base64=floats_to_es_base64(embedding_response.data[0].embedding)
        )


def floats_to_es_base64(values: list[float]) -> str:
    """Encode a list of floats as a base64 string for Elasticsearch.

    Elasticsearch expects vector bytes as 4-byte IEEE-754 floats in
    big-endian order when a dense_vector is supplied as a base64 string.
    """
    packed = struct.pack(f">{len(values)}f", *values)
    return base64.b64encode(packed).decode("ascii")


def get_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Calculate embeddings for text chunks of the documents of the given inventory index, and write them to separate embeddings files per document.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-i", "--inventory-index-file",
                        help="The index.json file",
                        type=str,
                        required=True,
                        )
    parser.add_argument("-e", "--embeddings-folder",
                        help="The folder to write the embedding files per document in.",
                        type=str,
                        required=True,
                        )
    return parser.parse_args()


@logger.catch(reraise=True)
def main():
    args = get_arguments()
    EmbeddingsGenerator(args.inventory_index_file,args.embeddings_folder).generate_embeddings()


if __name__ == '__main__':
    main()
