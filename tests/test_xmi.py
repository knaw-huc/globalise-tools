import unittest
from datetime import datetime

from icecream import ic
from loguru import logger

import globalise_tools.io_tools as rw
from scripts.gt_create_annotation_lists_for_inventory_number import _add_classified
from scripts.gt_ner_xmi_to_wa import XMIProcessorFactory


class XMITestCase(unittest.TestCase):
    @logger.catch(reraise=True)
    def test_original(self):
        # file_path = "./NL-HaNA_1.04.02_3598_0797.xmi"
        xmi_path = ".local/p_80-ner-event-preanno_NL-HaNA_1.04.02_3598_0797-0809 - 1781 -.xmi"
        type_system_path = "data/typesystem.xml"
        ts = datetime.today().isoformat()
        timespan4inventory = {
            ".local": {
                "type": "TimeSpan",
                "end_of_the_begin": ts,
                "begin_of_the_end": ts,
            }
        }
        xpf = XMIProcessorFactory(typesystem_path=type_system_path, timespan4inventory={}, event_mapping={})
        xp = xpf.get_xmi_processor(xmi_path=xmi_path, htr_offset={})
        entity_annotations = [a for a in xp.cas.views[0].get_all_annotations() if
                              a.type.name == "de.tudarmstadt.ukp.dkpro.core.api.ner.type.NamedEntity" and a.value]

        print()
        print(xp.cas.sofas[0].sofaString)
        for a in entity_annotations:
            print(f"NamedEntity {a.xmiID:3}: {a.begin:4}:{a.end:4} - {a.value:12} :", a.get_covered_text())
        self.assertEqual(1, 1)

    def test_event_mapping_fix(self):
        raw_event_mapping = rw.read_json("data/eventmapping.json")
        event_mapping = _add_classified(raw_event_mapping)
        self.assertNotEqual(event_mapping["AlteringARelationship"], raw_event_mapping["AlteringARelationship"])
        self.assertNotEqual(event_mapping, raw_event_mapping)


if __name__ == '__main__':
    unittest.main()
