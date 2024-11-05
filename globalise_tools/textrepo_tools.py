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


def get_iiif_base_url(client: TextRepoClient, external_id: str) -> str:
    meta = client.find_document_metadata(external_id)[1]
    return meta['scan_url'].replace('/info.json', '')


def get_iiif_url(client: TextRepoClient, external_id: str) -> str:
    scan_url = get_iiif_base_url(client, external_id)
    return f"{scan_url}/full/max/0/default.jpg"
