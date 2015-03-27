# Copyright (c) 2015. Mount Sinai School of Medicine
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

"""
Effect annotation for variants which modify the coding sequence without
changing the reading frame.
"""

from .translate import transcript_protein_sequence, translate_codon

def in_frame_coding_effect(
        ref,
        alt,
        cds_offset,
        sequence_from_start_codon,
        transcript,
        variant):
    """Coding effect of an in-frame nucleotide change

    Parameters
    ----------
    ref : str
        Reference nucleotides

    alt : str
        Nucleotides to insert in place of the reference nucleotides

    cds_offset : int
        Index of first ref nucleotide, starting from 0 = beginning of coding
        sequence. If variant is a pure insertion (no ref nucleotides) then this
        argument indicates the offset *after* which to insert the `alt`
        nucleotides.

    sequence_from_start_codon : Bio.Seq
        Transcript sequence from the CDS start codon (including the 3' UTR).
        This sequence includes the 3' UTR since a mutation may delete the stop
        codon and we'll have to translate past the normal end of the CDS to
        determine the new protein sequence.

    transcript : Transcript

    variant : Variant
    """

    n_ref_nucleotides = len(ref)

    if n_ref_nucleotides == 0:
        # since insertions interact with the "base counting, one start"
        # coordinates used by VCF & Ensembl to create lots of special cases
        # let's handle all logic for in-frame insertions separately
        return in_frame_insertion_effect(
            inserted_nucleotides=alt,
            cds_offset_before_insertion=cds_offset,
            transcript=transcript,
            variant=variant)

    original_protein_sequence = transcript_protein_sequence(transcript)
    first_ref_amino_acid_index = int(cds_offset / 3)

    assert first_ref_amino_acid_index <= len(original_protein_sequence), \
        ("Unexpected mutation at offset %d (5' UTR starts at %d"
         " while annotating %s on %s") % (
         first_ref_amino_acid_index,
         len(transcript.protein_sequence))

    last_ref_amino_acid_index = int((cds_offset + n_ref_nucleotides - 1) / 3)

    assert last_ref_amino_acid_index >= first_ref_amino_acid_index, \
        ("Expected first_ref_amino_acid_index (%d) <="
         "last_ref_amino_acid_index (%d) while annotating %s on %s") % (
         first_ref_amino_acid_index,
         last_ref_amino_acid_index,
         variant,
         transcript)

    # codons in the reference sequence
    ref_codons = str(sequence_from_start_codon[
        first_ref_amino_acid_index * 3:last_ref_amino_acid_index * 3 + 3])

    # which nucleotide of the codon got changed?
    codon_offset = cds_offset % 3

    mutant_codon = (
        ref_codon[:codon_offset] + alt + ref_codon[codon_offset + 1:])

    assert len(mutant_codon) == 3, \
        "Expected codon to have length 3, got %s (length = %d)" % (
            mutant_codon, len(mutant_codon))

    if aa_pos == 0:
        if mutant_codon in START_CODONS:
            # if we changed the starting codon treat then
            # this is technically a Silent mutation but may cause
            # alternate starts or other effects
            return AlternateStartCodon(
                variant,
                transcript,
                ref_codon,
                mutant_codon)
        else:
            # if we changed a start codon to something else then
            # we no longer know where the protein begins (or even in
            # what frame).
            # TODO: use the Kozak consensus sequence or a predictive model
            # to identify the most likely start site
            return StartLoss(
                variant=variant,
                transcript=transcript,
                aa_alt=translate_codon(mutant_codon, 0))

    original_amino_acid = translate_codon(ref_codon, aa_pos)
    mutant_amino_acid = translate_codon(mutant_codon, aa_pos)

    if original_amino_acid == mutant_amino_acid:
        return Silent(
            variant,
            transcript,
            aa_pos=aa_pos,
            aa_ref=original_amino_acid)
    elif aa_pos == len(transcript.protein_sequence):
        # if non-silent mutation is at the end of the protein then
        # should be a stop-loss
        assert original_amino_acid == "*"
        # if mutatin is at the end of the protein and both
        assert mutant_amino_acid != "*"
        return StopLoss(
            variant,
            transcript,
            aa_pos=aa_pos,
            aa_alt=mutant_amino_acid)
    else:
        # simple substitution e.g. p.V600E
        return Substitution(
            variant,
            transcript,
            aa_pos=aa_pos,
            aa_ref=original_amino_acid,
            aa_alt=mutant_amino_acid)


def in_frame_insertion_effect(
        inserted_nucleotides,
        transcript_offset,
        transcript,
        variant):
    assert len(inserted_nucleotides) > 0, \
        "Expected len(inserted_nucleotides) > 0 for %s on %s" % (
            transcript, variant)

    assert cds_offset_before_insertion < cds_len, \
        "Expected CDS offset (%d) < |CDS| (%d) for %s on %s" % (
            cds_offset, cds_len, variant, transcript)

    if start_codon:
        # IF insertion into start codon, StartLoss
        pass

    if stop_codon:
        # IF insertion into stop codon, StopLoss (scan forward to next stop?)
        pass

    pass
