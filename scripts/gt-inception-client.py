#!/usr/bin/env python3

import hydra
from icecream import ic
from loguru import logger
from omegaconf import DictConfig

from globalise_tools.inception_client import InceptionClient, Project, Document, Annotation


@logger.catch
@hydra.main(version_base=None)
def main(cfg: DictConfig) -> None:
    inception_cfg = cfg.inception
    authorization = inception_cfg.get('authorization', None)
    base = cfg.inception.base_uri
    if authorization:
        client = InceptionClient(base_uri=base, authorization=authorization, cookie=cfg.inception.cookie)
    else:
        client = InceptionClient(base_uri=base, user=cfg.inception.user, password=cfg.inception.password)
    create_project(client)
    list_all(client)


def create_project(client: InceptionClient):
    response = client.create_project(name="my-project", title="a test project")
    ic(response.json())
    response = client.create_project_document(project_id=4,
                                              data="Lorem ipsum dolor bla bla bla.",
                                              name="test-doc",
                                              format='text')
    ic(response)
    ic(response.json())


def list_all(client: InceptionClient):
    response = client.get_projects()
    projects = [Project.from_dict(p) for p in response.json()['body']]
    for project in projects:
        ic(project)
        print(project.name)
        response = client.get_project_documents(project.id)
        documents = [Document.from_dict(d) for d in response.json()['body']]
        for document in documents:
            ic(document)
            print(f"\t{document.name}")
            response = client.get_document_annotations(project.id, document.id)
            annotations = [Annotation.from_dict(d) for d in response.json()['body']]
            for annotation in annotations:
                ic(annotation)
                print(f"\t\t{annotation.user} | {annotation.state} | {annotation.timestamp}")


if __name__ == '__main__':
    main()
