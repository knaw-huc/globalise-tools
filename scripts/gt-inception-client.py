#!/usr/bin/env python3

import hydra
from icecream import ic
from loguru import logger
from omegaconf import DictConfig

from globalise_tools.inception_client import InceptionClient, Document


@logger.catch
@hydra.main(version_base=None)
def main(cfg: DictConfig) -> None:
    inception_cfg = cfg.inception
    authorization = inception_cfg.get('authorization', None)
    base = cfg.inception.base_uri
    if authorization:
        client = InceptionClient(base_uri=base, authorization=authorization, oauth2_proxy=cfg.inception.oauth2_proxy)
    else:
        client = InceptionClient(base_uri=base, user=cfg.inception.user, password=cfg.inception.password)
    # create_project(client)
    list_all(client)


def create_project(client: InceptionClient):
    response = client.create_project(name="my-project", title="a test project")
    response = client.create_project_document(project_id=4,
                                              name="test-doc",
                                              file_format='text',
                                              file_path="")
    ic(response)


def list_all(client: InceptionClient):
    for project in client.get_projects():
        if project.name == 'globalise-2023':
            ic(project)
            print(project.name)
            response = client.get_project_documents(project.id)
            documents = [Document.from_dict(d) for d in response.body]
            for document in documents:
                ic(document)
                print(f"\t{document.name}")
                xmi = client.get_project_document(project.id, document.id)
                path = f"out/{document.name.split(' ')[0]}.xmi"
                logger.debug(f"=> {path}")
                with open(path, "w") as f:
                    f.write(xmi)
                response = client.get_document_annotations(project.id, document.id)
                # annotations = [Annotation.from_dict(d) for d in response.body]
                # for annotation in annotations:
                #     if annotation.state == 'COMPLETE':
                #         ic(annotation)
                #         print(f"\t\t{annotation.user} | {annotation.state} | {annotation.timestamp}")


if __name__ == '__main__':
    main()
