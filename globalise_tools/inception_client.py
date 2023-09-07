import re
from dataclasses import dataclass
from typing import Dict, Any, List, TextIO, Union

import requests
from dataclasses_json import dataclass_json
from icecream import ic
from loguru import logger
from requests import Response
from requests.cookies import cookiejar_from_dict

PROJECTS_PATH = "/api/aero/v1/projects"


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


class InceptionClient:

    def __init__(self,
                 base_uri: str,
                 user: str = None,
                 password: str = None,
                 authorization: str = None,
                 oauth2_proxy: str = None):
        self.base_uri = base_uri.rstrip("/")
        self.user = user
        self._prepare_session(authorization, oauth2_proxy, password, user)

    def _prepare_session(self, authorization: str, oauth2_proxy: str, password: str, user: str):
        self.session = requests.Session()
        self.session.headers = {
            'User-Agent': 'inception-python-client'
        }
        if authorization:
            self.session.headers["authorization"] = authorization
            self.session.cookies = cookiejar_from_dict({'_oauth2_proxy': oauth2_proxy})
        else:
            self.session.auth = (user, password)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        # logger.info(f"closing session with args: {args}")
        self.session.close()

    def close(self):
        self.__exit__()

    def get_projects(self) -> List[Project]:
        path = f"{PROJECTS_PATH}"
        result = self.__get(path)
        return [Project.from_dict(d) for d in result.body]

    def get_project_by_id(self, project_id: int) -> InceptionAPIResponse:
        path = f"{PROJECTS_PATH}/{project_id}"
        return self.__get(path)

    def get_project_by_name(self, name: str) -> Union[Project, None]:
        matches = [p for p in (self.get_projects()) if p.name == name]
        if matches:
            return matches[0]
        else:
            return None

    def create_project(self, name: str, title: str = None) -> InceptionAPIResponse:
        path = f"{PROJECTS_PATH}"
        params = {
            'name': name,
            'creator': self.user
        }
        if title:
            params['title'] = title
        return self.__post(path, params=params)

    def get_project_user_permissions(self, project_id: int, user_id: str) -> InceptionAPIResponse:
        path = f"{PROJECTS_PATH}/{project_id}/permissions/{user_id}"
        return self.__get(path)

    def get_project_documents(self, project_id: int) -> InceptionAPIResponse:
        path = f"{PROJECTS_PATH}/{project_id}/documents"
        return self.__get(path)

    def get_project_document(self, project_id: int, document_id: int,
                             export_format: str = "xmi-xml1.1") -> str:
        path = f"{PROJECTS_PATH}/{project_id}/documents/{document_id}?format={export_format}"
        return self.__get(path, get_text=True)

    def create_project_document(self, project_id: int, file_path: str, name: str, file_format: str,
                                state: str = None) -> InceptionAPIResponse:
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

    def get_document_curation(self, project_id: int, document_id: str) -> InceptionAPIResponse:
        path = f"{PROJECTS_PATH}/{project_id}/documents/{document_id}/curation"
        return self.__get(path)

    def get_document_annotations(self, project_id: int, document_id: str) -> InceptionAPIResponse:
        path = f"{PROJECTS_PATH}/{project_id}/documents/{document_id}/annotations"
        return self.__get(path)

    def __get(self, path: str, get_text: bool = False) -> Union[InceptionAPIResponse, str]:
        url = self.base_uri + path
        logger.debug(f"GET {url}")
        response = self.session.get(url)
        if get_text:
            return response.text
        else:
            return as_inception_api_response(response)

    def __post(self, path: str, params: Dict, file: TextIO = None) -> InceptionAPIResponse:
        url = self.base_uri + path
        logger.debug(f"POST {url}")
        response = self.session.post(url=url,
                                     params=params,
                                     files={'content': file})
        return as_inception_api_response(response)


def as_inception_api_response(response):
    json = response.json()
    ic(response, json)
    return InceptionAPIResponse(response=response, body=json['body'], messages=json['messages'])
