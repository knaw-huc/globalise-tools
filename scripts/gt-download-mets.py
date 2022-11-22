import requests
import csv

data_dir = '/Users/bram/workspaces/globalise/globalise-tools/data'

with open(f'{data_dir}/NL-HaNA_1.04.02_mets.csv') as f:
    records = [r for r in csv.DictReader(f) if r['METS link'] != '']

for r in records:
    url = r['METS link']
    mets_id = to_mets_id(url)
    print(f"reading {url}...")
    r = requests.get(url)
    if r.ok:
        xml = r.text
        path = f'{data_dir}/mets/{mets_id}.xml'
        with open(path, 'w') as f:
            print(f"writing to {path}...")
            f.write(xml)
    else:
        print(r)
