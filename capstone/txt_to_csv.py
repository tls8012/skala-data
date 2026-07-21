import csv
from pathlib import Path


ADULT_DATA_PATH = Path("adult_data.txt")
ADULT_CSV_PATH = Path("adult_data.csv")


def convert_adult_data_to_csv(
    input_path: Path = ADULT_DATA_PATH, output_path: Path = ADULT_CSV_PATH
) -> None:
    """Convert the comma-space-delimited adult data text file to CSV."""
    with input_path.open(encoding="utf-8", newline="") as source, output_path.open(
        "w", encoding="utf-8", newline=""
    ) as destination:
        # The first row is the header; remaining rows use ', ' as the delimiter.
        reader = csv.reader(source, skipinitialspace=True)
        csv.writer(destination).writerows(reader)

    print(f"Converted {input_path} to {output_path}")


convert_adult_data_to_csv()
