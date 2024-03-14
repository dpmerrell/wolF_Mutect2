
from .reference_files import m2_ref_files
from .tasks import *

"""
    Run a MuTect2 somatic variant calling workflow on 
    a tumor-normal pair:
        * Scatter/gather MuTect2 across intervals of the genome
        * Compute contamination
        * Filter the calls: PoN filter, gnomAD, alignment artifacts, etc.
        * Annotate the calls with Funcotator

    kwargs:
        ref_build {"hg38", "hg19"}: default "hg38"
        sequencing_type {"WGS", "WES"}: default "WGS"

    Default reference files can be overridden by specifying
    them as kwargs. Important ones:
        * ref_fasta
        * gnomad_vcf
"""
def mutect2_workflow(pair_name, t_name, n_name,
                     t_bam, t_bai,
                     n_bam, n_bai,
                     ref_build="hg38",
                     sequencing_type="WGS",
                     scatter_count=10,
                     ref_files_override={},
                     ):

    ref_files = m2_ref_files[ref_build]
    ref_files = {**ref_files, **ref_files[sequencing_type]}
    ref_files = {**ref_files, **ref_files_override}

    results = {}

    # Split intervals
    intervals = SplitIntervals(inputs=dict(ref_fasta=ref_files["fasta"],
                                           ref_fasta_index=ref_files["fasta_idx"],
                                           ref_fasta_dict=ref_files["fasta_dict"],
                                           interval_list=ref_files["split_intervals"], 
                                           scatter_count=scatter_count
                                          )
                              )["subintervals"]

    # Get the sample names from the BAMs
    sample_names = GetSampleNames(inputs=dict(tumor_bam=t_bam,
                                              normal_bam=n_bam
                                             )
                                 )

    # MuTect2 scatter          
    m2_outputs = Mutect2(inputs=dict(case_name=sample_names["tumor_name"],
                                     ctrl_name=sample_names["normal_name"],
                                     t_bam=t_bam, 
                                     t_bai=t_bai,
                                     n_bam=n_bam, 
                                     n_bai=n_bai,
                                     ref_fasta=ref_files["fasta"],
                                     ref_fasta_index=ref_files["fasta_idx"],
                                     ref_fasta_dict=ref_files["fasta_dict"],
                                     gnomad_vcf=ref_files["gnomad_vcf"],
                                     gnomad_vcf_idx=ref_files["gnomad_vcf_idx"],
                                     pon_vcf=ref_files["pon_vcf"],
                                     pon_vcf_idx=ref_files["pon_vcf_idx"],
                                     interval=intervals
                                    )
                         )

    # MuTect2 gather
    m2g_outputs = MergeVCFs(inputs=dict(all_vcf_input=[m2_outputs["scatter_vcf"]]
                                           )
                               )
    results["merged_unfiltered_vcf"] = m2g_outputs["merged_unfiltered_vcf"]

    # Pileup summary scatter (for tumor and normal, separately)
    tumor_pileups = GetPileupSummaries(inputs={
                        "bam": t_bam, "bai": t_bai,
                        "ref_fasta": ref_files["fasta"],
                        "ref_fasta_index": ref_files["fasta_idx"],
                        "ref_fasta_dict": ref_files["fasta_dict"],
                        "contamination_vcf": ref_files["contamination_vcf"],
                        "contamination_vcf_idx": ref_files["contamination_vcf_idx"],
                        "interval" : intervals,
                        "command_mem": "4",
                        }
                    )["pileups"]
    normal_pileups = GetPileupSummaries(inputs={
                        "bam": n_bam, "bai": n_bai,
                        "ref_fasta": ref_files["fasta"],
                        "ref_fasta_index": ref_files["fasta_idx"],
                        "ref_fasta_dict": ref_files["fasta_dict"],
                        "contamination_vcf": ref_files["contamination_vcf"],
                        "contamination_vcf_idx": ref_files["contamination_vcf_idx"],
                        "interval" : intervals,
                        "command_mem": "4",
                        }
                    )["pileups"]

    # Pileup summary gather
    tumor_pileup = GatherPileupSummaries(inputs={
                       "all_pileups": [tumor_pileups],
                       "ref_fasta_dict": ref_files["fasta_dict"],
                       }
                   )["gathered_pileup"]
    normal_pileup = GatherPileupSummaries(inputs={
                       "all_pileups": [normal_pileups],
                       "ref_fasta_dict": ref_files["fasta_dict"],
                       }
                   )["gathered_pileup"]

    # Compute contamination

    # Filter variant calls

    # Filter alignment artifacts

    # Funcotator 

    return results

