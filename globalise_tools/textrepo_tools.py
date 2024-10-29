from textrepo.client import TextRepoClient, FileType


def get_file_type(client: TextRepoClient, file_type_name, mimetype) -> FileType:
    if client.has_file_type_with_name(file_type_name):
        file_type = client.find_file_type(file_type_name)
    else:
        file_type = client.create_file_type(file_type_name, mimetype)
    return file_type


def get_plain_text_file_type(client: TextRepoClient) -> FileType:
    return get_file_type(client, 'txt', 'text/plain')


def get_xmi_file_type(client: TextRepoClient) -> FileType:
    return get_file_type(client, 'xmi', 'application/vnd.xmi+xml')
