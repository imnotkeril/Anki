import urllib.request
from pathlib import Path

URL = "https://raw.githubusercontent.com/mifunetoshiro/kanjium/master/data/source_files/raw/accents.txt"
OUT = Path(__file__).parent.parent / "data" / "kanjium_accents.txt"


def main() -> None:
    OUT.parent.mkdir(exist_ok=True)
    urllib.request.urlretrieve(URL, OUT)
    print(f"wrote {OUT} ({OUT.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
