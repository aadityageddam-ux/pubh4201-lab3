"""Download the two raw datasets provided for PUBH 4201 Lab 3."""

from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
BASE_URL = (
    "https://raw.githubusercontent.com/gwcbi/applied-computing-HDS/"
    "refs/heads/main/data/raw/lab3-messy-data"
)

DATASETS = {
    "messy_samples.csv": b"sample_id,patient_name,dob,sex",
    "messy_sequences.fasta": b">sample_001",
}


def download_dataset(filename: str, expected_start: bytes) -> None:
    """Download one dataset and make sure it looks like the expected file."""
    url = f"{BASE_URL}/{filename}"
    request = Request(url, headers={"User-Agent": "PUBH4201-Lab3"})

    with urlopen(request, timeout=30) as response:
        contents = response.read()

    # This catches an empty response or an error page saved in place of the data.
    if not contents.startswith(expected_start):
        raise ValueError(f"Downloaded content for {filename} was not recognized.")

    output_path = RAW_DATA_DIR / filename
    output_path.write_bytes(contents)
    print(f"Downloaded {filename} to {output_path.relative_to(PROJECT_ROOT)}")


def main() -> None:
    """Download both files to the local raw-data folder."""
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

    try:
        for filename, expected_start in DATASETS.items():
            download_dataset(filename, expected_start)
    except (HTTPError, URLError, TimeoutError, ValueError) as error:
        raise SystemExit(f"Download failed: {error}") from error


if __name__ == "__main__":
    main()
