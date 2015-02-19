from .transcript_mutation_effects import *

transcript_effect_priority_list = [
    IncompleteTranscript,
    NoncodingTranscript,
    Intronic,
    ThreePrimeUTR,
    # mutations to the upstream 5' UTR may change the ORF (reading frame),
    # so give 5' UTR mutations higher prioriry
    FivePrimeUTR,
    Silent,
    Substitution,
    Insertion,
    Deletion,
    ComplexSubstitution,
     # intronic variants near the splice boundaries but which aren't
    # the two nucleotides closest to the exon
    IntronicSpliceSite,
    # exonic variants near a splice boundary
    ExonicSpliceSite,
    # modification or deletion of stop codon
    StopLoss,
    # mutation in the two nucleotides immediately following an exon/intron
    # boundary
    SpliceDonor,
    # mutation in the two nucleotides immediately preceding an intron/exon
    # boundary
    SpliceAcceptor,
    PrematureStop,
    # frame-shift which creates immediate stop codon, same as PrematureStop
    FrameShiftTruncation,
    # modification or deletion of a start codon
    StartLoss,
    # out-of-frame insertion or deletion
    FrameShift
]

transcript_effect_priority_dict = {
    transcript_effect_class : priority
    for (priority, transcript_effect_class)
    in enumerate(transcript_effect_priority_list)
}

def effect_priority(effect):
    """
    Returns the integer priority for a given transcript effect
    """
    # since intergenic variants may have a None value for their
    # highest_priority effect it simplifies other code to handle None
    # here
    if effect is None:
        return -1
    return transcript_effect_priority_dict[effect.__class__]

def top_priority_transcript_effect(effects):
    """
    Given a collection of variant transcript effects,
    return the top priority object. In case of multiple transcript
    effects with the same priority, return the one affecting the longest
    transcript.
    """
    if len(effects) == 0:
        raise ValueError("List of effects cannot be empty")

    best_effects = []
    best_priority = -1
    for effect in effects:
        priority = effect_priority(effect)
        if priority > best_priority:
            best_effects = [effect]
            best_priority = priority
        elif priority == best_priority:
            best_effects.append(effect)

    if any(effect.transcript.complete for effect in best_effects):
        # if any transcripts have complete coding sequence annotations,
        # filter the effects down to those that are complete and sort
        # them by length of the coding sequence
        best_effects = [
            effect
            for effect in best_effects
            if effect.transcript.complete
        ]
        key_fn = lambda effect: len(effect.transcript.coding_sequence)
    else:
        # if effects are over incomplete transcripts, sort them by the
        # their total transcript length
        key_fn = lambda effect: len(effect.transcript)
    return max(best_effects, key=key_fn)
