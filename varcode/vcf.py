# Copyright (c) 2014. Mount Sinai School of Medicine
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# required so that 'import vcf' gets the global PyVCF package,
# rather than our local vcf module
from __future__ import absolute_import

from .reference_name import (
    infer_reference_name,
    ensembl_release_number_for_reference_name
)
from .variant import Variant
from .variant_collection import VariantCollection
from . import type_checks
from pyensembl import EnsemblRelease

import vcf # PyVCF

def load_vcf(
        filename,
        reference_path_field='reference',
        only_passing=True,
        ensembl_release=None):
    """
    Load reference name and Variant objects from the given VCF filename.
    Drop any entries whose FILTER field is not one of "." or "PASS".

    Parameters
    ----------

    filename : str

    reference_path_field : str, optional
        Name of metadata field which contains path to reference FASTA
        file (default = 'reference')

    only_passing : boolean, optional
        If true, any entries whose FILTER field is not one of "." or "PASS" is dropped.

    ensembl_release : int, optional
        Which release of Ensembl to use for annotation, by default inferred
        from the reference path.
    """

    type_checks.require_string(filename, "filename")    

    vcf_reader = vcf.Reader(filename=filename)

    if not ensembl_release:
        reference_path = vcf_reader.metadata[reference_path_field]
        reference_name = infer_reference_name(reference_path)
        ensembl_release = ensembl_release_number_for_reference_name(
                reference_name)

    ensembl = EnsemblRelease(release=ensembl_release)
    
    # We ignore "no-call" variants, i.e. those where X.ALT = [None].
    variants = [
        Variant(
            contig=x.CHROM,
            pos=x.POS,
            ref=x.REF,
            alt=x.ALT[0].sequence,
            info=x.INFO,
            ensembl=ensembl)
        for x in vcf_reader
        if x.ALT[0] and (not only_passing or not x.FILTER or x.FILTER == "PASS")
    ]

    return VariantCollection(
        variants=variants,
        original_filename=filename)