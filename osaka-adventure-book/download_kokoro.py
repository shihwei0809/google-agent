import urllib.request
import tarfile
import os

url = "https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/kokoro-multi-lang-v1_1.tar.bz2"
filename = "kokoro-multi-lang-v1_1.tar.bz2"

print(f"Downloading {url} ...")
def report(block_num, block_size, total_size):
    read_so_far = block_num * block_size
    if total_size > 0:
        percent = read_so_far * 1e2 / total_size
        print(f"\rDownloaded {percent:.1f}%", end="", flush=True)
    else:
        print(f"\rDownloaded {read_so_far} bytes", end="", flush=True)

try:
    urllib.request.urlretrieve(url, filename, reporthook=report)
    print("\nDownload complete. Extracting file...")
    
    with tarfile.open(filename, "r:bz2") as tar:
        tar.extractall()
        
    print("Extraction complete. Deleting archive...")
    os.remove(filename)
    print("Done!")
except Exception as e:
    print(f"\nError: {e}")
