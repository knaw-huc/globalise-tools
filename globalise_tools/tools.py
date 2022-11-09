def na_url(file_path):
    file_name = file_path.split('/')[-1]
    inv_nr = file_name.split('_')[2]
    file = file_name.replace('.xml', '')
    return f"https://www.nationaalarchief.nl/onderzoeken/archief/1.04.02/invnr/{inv_nr}/file/{file}"
