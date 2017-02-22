from __future__ import division
import argparse
import pandas as pd
import pysam
import copy
import numpy as np


parser = argparse.ArgumentParser(description='This script is designed to read in a csv of putative variant calls from deepSNV and query the bam file for the number of reads matching the reference base at that position.',usage ="python reciprocal_variants.py sample.bam sample.csv")

parser.add_argument('bam', metavar='bam', nargs='+',
                    help='The bam file of the sample')
parser.add_argument('csv', metavar='csv', nargs='+',
                    help='The deepSNV csv file')


class meta_qual(object):
    def __init__(self):
        self.mapq=[]
        self.phred=[]
        self.read_pos=[]



# class test_args: # for debugging and testing
#     csv = ["~/Desktop/scratch/1139.removed.csv"]
#     bam = ["/Users/jt/Desktop/scratch/1139.removed.bam"]
#args=test_args()

args=parser.parse_args()    
variants=pd.read_csv(args.csv[0],index_col=False)
bam= pysam.AlignmentFile(args.bam[0], "rb") 

def get_reference(row,bam):
    # grab some data from the first series.
    chr=row["chr"]
    pos=int(row["pos"])
    py_pos=pos-1 # pythonify the position
    ref=row["ref"]
    var=row["var"]
    deepsnv_n_fw=row["n.tst.fw"]
    deepsnv_n_bw=row["n.tst.bw"]
    deepsnv_cov_fw=row["cov.tst.fw"]
    deepsnv_cov_bw=row["cov.tst.bw"]
    ref_qual=meta_qual()
    var_qual=meta_qual()
    fw=0
    bw=0
    cov_fw=0
    cov_bw=0
    for pileupcolumn in bam.pileup(chr,py_pos,py_pos+1,truncate=True,stepper="all",max_depth=1E6): # look at the range py_pos to py_pos+1 and all the bases that align to those positions. Think of a column on each position like the samtools output of mpileup
        if pileupcolumn.pos==py_pos: #If the position is the one we want don't need 
            for pileupread in pileupcolumn.pileups: #Now for each read in that column
                if pileupread.alignment.is_reverse:
                    if  not pileupread.is_del and not pileupread.is_refskip:
                        called_base=pileupread.alignment.query_sequence[pileupread.query_position] # what is the called base at the position
                        called_phred=pileupread.alignment.query_qualities[pileupread.query_position] # what is the phred of that base
                        if called_phred>30 : # change this if you change the phred cut off in deepSNV. deepSNV only looks a phred>30. and we only want those calles that match the variant.
                             cov_bw +=1
                             if called_base==ref:
                                 bw +=1
                                 ref_qual.mapq.append(pileupread.alignment.mapping_quality)# add the mapping quality of the read to the list
                                 ref_qual.phred.append(called_phred)
                                 ref_qual.read_pos.append(pileupread.query_position)
                             if called_base==var:
                                 var_qual.mapq.append(pileupread.alignment.mapping_quality)# add the mapping quality of the read to the list
                                 var_qual.phred.append(called_phred)
                                 var_qual.read_pos.append(pileupread.query_position)
                                 
                    else : # deepSNV does not through out indels they are included in the coverage. We count them as well for consistency.
                         cov_bw +=1 
                if not pileupread.alignment.is_reverse:
                    if  not pileupread.is_del and not pileupread.is_refskip:
                        called_base=pileupread.alignment.query_sequence[pileupread.query_position] # what is the called base at the position
                        called_phred=pileupread.alignment.query_qualities[pileupread.query_position] # what is the phred of that base
                        if called_phred>30: # change this if you change the phred cut off in deepSNV. deepSNV only looks a phred>30. and we only want those calles that match the variant.
                            cov_fw +=1
                            if called_base==ref:
                                fw +=1
                                ref_qual.mapq.append(pileupread.alignment.mapping_quality)# add the mapping quality of the read to the list
                                ref_qual.phred.append(called_phred)
                                ref_qual.read_pos.append(pileupread.query_position)
                            if called_base==var:
                                var_qual.mapq.append(pileupread.alignment.mapping_quality)# add the mapping quality of the read to the list
                                var_qual.phred.append(called_phred)
                                var_qual.read_pos.append(pileupread.query_position)
                    else:  # deepSNV does not through out indels they are included in the coverage.
                         cov_fw +=1
    # Append needed columns for var
    row["MapQ"]=np.mean(var_qual.mapq)
    row["Phred"]=np.mean(var_qual.phred)
    row["Read_pos"]=np.mean(var_qual.read_pos)
    # build output for ref
    ref_out=copy.deepcopy(row)
    ref_out["var"]=ref
    ref_out["n.tst.fw"]=fw
    ref_out["n.tst.bw"]=bw
    ref_out["cov.tst.fw"]=cov_fw
    ref_out["cov.tst.bw"]=cov_bw
    ref_out["freq.var"]=(fw+bw)/(cov_fw+cov_bw)
    ref_out["p.val"]="NA"
    ref_out["sigma2.freq.var"]="NA"
    ref_out["n.ctrl.fw"]="NA"
    ref_out["n.ctrl.bw"]="NA"
    ref_out["raw.p.val"]="NA"
    ref_out["mutation"]=ref_out["chr"]+"_"+ref_out["ref"]+str(ref_out["pos"])+ref_out["var"]
    ref_out["MapQ"]=np.mean(ref_qual.mapq)
    ref_out["Phred"]=np.mean(ref_qual.phred)
    ref_out["Read_pos"]=np.mean(ref_qual.read_pos)

    # verify everything is up to snuff
    if not len(var_qual.mapq)==len(var_qual.phred) and len(var_qual.phred)==len(var_qual.read_pos) and len(var_qual.read_pos)==(deepsnv_n_fw+deepsnv_n_bw):
        raise ValueError, 'We did not find the same number of variant bases as deepSNV - something is up'
    if not len(ref_qual.mapq)==(ref_out["n.tst.fw"]+ref_out["n.tst.bw"]):
        raise ValueError, "Didn't get the same number of reference qualities as bases- something is up"
    if not cov_bw==deepsnv_cov_bw:
        raise ValueError, 'We did not find the same number of reverse reads as deepSNV - something is up'
    if not cov_fw==deepsnv_cov_fw:
        raise ValueError, 'We did not find the same number of forward reads as deepSNV - something is up'
    
    return([row,ref_out])
    
inferred_qual=pd.DataFrame()
for index, row in variants.iterrows():
    meta_bases=get_reference(row,bam)                                                    
    inferred_qual=inferred_qual.append(meta_bases[0])
    inferred_qual=inferred_qual.append(meta_bases[1])

print inferred_qual

# remove duplicate rows if applicable

# write output to csv