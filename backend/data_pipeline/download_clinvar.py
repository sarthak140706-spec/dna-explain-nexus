from pathlib import Path
import requests


CLINVAR_URL = (
    "https://ftp.ncbi.nlm.nih.gov/pub/clinvar/"
    "tab_delimited/variant_summary.txt.gz"
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]

RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"

OUTPUT_FILE = RAW_DATA_DIR / "variant_summary.txt.gz"


def download_file(url: str, output_path: Path) -> None:
    """
    Download a file in chunks so large genomic datasets
    do not need to be loaded fully into memory.
    """

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    if output_path.exists():
        print("ClinVar dataset already exists.")
        print(f"File: {output_path}")
        print(f"Size: {output_path.stat().st_size / (1024 ** 2):.2f} MB")
        return

    print("Downloading ClinVar variant summary...")
    print(f"Source: {url}")
    print(f"Destination: {output_path}")

    with requests.get(
        url,
        stream=True,
        timeout=120,
    ) as response:

        response.raise_for_status()

        total_size = int(
            response.headers.get("content-length", 0)
        )

        downloaded = 0
        chunk_size = 1024 * 1024

        with open(output_path, "wb") as file:

            for chunk in response.iter_content(
                chunk_size=chunk_size
            ):

                if not chunk:
                    continue

                file.write(chunk)

                downloaded += len(chunk)

                if total_size > 0:
                    percent = (
                        downloaded
                        / total_size
                        * 100
                    )

                    print(
                        f"\rDownloaded: "
                        f"{downloaded / (1024 ** 2):.1f} MB "
                        f"({percent:.1f}%)",
                        end="",
                    )

    print("\nDownload completed.")

    print(
        f"Final size: "
        f"{output_path.stat().st_size / (1024 ** 2):.2f} MB"
    )


if __name__ == "__main__":

    try:

        download_file(
            CLINVAR_URL,
            OUTPUT_FILE,
        )

    except requests.RequestException as error:

        print("\nClinVar download failed.")
        print(error)

    except Exception as error:

        print("\nUnexpected error:")
        print(error)