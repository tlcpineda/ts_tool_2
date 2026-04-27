import csv
import os
import tkinter as tk
from tkinter import filedialog as fd


def welcome_sequence(items: list):
    max_chars = len(max(items, key=len))
    line_len = max(max_chars + 10 * 2, 60)
    items = [""] + items + [""]

    hor_bar(line_len)

    for item in items:
        print(f"{item:^{line_len}}")

    hor_bar(line_len)


def hor_bar(num_chars: int, text: str = "") -> None:
    display_x = num_chars * "░"

    if text:  # Redefine display is text is defined
        text_len = len(text)
        padded_len = (0 if text is None else 2) * 2 + text_len
        display_x = (
            display_x[:5] + f"{text:^{padded_len}}" + display_x[5 + padded_len :]
        )

    print(display_x)


def identify_path(base_type: str, initdir: str = "") -> str | tuple[str, ...]:
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)

    path = ""
    paths = ()

    match base_type:
        case "file":
            paths = fd.askopenfilenames(
                title="Select DOCX Files",
                filetypes=(("DOCX files", "*.docx"), ("All files", "*.*")),
                initialdir=initdir,
            )
        case "csv":
            path = fd.askopenfilename(
                title="Select CSV File",
                filetypes=(("CSV files", "*.csv"), ("All files", "*.*")),
                initialdir=initdir,
            )
        case "folder":
            path = fd.askdirectory(title="Select Folder", initialdir=initdir)

    root.destroy()
    return paths if base_type == "file" else path


def ensure_path_exists(dirpath: str, base_type: str = "file") -> bool:
    try:
        path_to_check = os.path.dirname(dirpath) if base_type == "file" else dirpath

        if not path_to_check or path_to_check in [".", ""]:
            return True

        if not os.path.exists(path_to_check):
            os.makedirs(path_to_check)

            display_message("INFO", "Path created.")
            display_path_desc(path_to_check, "folder")
            return True

        if not os.path.isdir(path_to_check):
            display_message("ERROR", "Invalid path.")
            display_path_desc(path_to_check, "folder")
            return False

        display_message("INFO", "Path already exists.")
        display_path_desc(path_to_check, "folder")
        return True

    except Exception as err:
        display_message("ERROR", "Path could not be created", f"{err}")
        return False


def display_path_desc(path: str, base_type: str) -> tuple[str, str]:
    parent_name, base_name = os.path.split(path)
    split_parent_name = parent_name.split("/" if "/" in parent_name else os.sep)
    num_levels = 3
    process_dirname = (
        parent_name
        if len(split_parent_name) <= num_levels
        else f".../{'/'.join(split_parent_name[-3:])}"
    )

    print(
        f"\n<=> {base_type.title()} Details :"
        f"\n<=>  Directory : {process_dirname}"
        f"\n<=>  Base Name : {base_name}"
    )

    return parent_name, base_name


def continue_sequence() -> bool:
    proper_resp = False
    resp = "C"

    while not proper_resp:
        print(
            "\n>>> Select an option :"
            "\n>>>  [C]ontinue with another chapter ?"
            "\n>>>  E[X]it and close this window ?"
        )

        resp = input(">>> ").upper()

        proper_resp = True if resp in ["C", "X"] else False

    if resp == "X":
        print("\n<=> Closing down ...")

        return True
    else:
        print("\n<=> Restarting ...\n")

        return False


def display_message(tag: str, message: str, exception: str = "") -> None:
    print(f"\n<=> [{tag}] {message}")

    if exception:
        print(f"<=>  {exception}")


def clean_number(num: str) -> tuple[str, bool]:
    """
    Strip leading/trailing zeroes from chapter numbers.
    Main chapters (including extra chapters) are numbered with integers.
    """
    ch_num = 0
    is_main_ch = False

    try:
        num_caps = num.upper()

        if num_caps.startswith("EX"):  # Handle extra chapters; ie "EX01", "EX02".
            ch_num = num_caps
            is_main_ch = True

        else:  # Handle numeric chapters ("0068", "0068.5", etc)
            n = float(num)

            if n.is_integer():
                ch_num = int(n)
                # Handle chapter numbers less than 10; to display as "0#".
                ch_num = f"{ch_num:02}" if len(str(ch_num)) < 2 else ch_num
                is_main_ch = True
            else:
                ch_num = n
                # Handle chapter numbers less than 10; to display as "0#.#".
                ch_num = f"{ch_num:04}" if len(str(ch_num)) < 4 else ch_num
                is_main_ch = False

    except ValueError as v:
        display_message(
            "ERROR",
            f"Invalid chapter format, {num}.  Check folder name.",
            f"{v}",
        )

    except Exception as e:
        display_message("ERROR", "Failed to extract chapter number.", f"{e}")

    return str(ch_num), is_main_ch


def load_csv(inpath: str = "") -> tuple[list[list[str]], str]:
    data = []

    if not inpath:
        print(">>> Select preliminary CSV file ...")

        path = str(identify_path("csv"))

        if not path:
            print("\n<=> No file selected.")
            return data, ""

        inpath = path

    display_path_desc(os.path.normpath(inpath), "file")

    with open(inpath, "r", newline="", encoding="utf-8-sig") as csvfile:
        data = list(csv.reader(csvfile))

        return data, os.path.normpath(inpath)


def rename_path(path_src: str, path_dst: str, pathtype: str) -> None:
    base_src = os.path.basename(path_src)
    base_dst = os.path.basename(path_dst)
    try:
        os.rename(path_src, path_dst)

        display_message(
            "SUCCESS",
            f"{pathtype.title()} renamed.\n<=>  From : {base_src}\n<=>  To   : {base_dst}",
        )

    except Exception as e:
        display_message("ERROR", f"Failed to rename {pathtype}.", f"{e}")


def write_to_csv(csv_path: str, data: list) -> None:
    """
    Save data to the specified path.
    :param csv_path: The path pointing to the CSV file.
    :param data: A 2D list, with header row/s.
    :return: None
    """
    try:
        with open(csv_path, "w", newline="", encoding="utf-8") as file:
            csv.writer(file).writerows(data)

        display_message("SUCCESS", f"{len(data) - 1} data rows written to file.")

        display_path_desc(csv_path, "file")

    except Exception as e:
        display_message("ERROR", "Writing to CSV file failed.", f"{e}")


def expand_path(path_short: str) -> str:
    return os.path.normpath(os.path.expanduser(path_short))


def copy_file(source_path: str, dest_path: str, filename: str, extname: str) -> None:
    # Creates a copy of the file (Manual Binary Copy) to revision folder.
    file_path_0 = parse_pathname(source_path, filename, extname, "file")
    file_path_1 = parse_pathname(dest_path, filename, extname, "file")

    try:
        with open(file_path_0, "rb") as f_src:
            with open(file_path_1, "wb") as f_dst:
                # Copying in 1MB chunks to be safe with large files
                while True:
                    chunk = f_src.read(1024 * 1024)
                    if not chunk:
                        break
                    f_dst.write(chunk)

        display_message("SUCCESS", f"File copied to '{os.path.basename(dest_path)}'.")
        display_path_desc(file_path_1, "file")

    except Exception as e:
        display_message("ERROR", "Failed to copy file.", f"{e}")


def parse_pathname(parent_dir: str, basename: str, extname: str, pathtype: str) -> str:
    if pathtype == "file":
        dest_path = os.path.join(parent_dir, f"{basename}.{extname}")
    else:  # folder
        dest_path = os.path.join(parent_dir, f"{basename}/{extname}")

    return os.path.normpath(dest_path)
