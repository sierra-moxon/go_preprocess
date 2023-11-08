"""Protein 2 GO AnnotationConverter class."""
import copy
import datetime
from typing import Any, Optional

import pystow
from ontobio.model.association import Curie, GoAssociation

from src.gopreprocess.file_processors.gaf_processor import GafProcessor
from src.gopreprocess.file_processors.gpi_processor import GpiProcessor
from src.utils.decorators import timer
from src.utils.download import download_file


def generate_annotation(annotation: GoAssociation, xrefs: dict) -> GoAssociation:
    """
    Generate a new annotation based on the given protein 2 GO annotation.

    :param annotation: The protein 2 GO annotation.
    :type annotation: GoAssociation
    :param xrefs: The xrefs dictionary from the parsed GPI file, mapping the gene of the target
    species to the set of UniProt ids for the source - in this case, the source is the protein 2 GO GAF file,
    so really we're still dealing with the source taxon.

    :return: A new annotation.
    :rtype: GoAssociation
    """
    if annotation.subject.id in xrefs.keys():
        new_gene = Curie(namespace="MGI", identity=xrefs[annotation.subject.id].replace("MGI:MGI:", "MGI:"))
        new_annotation = copy.deepcopy(annotation)
        # not sure why this is necessary, but it is, else we get a Subject with an extra tuple wrapper
        new_annotation.subject.id = new_gene
        new_annotation.subject.synonyms = []
        new_annotation.object.taxon = Curie.from_str("NCBITaxon:10090")
        new_annotation.provided_by = "GO_Central"
        return new_annotation
    else:
        return None


def get_source_annotations(isoform: bool, taxon: str) -> tuple[dict, Any, Optional[Any]]:
    """
    Get the source annotations from the protein 2 GO GAF file.

    :param isoform: Whether to process isoform annotations.
    :type isoform: bool
    :param taxon: The target taxon to which the annotations belong.
    :type taxon: str
    :return: A tuple containing the xrefs dictionary, the source annotations, and optionally the isoform
    source annotations.
    :rtype: tuple[dict, Any]
    """
    taxon = taxon.replace("NCBITaxon:", "taxon_")
    p2go_file = download_file(target_directory_name=f"GOA_{taxon}", config_key=f"GOA_{taxon}", gunzip=True)

    target_gpi_path = download_file(target_directory_name="MGI_GPI", config_key="MGI_GPI", gunzip=True)

    gpi_processor = GpiProcessor(target_gpi_path)
    xrefs = gpi_processor.get_xrefs()

    # assign the output of processing the source GAF to a source_annotations variable
    gp = GafProcessor(filepath=p2go_file)
    source_annotations = gp.parse_p2g_gaf()

    if isoform:
        p2go_isoform_file = download_file(
            target_directory_name=f"GOA_{taxon}_ISOFORM", config_key=f"GOA_{taxon}_ISOFORM", gunzip=True
        )
        gp_isoform = GafProcessor(filepath=p2go_isoform_file)
        source_isoform_annotations = gp_isoform.parse_p2g_gaf()
        return xrefs, source_annotations, source_isoform_annotations
    else:
        return xrefs, source_annotations, None


def dump_annotations(annotations, isoform):
    """Dump annotations to a file."""
    file_suffix = "-isoform" if isoform else ""
    header_filepath = pystow.join(
        key="GAF_OUTPUT",
        name=f"mgi-p2g-converted{file_suffix}.gaf",
        ensure_exists=True,
    )
    with open(header_filepath, "w") as file:
        file.write("!gaf-version: 2.2\n")
        file.write("!Generated by: GO_Central preprocess pipeline: protein to GO transformation\n")
        file.write("!Date Generated: " + str(datetime.date.today()) + "\n")
        for annotation in annotations:
            file.write("\t".join(map(str, annotation)) + "\n")


class P2GAnnotationCreationController:

    """Converts annotations from one species to another based on ortholog relationships between the two species."""

    def __init__(self):
        """Initialize the AnnotationConverter class."""

    @timer
    def convert_annotations(self, isoform: bool, taxon: str) -> None:
        """
        Convert Protein to GO annotations from source to target taxon.

        :param isoform: Whether to process isoform annotations.
        :type isoform: bool
        :param taxon: The target taxon to which the annotations belong.
        :type taxon: str
        :returns: None
        """
        # Gather source annotations and cross-references
        source_annotations, xrefs, isoform_annotations = get_source_annotations(isoform=isoform, taxon=taxon)

        # Convert source annotations to target format
        converted_target_annotations = [
            annotation_obj.to_gaf_2_2_tsv()
            for annotation in source_annotations
            if (annotation_obj := generate_annotation(annotation=annotation, xrefs=xrefs)) is not None
        ]

        # Dump non-isoform annotations
        dump_annotations(converted_target_annotations, isoform=False)

        # Process isoform annotations if required
        if isoform:
            converted_target_isoform_annotations = [
                annotation_obj.to_gaf_2_2_tsv()
                for annotation in isoform_annotations
                if (annotation_obj := generate_annotation(annotation=annotation, xrefs=xrefs)) is not None
            ]

            # Dump isoform annotations
            dump_annotations(converted_target_isoform_annotations, isoform=True)