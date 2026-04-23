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


def identify_path(base_type: str, initdir: str = "") -> str | tuple:
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)

    path = ""

    match base_type:
        case "file":
            path = fd.askopenfilenames(
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
    return path


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


def display_path_desc(filepath: str, base_type: str) -> tuple:
    parent_name, base_name = os.path.split(filepath)
    split_parent_name = parent_name.split(os.sep)
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
        if num.upper().startswith("EX"):  # Handle extra chapters; ie "EX01", "EX02".
            ch_num = num.upper()
            is_main_ch = True

        else:  # Handle numeric chapters ("0068", "0068.5", etc)
            n = float(num)

            if n.is_integer():
                ch_num = int(n)
                # Handle chapter numbers less than 10.
                ch_num = f"{ch_num:02}" if len(str(ch_num)) < 2 else ch_num
                is_main_ch = True
            else:
                ch_num = n
                # Handle chapter numbers less than 10.
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


def load_csv() -> tuple[list, str]:
    data = []

    print(">>> Select preliminary CSV file ...")

    path = str(identify_path("csv"))
    # path = identify_path("csv")

    if not path:
        print("\n<=> No file selected.")
        return data, ""

    display_path_desc(os.path.normpath(path), "file")

    with open(path, "r", newline="", encoding="utf-8-sig") as csvfile:
        data = list(csv.reader(csvfile))

        return data, os.path.normpath(path)


# def process_pathname(
#     case_num: int, base_path: str, target: str = "", data: list = []
# ) -> str:
#     psd_path = os.path.join(base_path, target)

#     if not psd_path:
#         return ""

#     display_path_desc(psd_path, "folder")

#     for item in os.listdir(psd_path):
#         filename, ext = os.path.splitext(item)

#         display_message("PROCESSING", f"{item} ...")

#         if ext.lower() == ".psd":  # Process only PSD files
#             path0 = os.path.join(psd_path, item)

#             if os.path.isfile(path0):
#                 match case_num:
#                     case 1:  # Initial case when appending page markers ("##X") to original file name.
#                         page_num = filename[-2:]

#                         if page_num.isdigit():
#                             new_filename = f"{filename} {page_num}X{ext}"
#                             path1 = os.path.join(psd_path, new_filename)

#                             if path0 == path1:
#                                 display_message(
#                                     "SKIP", "File with the same target name exists."
#                                 )
#                             else:
#                                 rename_path(path0, path1, "file")
#                         else:
#                             display_message("SKIP", "Not a valid file path.")

#                     case 2:  # Case when marking files for revision, with "X"
#                         if " " in filename:
#                             filename0, page = filename.split(" ")

#                             if page.isdigit() and page in data:
#                                 new_filename = f"{filename}X{ext}"
#                                 path1 = os.path.join(psd_path, new_filename)

#                                 if path0 == path1:
#                                     display_message("SKIP", "File already marked.")
#                                 else:
#                                     rename_path(path0, path1, "file")
#                             else:
#                                 display_message("SKIP", "No revisions required.")
#                         else:
#                             display_message("SKIP", "No page marker found.")

#                     case 3:  # Case when cleaning up files name, prior to submission, remove page markers ("##" or "##X")
#                         if " " in filename:
#                             filename0, page = filename.split(" ")

#                             new_filename = f"{filename0}{ext}"
#                             path1 = os.path.join(psd_path, new_filename)

#                             if path0 == path1:
#                                 display_message(
#                                     "SKIP", "File with the same name exists."
#                                 )
#                             else:
#                                 rename_path(path0, path1, "file")
#                         else:
#                             display_message("SKIP", "No page marker found.")

#             else:
#                 display_message("SKIP", "Not a valid file path.")
#         else:
#             display_message("SKIP", "Not a PSD file.")

#     return psd_path


def rename_path(path_src: str, path_dst, pathtype: str) -> None:
    base_src = os.path.basename(path_src)
    base_dst = os.path.basename(path_dst)
    try:
        os.rename(path_src, path_dst)

        display_message(
            "SUCCESS",
            f"F{pathtype[1:]} renamed.\n<=>  From : {base_src}\n<=>  To   : {base_dst}",
        )

    except Exception as e:
        display_message("ERROR", f"Failed to rename {pathtype}.", f"{e}")
