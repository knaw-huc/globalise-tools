#!/usr/bin/env python3
import json
import pathlib
import uuid

import cassis
import hydra
from loguru import logger
from omegaconf import DictConfig

from globalise_tools.events import NAMED_ENTITY_LAYER_NAME, EVENT_LAYER_NAME, ENTITIES


@hydra.main(version_base=None)
@logger.catch
def main(cfg: DictConfig) -> None:
    base = '/Users/bram/workspaces/globalise'
    with open(f'{base}/globalise-tools/data/typesystem.xml', 'rb') as f:
        typesystem = cassis.load_typesystem(f)

    inception_export_path = pathlib.Path(f"{base}/globalise-tools/data/inception_output/")
    xmi_paths = list(inception_export_path.glob("*.xmi"))

    for path in sorted(xmi_paths):
        logger.info(f'<= {path}')
        with open(path, 'rb') as f:
            cas = cassis.load_cas_from_xmi(f, typesystem=typesystem)
        logger.info(f"{len(cas.views)} views")
        main_view = cas.views[0]
        named_entity_annotations = [a for a in main_view.get_all_annotations() if
                                    a.type.name == NAMED_ENTITY_LAYER_NAME]
        glob_annotations = [a for a in main_view.get_all_annotations() if
                            a.type.name == EVENT_LAYER_NAME]
        semarg_annotations = [a for a in main_view.get_all_annotations() if
                              a.type.name == "de.tudarmstadt.ukp.dkpro.core.api.semantics.type.SemArg"]
        print(f"{len(named_entity_annotations)} ne annotations")
        if named_entity_annotations:
            print(named_entity_annotations[0])

        for nea in named_entity_annotations:
            e_uuid = uuid.uuid4()
            class_name = nea.value
            if not class_name:
                logger.warning(f"no className for {nea}")
            else:
                if class_name not in ENTITIES:
                    logger.error(f"unknown className: {class_name} in {nea}")
                else:
                    body = {
                        "@context": {"@vocab": "https://knaw-huc.github.io/ns/team-text#"},
                        "type": "Entity",
                        "id": f"urn:globalise:entity:{e_uuid}",
                        "metadata": {
                            "type": "EntityMetadata",
                            "className": class_name,
                            "classDescription": ENTITIES[class_name],
                            "beginChar": nea.begin,
                            "endChar": nea.end,
                            "text": nea.get_covered_text(),
                        }
                    }
                    print(json.dumps(body, indent=4))
        print()

        print(f"{len(glob_annotations)} glob annotations")
        if glob_annotations:
            print(glob_annotations[0])
        for ga in glob_annotations:
            print(
                f'begin_char={ga.begin}, end_char={ga.end}, text="{ga.get_covered_text()}", category={ga.category}, relationtype={ga.relationtype}')

        print()

        print(f"{len(semarg_annotations)} semarg annotations")
        for sa in semarg_annotations:
            print(f'begin_char={sa.begin}, end_char={sa.end}, text="{sa.get_covered_text()}"')
        print()


if __name__ == '__main__':
    main()

"""
TODO:
- map inception entity annotations to text and image targets
- when creating the xmi, store the text range for the words
- per word, store the image coords and the textanchor range
- now
"""
