import argparse
import glob
import os
from typing import List

import datasets
from tokenizers import normalizers, pre_tokenizers, BertWordPieceTokenizer, Regex
from transformers import PreTrainedTokenizerFast

DATASET_TYPES = {"ngs": "loaders/ngs_script.py", "wtr": "loaders/trns_script.py"}

def _kmer_split(k: int, sequence: str) -> List[str]:
    return " ".join([sequence[j: j + k] for j in range(len(sequence) - k + 1)])

def get_training_corpus(trans_data, batch_size, k):
    for i in range(0, len(trans_data["train"]), batch_size):
        yield [_kmer_split(k, seq) for seq in trans_data["train"][i : i + batch_size]["sequence"]]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--out",
        default="./",
        type=str,
        help="Path to the output directory, where the files will be saved",
    )
    parser.add_argument(
        "--name", default="bert-wordpiece", type=str, help="The name of the output vocab files"
    )
    parser.add_argument(
        "--dataset", default="wtr", type=str, help="The name of the input dataset"
    )
    parser.add_argument(
        "--dataset_config_name", default="transcript", type=str, help="The name of the input dataset"
    )
    parser.add_argument(
        "--dataset_dir", default="run/data", type=str, help="The name of the input dataset"
    )
    parser.add_argument(
        "--vocab_size", default=10000, type=int, help="vocab size"
    )
    parser.add_argument(
        "--batch_size", default=1024, type=int
    )
    parser.add_argument(
        "--k", default=17, type=int
    )
    parser.add_argument('--fast', action='store_true')
    args = parser.parse_args()
    
    # Initialize an empty tokenizer
    tokenizer = BertWordPieceTokenizer(
        clean_text=True,
        handle_chinese_chars=False,
        strip_accents=False,
        lowercase=True,
    )
    
    tokenizer.normalizer = normalizers.Sequence(
            [normalizers.Nmt(), normalizers.Lowercase(), normalizers.Replace(Regex("[^actg\s]"), "")]
            )

    tokenizer.pre_tokenizer = pre_tokenizers.Whitespace()

    trans_data = datasets.load_dataset(DATASET_TYPES[args.dataset], args.dataset_config_name, data_dir=args.dataset_dir)
    trans_data = trans_data.shuffle(seed=42)

    # And then train
    tokenizer.train_from_iterator(
        get_training_corpus(trans_data, args.batch_size, args.k),
        vocab_size=args.vocab_size,
        min_frequency=2,
        show_progress=True,
        special_tokens=["[PAD]", "[UNK]", "[CLS]", "[SEP]", "[MASK]"],
        limit_alphabet=3000,
        wordpieces_prefix="##",
    )
    
    # Save the files
    if args.fast:
        fast_tokenizer =  PreTrainedTokenizerFast(
                tokenizer_object=tokenizer,
                bos_token='[CLS]', eos_token='[SEP]', 
                unk_token='[UNK]', sep_token='[SEP]', 
                cls_token='[CLS]', pad_token='[PAD]', mask_token='[MASK]',
                truncation_side='right')
        fast_tokenizer.save_pretrained(os.path.join(args.out, args.name))
    else:
        tokenizer.save_model(args.out, args.name)

if __name__ == "__main__":
    main()
