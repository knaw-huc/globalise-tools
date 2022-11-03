#!/usr/bin/env python3
import json as JSON
import xml.etree.ElementTree as ET

file = '../data/NL-HaNA_1.04.02_1092_0017.xml'
tree = ET.parse(file)
root = tree.getroot()

json = JSON.loads(root.text)
json2 = JSON.loads(json['na_viewer']['view_response'])
print(JSON.dumps(json2, indent=4))
