# Pipeline Tutorial

_Note: Some aspects of this tutorial are specific to lab needs please feel free to skip ahead as needed._
In this example we will run a small data set through using a command line approach. We are working with one MFE sample and a wsn33 plasmid control. For computational speed, these fastq files have been reduced by 75%. This approach can be run on flux as is, or run through a pbs for larger data sets. The last section provides instructions for working with real data.

For consistency all of the commands can be run from the variant_pipeline/tutorial directory. If you are running this from a different directory (for example, when you are working with your real data on scratch in section 4), make sure the paths to your files are correct. You may need to edit them in the commands provided.

## Table of Contents

-   [Before you begin](#before-you-begin)
-   [0) Getting started](#getting-started)
-   [1) Fastq setup](#fastq-setup)
-   [2) Running the pipeline](#running-the-pipeline)
-   [3) Analysis](#analysis)
-   [4) Working with real data](#working-with-real-data)

<a name="before-you-begin"/>

## Before you begin

You will need:

-   Access to the lab's allocation on flux. Adam will need to email the administrator at hpc.
-   Some form of two factor identification.
-   Know basic unix commands. See tutorials and lists on Mbox/Lauring Lab/Command Line Tools.
-   Know the basics of flux organization and access. See Ten easy steps in MBox/Lauring Lab/Command Line Tools.

<a name="getting-started"/>

## 0) Getting started

First things first we need to get a version of this repository onto the high computing cluster so that you can use it. This can be done a number of ways. Here we will outline how to first fork your own version of this repository. This will be useful as you may wish to contribute to the project in the future. Please log into flux following the steps below. Then you can fork and clone the repository using the tutorial found [here](http://blog.swilliams.me/words/2015/06/30/basic-github-workflow-for-collaboration/)

Log onto the flux platform by typing the following in a terminal window.

```
ssh your_username@flux-login.arc-ts.umich.edu
```

You will be asked for your level one. No characters appear as you type.

You will then be prompted for your prefered method of two level identification.

Once on flux you will automatically begin in your home directory (~/ which is a shortcut for /home/username/ ). You can use the unix command "pwd" to see your location. At this point you should see /home/your_username. We will add the variant pipeline to our home directory so it is easily accessible from anywhere.

Now we will follow [this](http://blog.swilliams.me/words/2015/06/30/basic-github-workflow-for-collaboration/) collaboration tuturial. Our first task will be to fork the lab's repository to our own account. To do this click the fork icon at the top right of this page.

Next we will clone your version of the repository onto the flux

On flux type

```
git clone https://github.com/username/variant_pipeline.git
```

where username is your github username.

The next step is to set up remotes. These allow your local version on flux to communicate with github. This repository will have two remotes 'origin' is your own version on github, and 'upstream' which will be the lab's master version. Origin was set up when you forked the repository. To set up 'upstream' use the following command.

```
cd variant_pipeline
git remote add upstream https://github.com/lauringlab/variant_pipeline.git
```

Now it is possible to keep your version up to date with the master copy by using

```
git pull upstream master
```

## 0.1) Dependencies

To run these all pipelines you must have the java developer kit installed. It can be installed from [here](http://www.oracle.com/technetwork/java/javase/downloads/jdk8-downloads-2133151.html). If bpipe doesn't run this is the first place to start.

All the other depedencies, except R and the R packages, are handled by conda. Install conda by following the tutorial [here](https://conda.io/docs/user-guide/overview.html).

We can install the conda environment with the following command (run from the variant_pipeline/ directory)

```
conda env create -f scripts/environment.yml
```

We have to activate the environment before running the commands below.

```
conda activate variant-pipeline
```

On flux we can achieve an equivalent environment with a few commands. First run:

```
module load muscle bowtie2 fastqc R/3.5.0
```

Now we need to set up the R modules. The R modules are managed by packrat. I am using R 3.5.0. From the main directory run

```
R
packrat::restore()
```

to download the needed dependencies. They should be placed the packrat/lib directory. This is important since the R script will look for them there. You may need to install packrat first if you don't have it.

After the R dependencies are loaded, exit the R session by calling q(). Now finish loading the modules with the following command:

```
module load python-anaconda2/201704
```

We should now have an equivalent environment set up on flux. (Note that in variant_pipeline/bin/variantPipeline.py, we specify the R_lib path to use R version 3.5.0. This would need to be modified for newer versions of R.) 

Now the code is installed and the dependencies are sorted, we are ready to begin the tutorial. Let's go there now, by moving to the tutorial subdirectoy within the variant_pipeline directory.

```
cd tutorial
```

The variant pipeline runs in two stages. The first aligns and processes the fastq files. The second identifies variants. Each stage is defined by a bpipe pipeline that can be initiated using bin/variantPipeline.py.

There are two options to call variants. The first relies on the R package deepSNV to calulcate a base specific error rate using a plasmid control. Putative variants can then be filtered based on average phred score, average mapping quality, frequency and average position in the read. This pipeline outputs a deepSNV csv file for containing all variant calls. **NOTE: the variant calles from this pipeline are from deepSNV and are base 1. i.e. the first position of each segment is 1.**

The second variant calling pipeline uses python scripts to identify all alleles present in the bam file. It does not provide a p.value or any measurement of certainty for each variant. The output from this pipeline is a json file containing mimum meta data for each file and all vatiant call. **NOTE: the variant calles from this pipeline are from python and are base 0. i.e. the first position of each segment is 0 not 1.**

<a name="fastq-setup"/>

## 1) Fastq setup

The first step is to name the fastq file in the manner the pipeline expects. We require the fastq file to be named in the following format _sample_name.read_direction.#.fastq_, where # is the number of fastq file for the given sample and read direction (usually 1 for miseq) and read*direction is a 1 or 2, indicating forward or reverse reads. \_Note: I don't think illumina limits fastq files anymore and so the # notation may be a bit out-dated. We should think about updating the pipeline so this is no longer a requirement*

To do this we'll use the change_names_miseq.py script (when working with hiseq runs naming is slightly different we can use the change_names_hiseq.py script). Before running the script, we will test it to make sure we are naming things as we expect. Note that the script will copy the original files to a new file. This leaves the original unchanged. Additionally, the script will not copy anything unless you run it with the -run flag. Omitting this flag runs the program in test mode. It will print what it proposes to do and make a mock log. This ensures you don't do anything hastily. For more information about the script simply type

```
python ../scripts/change_names_miseq.py -h
```

_Note: if the final directory ("data/fastq" in this case) doesn't exist it will be made. **Also, fastq files are gzipped when we get them from the sequencing core (they end in .gz). This script will detect files that end in ".fastq" and ".fastq.gz". It will copy the unzipped and gzipped files from the -s directory (data/fastq_original/) to -f (data/fastq/), but it will not unzip them. To do that use the gunzipp command. This may take some time for large files**_

Let's test the renaming script.

```
python ../scripts/change_names_miseq.py -s data/fastq_original/ -f data/fastq/
```

Everything looks good so lets do it for real by adding the -run option

```
python ../scripts/change_names_miseq.py -s data/fastq_original/ -f data/fastq/ -run
```

_Note: a log of the name changes was made in fastq/renaming_log.txt for posterity_

unzip the files if needed.

```
gunzip -v data/fastq/*gz
```

Now that we have our samples prepped we can run the pipeline.

<a name="running-the-pipeline"/>

## 2) Running the aligning pipeline

The pipeline is run by in [bpipe](https://code.google.com/p/bpipe/wiki/Overview) using a python wrapper. The wrapper converts an yaml options file into the format needed by the pipeline stages. It also copies the stages.groovy and pipeline.groovy scripts from the scripts directory in variant_pipeline to the working directory and then runs the pipeline. To see our options type.

```
python ../bin/variantPipeline.py -h
```

We need to provide the directory containing the fastq files, the directory where we want the output to go (it will be made if it doesn't exist), our reference for bowtie (provided by the tutorial, see README on how to make one for your sample set), and the name of our control sample. To make sure everything is in working order we can run the pipeline in test mode by activating the -t option.

```
python ../bin/variantPipeline.py ../scripts/aligning_pipeline.groovy "./data/fastq/*fastq" ./data/aligned_output ./options.yaml -t
```

It seems like everything is in order so we'll let it rip. This took about 5 min on my old macbook pro. On the flux it won't take long at all.

```
python ../bin/variantPipeline.py ../scripts/aligning_pipeline.groovy "./data/fastq/*fastq" ./data/aligned_output ./options.yaml
```

## 3a) Calling variants using deepSNV

We can call variants using deepSNV in the following pipeline. This pipeline call variants, checks their average mapq,phred, and read position. It also identifies nonsynonymous and synonymous variants and filters putative variants according to the provided thresholds.

In the tutorial I have set up the options to require deepSNV to identify the variants and to call NS/S relative to the plasmid control since the tutorial tests a single point mutatant made from the plasmid control. These might not be the settings you require. In practice we infered variants when the plasmid control differed from the sample at the consensus level, called NS/S relative to the sample consensus, and only required minority variants (frequency<0.5) to be identified by deepSNV and meet the filtering thresholds.

You will have to make sure the muscle path in the tutorial is correct for your machine.

```
python ../bin/variantPipeline.py ../scripts/deepsnv_pipeline.groovy "./data/aligned_output/removed_duplicates/*.bam" ./data/deepSNV_pipeline/ ./options.yaml
```

_If you expect a high level of pcr errors then use a two sided distribution. Set the disp option to two.sided_

## 3b) Calling all variants with python pipeline

This pipeline tallies all bases at all positions. It outputs a JSON file, without filtering and calls NS/S relative to a the positions in a JSON input file. **The positions given by this pipeline are in python-speak and are base 0. They will be 1 position behind those given by the deepSNV pipeline which is base 1.**

```
python ../bin/variantPipeline.py ../scripts/python_pipeline.groovy "./data/aligned_output/removed_duplicates/*.bam" ./data/all_variants ./options.yaml
```

<a name="analysis"/>

## 4) Secondary Analysis

The pipeline provides all bases above the stringent cut off for each position. In almost all cases these will match the reference base in the plasmid control. Variants below the stringency cut off are filtered by the criteria in the options file.

<a name="working-with-real-data"/>

## 5) Working with real data

So you just got some Illumina data back! Now to analyze it. Using either cyberduck, or better still, [globus](http://arc.umich.edu/flux-and-other-hpc-resources/flux/using-flux/transferring-files-with-globus-gridftp/) transfer your run data to the appropriate directory on NAS (which is backed up regularly by the University and also backed up to a lab external hard drive). DO NOT delete your data from the portable hard drive unless you check with Adam first. NEVER edit these primary sequence files. The path to our NAS is "/nfs/med-alauring" and there are directories for raw data that are organized by year. (See the flux directory sctructure below). It is a good idea to rename your directory prior to transfer so that it does not have spaces. Stay tuned for a uniform nomenclature for our lab.

### Flux directory structure

![Dir structure](https://github.com/jtmccr1/variant_pipeline/blob/master/doc/Flux.jpeg)

Once your data is in NAS, be a good neighbor and make the data accessible to everyone in the lab. The first command makes alauring-lab the group for the files. We have to do this because the default for some people in the lab is internalmed and for others is micro. This makes the group something everyone belongs to. The next command gives those in the group read, write, and execute permission.

```
chgrp -R alauring-lab path/to/your_data
chmod -R g=rwx
```

Now that the data in up on NAS. Let's get a directory set up on /scratch/ where we will do our actual work.

```
cd /scratch/alauring_fluxm/
ls
```

Look there is folder just for you! cd into it and we can begin.

### 4.1 Setup

Let's setup an experimental directory. This will hold all of the files and data that you use for a given experiment or flux run. From your scratch directory run, where "exp_label" is the name you choose for this experiment. Make it something that provides information about the experiment and/or a date.

```
mkdir exp_label
cd exp_label
mkdir data
mkdir data/fastq
mkdir data/reference
mkdir scripts
```

You can now navigate through the exp_label directory and sub-directories to see that there is a directory called "data" that contains sub-directories for fastq files and reference files. There is also a sub-directory called "scripts" that you will rarely access.

_Note you may have to make a reference file for bowtie2 to align to. I like to keep mine in data/reference. You can use the command in the readme file to make your reference so long as you already have a fasta file._

### 4.2 Running

Now we'll rename and copy our fastq's from the NAS to our data directory. We just have to tell the computer where to find our scripts. These commands should look familar, and can be run from your experiment folder on scratch.

```
python ~/variant_pipeline/scripts/change_names_miseq.py -s path/to/data/on/NAS -f data/fastq/
```

The only differences between this and what we did above are the paths to the scripts and the data. The path to your data on NAS should be something like "/nfs/med-alauring/raw_data/2015/filename". Because the pipeline is in your home directory you can easily access it with the shortcut "~/"

If this looks good let's run

```
python ~/variant_pipeline/scripts/change_names_miseq.py -s path/to/data/on/NAS -f data/fastq/ -run
```

_Note if you data on NAS ends in .gz then it is gzipped. This script is able to copy and unzip zipped files automatically._

Now we can copy the pbs script from the tutorial and modify it to suit our purposes.

```
cp ~/variant_pipeline/bin/variant_pipeline.pbs ./experiment_name.pbs
```

You can use the command "nano experiment_name.pbs" to open the text editor and edit the pbs script. Make sure you edit the path to the variantPipeline.py script by directing it to your home directory (~/). The last line should read

```
 python ~/variant_pipeline/bin/variantPipeline.py ./scripts/options.yaml
```

We will also need to make an options file. To start you can copy the turtorial options file into your scripts directory and edit it as above.

Then just submit using qsub as before and sit back while the computer does the rest. :smiley:

python ../bin/variantPipeline.py ../scripts/basic_pipeline.groovy "./data/fastq/\*.fastq" results/basicnew_options.yaml

python ../bin/variantPipeline.py ../scripts/python_pipeline.groovy "./results/basic/removed_duplicates/\*.bam" results/variant_calls new_options.yaml

## Appendix

### Using a pbs script to run the pipeline

**If you are running on the flux** Then instead of running the above command from the command line we would usually run this command in a pbs script. This is because running memory intensive commands on the login node slows everyone down. A pbs script tells flux to set aside a separate node just for our work. An example of a pbs script can be found in bin/variant*pipeline.pbs. For larger sample sets you'll need to adjust the memory and walltime limits\*\*\_can you provide suggested times and memory for a hiseq run or a miseq run?*\*\*. A detailed description of pbs scripts can be found [here](http://arc-ts.umich.edu/software/torque/).
The script can be edited using a text editor, like nano.

Let's run the same pipeline using a pbs script.

The first lines of a pbs script begin with "#PBS" and give the scheduler information regarding our job.
Let's make some modifications using nano.

```
nano ../bin/variant_pipeline.pbs
```

_Note you can't use the mouse to navigate in nano, but you can use the arrow keys. You can save by pressing cntrl+x_

The line

> #PBS -N test_PR8

signifies the name of the job. Let's change "test_PR8" to "tutorial"

> #PBS -M my_email@umich.edu

Tells the computer to send you an email at the start and end of the job let's change it so I don't get all your emails.

> #PBS -l nodes=1:ppn=2,mem=24gb,walltime=2:00:00

signifies how many nodes, processors per node, memory, and max time we want the job to run. For this small job lets use 10gb of memory and limit the wall time to 10 min 00:10:00.

We then can submit the job using

```bash
qsub ../bin/variant_pipeline.pbs
```

and check the status of it using

```bash
qstat -u yourusername
```

_You may find yourself in the unfortunate position of seeing a failed pipeline once in a while. If a certain stage fails, I have found it helpful to delete the your_output_dir/.bpipe directory, which is a hidden directory, and resubmitting the pipeline. Bpipe will rerun the pipeline from the begining, but it will skip steps whose output already exists._

A log of the job output can be found at tutorial.o########## where tutorial is the name of the job and ####### is the job Id. We can page through the output using

```
more tutorial.o*
```

and spacebar to page down.

At the bottom we should find

> --------------------- Pipeline Success -------------------------

The output data from a successful run can be found in your_output_dir/mapq.all.sum.csv.
This contains the called variants and the data needed to filter them to your hearts desire.

Additionally Bpipe keeps a log of all the commands it runs in 'commandlog.txt'. This can be useful for debugging.
