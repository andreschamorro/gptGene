# importing module
import sys
# appending a path
sys.path.extend(['.', '..'])
import datasets
from model.Tokenizer import KmerBPETokenizer

def get_training_corpus():
    for i in range(0, len(trans_data["train"]), batch_size):
        yield trans_data["train"][i : i + batch_size]["feature"]

def main(k=17, vocab_size=10000, batch_size=1024):

    trans_data = datasets.load_dataset('loaders/dataset_script.py', data_dir='run/data')
    trans_data = trans_data.shuffle(seed=42)
    
    tokenizer = KmerBPETokenizer(k=k)
    
    tokenizer.train_from_iterator(
            get_training_corpus(),
            vocab_size=vocab_size,
            show_progress=True,
            min_frequency=2,
            special_tokens=["<s>", "<pad>", "</s>", "<unk>", "<mask>",])
    
    tokenizer.save_model("../run/transcripts_bpe_tokenizer", "k17")

if __name__ == "__main__":
    main()