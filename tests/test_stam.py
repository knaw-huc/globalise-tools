import unittest

from stam import AnnotationStore, Selector, AnnotationDataBuilder, Offset


class StamTestCase(unittest.TestCase):
    def test_stam(self):
        store = AnnotationStore(id="globalise-annotation-store")
        resource = store.add_resource(id="test_res", text="Hello world")
        annotation_set = store.add_annotationset(id="test_dataset")
        key_pos = "pos"
        annotation_set.add_key(key_pos)
        data = annotation_set.add_data(key_pos, "noun", "D1")
        store.annotate(id="A1",
                       target=Selector.text(resource, Offset.simple(6, 11)),
                       data=[AnnotationDataBuilder.link(data)])

        store.to_file("example.stam.json")

        self.assertEqual(key_pos, "pos")


if __name__ == '__main__':
    unittest.main()
