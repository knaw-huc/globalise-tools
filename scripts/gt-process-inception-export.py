#!/usr/bin/env python3
import cassis
import hydra
from loguru import logger
from omegaconf import DictConfig


@hydra.main(version_base=None)
@logger.catch
def main(cfg: DictConfig) -> None:
    base = '/Users/bram/workspaces/globalise'
    with open(f'{base}/globalise-tools/data/typesystem.xml', 'rb') as f:
        typesystem = cassis.load_typesystem(f)

    with open(f'{base}/globalise-tools/data/inception_output/NL-HaNA_1.04.02_1090_0313-0322.xmi', 'rb') as f:
        cas = cassis.load_cas_from_xmi(f, typesystem=typesystem)
    main_view = cas.views[0]
    named_entity_annotations = [a for a in main_view.get_all_annotations() if
                                a.type.name == "de.tudarmstadt.ukp.dkpro.core.api.ner.type.NamedEntity"]
    glob_annotations = [a for a in main_view.get_all_annotations() if
                        a.type.name == "webanno.custom.SemPredGLOB"]
    semarg_annotations = [a for a in main_view.get_all_annotations() if
                          a.type.name == "de.tudarmstadt.ukp.dkpro.core.api.semantics.type.SemArg"]
    print(f"{len(named_entity_annotations)} ne annotations")
    print(named_entity_annotations[0])
    print(f"{len(glob_annotations)} glob annotations")
    print(glob_annotations[0])
    print(f"{len(semarg_annotations)} semarg annotations")
    print(semarg_annotations[0])


if __name__ == '__main__':
    main()
