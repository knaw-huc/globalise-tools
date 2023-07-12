from dataclasses import dataclass
from typing import Dict

import requests
from dataclasses_json import dataclass_json
from loguru import logger


class InceptionClient:

    def __init__(self,
                 base_uri: str,
                 user: str = None,
                 password: str = None,
                 authorization: str = None,
                 cookie: str = None):
        self.base_uri = base_uri.rstrip("/")
        self.user = user
        self.password = password
        self.authorization = authorization
        self.cookie = cookie

    def get_projects(self):
        path = "/api/aero/v1/projects"
        return self.__get(path)

    def get_project(self, project_id: int):
        path = f"/api/aero/v1/projects/{project_id}"
        return self.__get(path)

    def create_project(self, name: str, title: str = None):
        path = f"/api/aero/v1/projects"
        params = {
            'name': name,
            'creator': self.user
        }
        if title:
            params['title'] = title
        return self.__post(path, params)

    def get_project_user_permissions(self, project_id: int, user_id: str):
        path = f"/api/aero/v1/projects/{project_id}/permissions/{user_id}"
        return self.__get(path)

    def get_project_documents(self, project_id: int):
        path = f"/api/aero/v1/projects/{project_id}/documents"
        return self.__get(path)

    def get_document_curation(self, project_id: int, document_id: str):
        path = f"/api/aero/v1/projects/{project_id}/documents/{document_id}/curation"
        return self.__get(path)

    def get_document_annotations(self, project_id: int, document_id: str):
        path = f"/api/aero/v1/projects/{project_id}/documents/{document_id}/annotations"
        return self.__get(path)

    def __get(self, path: str):
        url = self.base_uri + path
        logger.info(f"GET {url}")
        if self.authorization:
            # ic(self.authorization, self.cookie)
            return requests.get(
                url,
                headers={
                    "authorization": self.authorization,
                    "cookie": self.cookie
                }
            )
        else:
            # ic(self.user, self.password)
            return requests.get(url, auth=(self.user, self.password))

    def __post(self, path: str, params: Dict):
        url = self.base_uri + path
        logger.info(f"POST {url}")
        if self.authorization:
            # ic(self.authorization, self.cookie)
            return requests.post(
                url=url,
                headers={
                    "authorization": self.authorization,
                    "cookie": self.cookie
                },
                params=params
            )
        else:
            # ic(self.user, self.password)
            return requests.post(url=url, auth=(self.user, self.password), params=params)


@dataclass_json
@dataclass
class Project:
    id: int
    name: str
    title: str


@dataclass_json
@dataclass
class Document:
    id: int
    name: str
    state: str


@dataclass_json
@dataclass
class Annotation:
    user: str
    state: str
    timestamp: str = None


@dataclass_json
@dataclass
class Message:
    level: str
    message: str
