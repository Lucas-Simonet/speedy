from llama_cpp import Llama
import os


def main():
    print("current directory")
    print(os.getcwd())
    os.chdir("/Users/lucassimonet/Dev/speedy/speedy")
    print(os.getcwd())

    # print("Downloading GGUH files")
    # hf_hub_download(repo_id="microsoft/Phi-3-mini-4k-instruct-gguf", filename="Phi-3-mini-4k-instruct-q4.gguf", cache_dir="./speedy")

    llm = Llama(
        model_path="Phi-3-mini-4k-instruct-q4.gguf",  # path to GGUF file
        n_ctx=4096,  # The max sequence length to use - note that longer sequence lengths require much more resources
        n_threads=8,  # The number of CPU threads to use, tailor to your system and the resulting performance
    )

    prompt = "What is a mixin in python ?"

    output = llm(
        f"<|user|>\n{prompt}<|end|>\n<|assistant|>",
        max_tokens=500,  # Generate up to 256 tokens
        stop=["<|end|>"],
        echo=True,  # Whether to echo the prompt
        stream=True,
    )

    for item in output:
        print(item["choices"][0]["text"], end="")


if __name__ == "__main__":
    main()
