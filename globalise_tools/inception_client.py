import re
from dataclasses import dataclass
from typing import Dict, Any, List, TextIO

import requests
from dataclasses_json import dataclass_json
from icecream import ic
from loguru import logger
from requests import Response

PROJECTS_PATH = "/api/aero/v1/projects"


class InceptionClient:

    def __init__(self,
                 base_uri: str,
                 user: str = None,
                 password: str = None,
                 authorization: str = None,
                 oauth2_proxy: str = None):
        self.base_uri = base_uri.rstrip("/")
        self.user = user
        self.password = password
        self.authorization = authorization
        self.cookies = {'_oauth2_proxy': oauth2_proxy}

    def get_projects(self):
        path = f"{PROJECTS_PATH}"
        return self.__get(path)

    def get_project(self, project_id: int):
        path = f"{PROJECTS_PATH}/{project_id}"
        return self.__get(path)

    def create_project(self, name: str, title: str = None):
        path = f"{PROJECTS_PATH}"
        params = {
            'name': name,
            'creator': self.user
        }
        if title:
            params['title'] = title
        return self.__post(path, params=params)

    def get_project_user_permissions(self, project_id: int, user_id: str):
        path = f"{PROJECTS_PATH}/{project_id}/permissions/{user_id}"
        return self.__get(path)

    def get_project_documents(self, project_id: int):
        path = f"{PROJECTS_PATH}/{project_id}/documents"
        return self.__get(path)

    def create_project_document(self, project_id: int, file_path: str, name: str, file_format: str, state: str = None):
        path = f"{PROJECTS_PATH}/{project_id}/documents"
        rx = '[' + re.escape(''.join('\x00!"#$%&\'*+/:<=>?@\\`{|}')) + ']'
        acceptable_name = re.sub(rx, '', name)[:200].strip()
        params = {
            'name': acceptable_name,
            'format': file_format
        }
        if state:
            params['state'] = state
        with open(file_path) as file:
            return self.__post(path, params=params, file=file)

    def get_document_curation(self, project_id: int, document_id: str):
        path = f"{PROJECTS_PATH}/{project_id}/documents/{document_id}/curation"
        return self.__get(path)

    def get_document_annotations(self, project_id: int, document_id: str):
        path = f"{PROJECTS_PATH}/{project_id}/documents/{document_id}/annotations"
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
                    "cookie": self.cookies
                }
            )
        else:
            # ic(self.user, self.password)
            return requests.get(url, auth=(self.user, self.password))

    def __post(self, path: str, params: Dict, file: TextIO = None):
        url = self.base_uri + path
        logger.info(f"POST {url}")
        if self.authorization:
            # ic(self.authorization, self.cookie)
            response = requests.post(
                url=url,
                headers={
                    "authorization": self.authorization
                },
                params=params,
                cookies=self.cookies,
                files={'content': file}
            )
        else:
            # ic(self.user, self.password)
            response = requests.post(url=url, auth=(self.user, self.password), params=params, files={'content': file})
        json = response.json()
        ic(response, json)
        return InceptionAPIResponse(response=response, body=json['body'], messages=json['messages'])


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


@dataclass
class InceptionAPIResponse:
    response: Response
    body: Any
    messages: List[Message]
