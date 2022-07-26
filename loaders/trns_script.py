# Copyright 2020 The HuggingFace Datasets Authors and the current dataset script contributor.
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
"""Reference Genome dataset generator"""


import csv
import json
import gzip
import os
import tempfile
from multiprocessing import Pool, cpu_count
import subprocess
import shutil
import six
import ngsim
from Bio import bgzf, SeqIO

import datasets

logger = datasets.logging.get_logger(__name__)


_TRNS_CITATION = """\
@InProceedings{huggingface:dataset,
title = {A great new dataset},
author={huggingface, Inc.
},
year={2020}
}
"""

_TRNS_DESCRIPTION = """\
        This Gene annotaded Genome Reference ngs dataset is designed to create a NLP like model.
"""

_HOMEPAGE = "https://www.ncbi.nlm.nih.gov/grc"

_LICENSE = "MIT License"

_URLS = {
        "transcript": "https://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_human/release_41/gencode.v41.transcripts.fa.gz",
        "whole_genome": "https://hgdownload.soe.ucsc.edu/goldenPath/hg38/bigZips/hg38.fa.gz",
}

_FILES = {
    "transcript": "gencode.v41.transcripts.fa.gz", 
    "whole_genome": "hg38.fa.gz"
}

_TEMPFILES = []

def _tmp(prefix='gpt_gene.', suffix='.tmp'):
    """
    Makes a tempfile and registers it in the BedTool.TEMPFILES class
    variable.  Adds a "gpt_gene." prefix and ".tmp" extension for easy
    deletion if you forget to call cleanup().
    """
    tmpfn = tempfile.NamedTemporaryFile(
        prefix=prefix,
        suffix=suffix,
        delete=False,
    )
    tmpfn = tmpfn.name
    _TEMPFILES.append(tmpfn)
    return tmpfn

class TrnsConfig(datasets.BuilderConfig):
    """BuilderConfig for Trns."""

    def __init__(
        self,
        **kwargs,
    ):
        """BuilderConfig for Trns.
        Args:
          x_fold: `int`, the fold of read coverage to be simulated
          num_read: `int`, number of reads/read pairs to be generated per sequence/amplicon (not be used together with x_fold)
            to the label
          data_dir: `string`, the path to the folder containing the fasta files
          **kwargs: keyword arguments forwarded to super.
        """
        super(TrnsConfig, self).__init__(**kwargs)

class TrnsDataset(datasets.GeneratorBasedBuilder):
    """TODO: Short description of my dataset."""

    VERSION = datasets.Version("0.1.0")

    # This is an example of a dataset with multiple configurations.
    # If you don't want/need to define several sub-sets in your dataset,
    # just remove the BUILDER_CONFIG_CLASS and the BUILDER_CONFIGS attributes.

    # If you need to make complex sub-parts in the datasets with configurable options
    # You can create your own builder configuration class to store attribute, inheriting from datasets.BuilderConfig
    # BUILDER_CONFIG_CLASS = MyBuilderConfig

    # You will be able to load one or the other configurations in the following list with
    # data = datasets.load_dataset('my_dataset', 'first_domain')
    # data = datasets.load_dataset('my_dataset', 'second_domain')
    BUILDER_CONFIGS = [
        TrnsConfig(name="transcript", 
            version=VERSION, 
            description="Gencode transcript",),
    ]

    def _preprocessing(self, dl_manager):
        # TODO: This method is tasked with downloading/extracting the data and defining the splits depending on the configuration
        # If several configurations are possible (listed in BUILDER_CONFIGS), the configuration selected by the user is in self.config.name

        # dl_manager is a datasets.download.DownloadManager that can be used to download and extract URLS
        # It can accept any type or nested list/dict and will give back the same structure with the url replaced with path to local files.
        # By default the archives will be extracted and a path to a cached folder where they are extracted is returned instead of the archive

        data_dir = os.path.abspath(os.path.expanduser(dl_manager.manual_dir))
        ref_file = os.path.join(data_dir, _FILES[self.config.name])
        if not os.path.exists(ref_file):
            raise FileNotFoundError(
                "{ref_files} does not exist. Make sure you insert a manual dir that includes the file name {f}. Manual download instructions: {self.manual_download_instructions})"
            )

        return ref_file

    def _info(self):
        if self.config.name == "transcript":  # This is the name of the configuration selected in BUILDER_CONFIGS above
            features = datasets.Features(
                {
                    "sequence": datasets.Value("string"),
                    "trns_name": datasets.Value("string"),
                    # These are the features of your dataset like images, labels ...
                }
            )
        else:  # This is an example to show how to have different features for "first_domain" and "second_domain"
            features = datasets.Features(
                {
                    "sequence": datasets.Value("string"),
                    "id_name": datasets.Value("string"),
                    # These are the features of your dataset like images, labels ...
                }
            )
        return datasets.DatasetInfo(
            # This is the description that will appear on the datasets page.
            description=_TRNS_DESCRIPTION,
            # This defines the different columns of the dataset and their types
            features=features,  # Here we define them above because they are different between the two configurations
            # If there's a common (input, target) tuple from the features, uncomment supervised_keys line below and
            # specify them. They'll be used if as_supervised=True in builder.as_dataset.
            # supervised_keys=("sentence", "label"),
            # Homepage of the dataset for documentation
            homepage=_HOMEPAGE,
            # License for the dataset if available
            license=_LICENSE,
            # Citation for the dataset
            citation=_TRNS_CITATION,
        )

    def _split_generators(self, dl_manager):
        ref_file = self._preprocessing(dl_manager)

        return [
            datasets.SplitGenerator(
                name=datasets.Split.TRAIN,
                # These kwargs will be passed to _generate_examples
                gen_kwargs={
                    "reference": ref_file,
                    "split": "train"
                },
            ),
        ]

    # method parameters are unpacked from `gen_kwargs` as given in `_split_generators` "block_size": [int(bs) for bs in row.blockSizes.split(',')],
    def _generate_examples(self, reference, split):
        # TODO: This method handles input defined in _split_generators to yield (key, example) tuples from the dataset.
        # The `key` is for legacy reasons (tfds) and is not important in itself, but must be unique for each example.
        if self.config.name == "transcript":
            if reference.lower().endswith(('.bgz', '.gz')):
                with bgzf.open(reference, 'r') as fa:
                    for i, feature in enumerate(SeqIO.parse(fa, "fasta")):
                        yield i, {
                                "sequence": str(feature.seq),
                                "trns_name": str(feature.id),
                                }
            else:
                with open(reference, 'r') as fa:
                    for i, feature in enumerate(SeqIO.parse(fa, "fasta")):
                        yield i, {
                                "sequence": str(feature.seq),
                                "id_name": str(feature.id),
                                }
