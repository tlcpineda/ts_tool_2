import csv
import os

from docx import Document

from lib import (
    continue_sequence,
    display_message,
    display_path_desc,
    identify_path,
    welcome_sequence,
)

# Module variables
mod_name = "DOCX Translations to CSV"
mod_ver = "1"
date = "09 Apr 2026"
email = "tlcpineda.projects@gmail.com"
csv_name = "translations.csv"  # The filename of the output CSV file
textbox_dim_dst = [0.015, 0.01]  # width x height normalised.


def get_table_from_docx() -> tuple:
    print(">>> Select translation file/s (*.docx) to scrape ...")

    # Load file/s; at least one DOCX file may contain the translations.
    paths = identify_path("file")

    if not paths:
        print("\n<=> No file selected.")
        return [], None

    len_paths = len(paths)

    display_message(
        "INFO",
        f"Number of file{'s' if len_paths > 1 else ''} selected : {len(paths)}",
    )

    is_first_table = True
    parent_folder = ""
    row_data = []

    for path in paths:
        input_path = os.path.normpath(path)  # Normalise path.
        dirname, filename = display_path_desc(input_path, "file")

        try:
            doc = Document(input_path)
            row_start = 0
            add_heads = ["", "page_num", "panel", "x0", "y0", "w_box", "h_box", "text"]
            add_cols = [
                "",
                "col1",
                "col1/2",
                "calc",
                "calc",
                textbox_dim_dst[0],
                textbox_dim_dst[1],
                "text",
            ]

            if is_first_table:
                parent_folder = dirname
            else:
                row_start = 1

            for table in doc.tables:
                for row_num, row in enumerate(table.rows[row_start:]):
                    # for row in table.rows[row_start:]:
                    # Extract text from each cell in the row, and append to list.
                    row_data.append(
                        [
                            cell.text.replace("\n", " ").replace("\r", " ").strip()
                            for cell in row.cells
                        ]
                        + (add_heads if row_num == 0 and is_first_table else add_cols)
                    )

                is_first_table = False

        except Exception as e:
            display_message("ERROR", f"Cannot process '{filename}'.", f"{e}")

    # Extract, and return the tables found in the file.
    return row_data, parent_folder


def create_pre_csv() -> None:
    """
    Create a CSV file with table/s of translation notes from DOCX file/s.
    CSV file subject to manual processing for pagination and panel number designation.
    mod_01B.py shall handle x0, y0 calculations based on page/panel number.
    """

    row_data, parent_folder = get_table_from_docx()

    # Early return if no table is found in file.
    if not row_data or parent_folder is None:
        return

    try:
        csv_path = os.path.normpath(os.path.join(parent_folder, csv_name))

        # Open (or create) the CSV file for writing.
        with open(csv_path, "w", newline="", encoding="utf-8-sig") as csvfile:
            csv.writer(csvfile).writerows(row_data)

        display_message(
            "SUCCESS",
            f"Translations written to {csv_name}. Proceed to manual cleaning.",
        )
        display_path_desc(csv_path, "file")

    except Exception as e:
        display_message("ERROR", f"Error writing to CSV file {csv_name}.", f"{e}")


if __name__ == "__main__":
    welcome_sequence([mod_name, f"ver {mod_ver} {date}", email])

    print(input("\n>>> Press enter to continue ..."))

    confirm_exit = False

    while not confirm_exit:
        create_pre_csv()
        confirm_exit = continue_sequence()
