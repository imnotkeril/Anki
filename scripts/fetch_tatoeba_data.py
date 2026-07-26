import urllib.request
from pathlib import Path

FILES = {
    "sentences.tar.bz2": "https://downloads.tatoeba.org/exports/sentences.tar.bz2",
    "links.tar.bz2": "https://downloads.tatoeba.org/exports/links.tar.bz2",
    "jpn_indices.tar.bz2": "https://downloads.tatoeba.org/exports/jpn_indices.tar.bz2",
}
DATA_DIR = Path(__file__).parent.parent / "data"


def main() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    for filename, url in FILES.items():
        out_path = DATA_DIR / filename
        print(f"downloading {url} -> {out_path}")
        urllib.request.urlretrieve(url, out_path)
    print("done")


if __name__ == "__main__":
    main()
