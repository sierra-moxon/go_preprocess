import pystow
from src.processors.orthoprocessor import OrthoProcessor
from src.processors.gafprocessor import GafProcessor
from src.processors.gpiprocessor import GpiProcessor
from src.utils.settings import get_alliance_ortho_url, get_rgd_gpad_url, get_mgi_gpi_url
from typing import List, Dict
from pprint import pprint


def preprocess():
    rat_genes = preprocess_alliance_ortho()
    mouse_genes = preprocess_mgi_gpi()
    for annotation in preprocess_rgd():
        print(annotation)


def preprocess_alliance_ortho() -> Dict[str, str]:
    path = pystow.ensure_gunzip('ORTHO', url=get_alliance_ortho_url())  # autoclean=True, force=False)
    ortho_processor = OrthoProcessor(path)
    rat_genes = {}
    for pair in ortho_processor.get_data().get('data'):
        if pair.get('Gene1SpeciesTaxonID') == 'NCBITaxon:10090' and pair.get('Gene2SpeciesTaxonID') == 'NCBITaxon:10116':
            rat_genes[pair.get('Gene2ID')] = pair.get('Gene1ID')  # rat gene id: mouse gene id
    return rat_genes


def preprocess_rgd() -> Dict[str, List[str]]:
    rgd_gaf_path = pystow.ensure_gunzip('RGD', url=get_rgd_gpad_url())  # autoclean=True, force=True)
    rgd_gaf_processor = GafProcessor(rgd_gaf_path)
    namespaces = ["RGD", "UniProtKB"]
    data = rgd_gaf_processor.get_data(namespaces)
    return data


def preprocess_mgi_gpi() -> List[str]:
    mgi_gpi_path = pystow.ensure_gunzip('MGI', url=get_mgi_gpi_url())  # autoclean=True, force=True)
    mgi_gpi_processor = GpiProcessor(mgi_gpi_path)
    data = mgi_gpi_processor.parse_gpi()
    return data


if __name__ == '__main__':
    preprocess()
