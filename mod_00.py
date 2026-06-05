import math
import os
import tkinter as tk

from dotenv import load_dotenv

from lib import (
    clean_number,
    copy_file,
    display_message,
    display_path_desc,
    ensure_path_exists,
    expand_path,
    get_term_details,
    hor_bar,
    identify_path,
    load_csv,
    load_proj_cache,
    parse_pathname,
    rename_path,
    show_table,
    welcome_sequence,
    write_to_csv,
)

# Module variables
mod_name = "Preliminary Administrative Works"
mod_ver = "3"
date = "10 May 2026"
email = "tlcpineda.projects@gmail.com"
csv_name_pre = "numbering_tbl"
csv_heads = [
    [  # Official Japanse headers
        "最終更新日",
        "巻数",
        "写植データ",
        "日本語版データ",
        "話数",
        "ページ数",
        "納品外",
        "GOTO差し替え",
    ],
    [  # Translations of official Japanese headers
        "Last Updated",
        "Volume Number",
        "Typesetting Data",
        "Japanese Version Data",
        "Episode Number",
        "Page Number",
        "Not Included",
        "GOTO Replacement",
    ],
]

cols = 8  # Currently eight (8) columns are set in pagination webpage.

lang_iso_2 = "en"  # Two-character language ISO code

# Load .env file.
load_dotenv()
SRC_WEBAPP = os.getenv("WEBAPP", "")
BOX_DEV_CONSOLE = os.getenv("BOX_DEV_CONSOLE", "")
PROJ_CACHE = expand_path(os.getenv("PROJ_CACHE", ""))
PARENT_LOCAL = expand_path(os.getenv("PARENT_LOCAL", ""))


def prepare_files() -> None:
    ref_jpg_ch_folders = []
    ref_psd_ch_folders = []
    w_psd_ch_folders = []

    try:
        display_message("INFO", "Preparing reference files ... ")

        pagination_data, proj_name, vol_num, title_vol = gen_pagination()
        # List of reference PSD files.
        psd_filenames = [f"{row[2]}.psd" for row in pagination_data if row[6] == "—"]
        # List of referene JPEG files.
        jpg_filenames = [f"{row[3]}.jpg" for row in pagination_data if row[6] == "—"]

        print("\n>>> Process folders containing reference files.")

        psd_files_dir, psd_num_missing = verify_contents_ref_folder(
            psd_filenames, "Typesetting files (PSD)"
        )
        jpeg_jp_dir, jpeg_num_missing = verify_contents_ref_folder(
            jpg_filenames, "Japanese JPEG files"
        )

        # Proceed with sorting process only if both sets of files are complete.
        if psd_num_missing or jpeg_num_missing:
            display_message("WARN", "Incomplete reference files.")
            nums_list = [("PSD", psd_num_missing), ("JPEG", jpeg_num_missing)]
            col_len = max(len(str(value)) for (_, value) in nums_list)
            for name, value in nums_list:
                print(
                    f"<=>   Number of missing {name:4} files : {'No folder selected.' if value == 'NA' else value:>{col_len}}"
                )

            display_message("INFO", "Terminating process.")
            return

        # Sorting files.
        # Parent of both chapter working files, and reference files.
        proj_parent = parse_pathname(PARENT_LOCAL, proj_name, "", "folder")

        # Parse parent directory local destination of reference files.
        # to be appended by chapter folders.
        ref_psd_parent = parse_pathname(
            proj_parent, f"{int(float(vol_num))}.1 PSD", "", "folder"
        )
        ref_jpg_parent = parse_pathname(
            proj_parent, f"{int(float(vol_num))}.2 JPEG", "", "folder"
        )

        for row in pagination_data[2:]:  # Two rows of headers: JP, and EN.
            _, _, psd_name, jpeg_jp_name, ch_num, page_num, exclude_page, gtn = row

            print("")
            hor_bar(100, f"Processing '{psd_name}.psd' / '{jpeg_jp_name}.jpg' ...")

            if exclude_page == "—":  # "—" > False; ie row describes a working file.
                # Save a copy of the pair of files to reference directories.
                ch_name, ch_4 = parse_ch_name(ch_num)
                psd_dest = parse_pathname(ref_psd_parent, ch_name, "", "folder")
                jpg_dest = parse_pathname(ref_jpg_parent, ch_name, "", "folder")

                if psd_dest not in ref_psd_ch_folders:
                    ensure_path_exists(psd_dest, "folder")
                    ref_psd_ch_folders.append(psd_dest)

                copy_file(psd_files_dir, psd_dest, psd_name, "psd")

                if jpg_dest not in ref_jpg_ch_folders:
                    ensure_path_exists(jpg_dest, "folder")
                    ref_jpg_ch_folders.append(jpg_dest)

                copy_file(jpeg_jp_dir, jpg_dest, jpeg_jp_name, "jpg")

                # Save a copy of the PSD file, then renamed, in the working folder.
                psd_dest_w = parse_pathname(
                    proj_parent,
                    f"Initialise Files/V{int(vol_num):02} - {ch_name}",
                    f"{lang_iso_2}_{title_vol}_{ch_4}",
                    "folder",
                )

                if psd_dest_w not in w_psd_ch_folders:
                    ensure_path_exists(psd_dest_w, "folder")
                    w_psd_ch_folders.append(psd_dest_w)

                # # Working PSD file renamed "en_[title_vol]_[ch_4]_[pg_num_3]
                # psd_name_w = f"{'GTNP ' if gtn == '○' else ''}{lang_iso_2}_{title_vol}_{ch_4}_{int(page_num):03}"

                # Working PSD file same file name as typesetting data file;
                # with ordinal numbering by chapter affixed.
                # allowing for "GO TO NEXT PAGE" prefix.
                psd_name_w = (
                    f"{'GTNP ' if gtn == '○' else ''}{psd_name} {int(page_num):03}"
                )

                copy_file(psd_files_dir, psd_dest_w, psd_name, "psd")
                rename_path(
                    parse_pathname(psd_dest_w, psd_name, "psd", "file"),
                    parse_pathname(psd_dest_w, psd_name_w, "psd", "file"),
                    "file",
                )

            else:
                display_message("INFO", "Skipping file.  Excluded from delivery list.")
            hor_bar(100)

        # Manually delete the base folders when opportune.
        display_message(
            "INFO", "Folders containing reference files may now be deleted."
        )
        display_path_desc(jpeg_jp_dir, "folder")
        display_path_desc(psd_files_dir, "folder")

        # Summarising contents of recently created folders.
        summary_table = []

        for index, folder in enumerate(
            ref_psd_ch_folders + ref_jpg_ch_folders + w_psd_ch_folders
        ):
            summary_table.append(
                [
                    index + 1,
                    f".../{'/'.join((folder.split('/' if '/' in folder else os.sep))[-2:])}",
                    f"{len(os.listdir(folder)):6}",
                    "※"
                    if index > len(ref_psd_ch_folders + ref_jpg_ch_folders) - 1
                    else "",
                ]
            )

        show_table(
            f"New Folders in .../2 PROJECTS/{proj_name}",
            [4, 50, 10, 1],
            ["Item", "Directory", "Contents", ""],
            summary_table,
        )

        print("※ Files require adjustments in resolution and dimensions.")

    except Exception as e:
        display_message(
            "ERROR", "Failed to sort reference files to working directories.", f"{e}"
        )


def parse_ch_name(chapter_num: str) -> tuple[str, str]:
    ch, is_main = clean_number(chapter_num)
    ch_formatted = f"{'CH' if not ch.startswith('EX') else ''}{ch if is_main else ch.split('.')[0]}"

    ch_float = 1000 if ch.startswith("EX") else float(ch)
    ch_log = math.log(ch_float * (10 if ch_float < 10 else 1), 10)
    lead_0 = (
        "" if ch.startswith("EX") or ch_log > 3 else "0" * (4 - math.floor(ch_log + 1))
    )

    four_char_ch = f"{lead_0}{ch}"

    return ch_formatted, four_char_ch


def verify_contents_ref_folder(
    fnames: list[str], files_desc: str
) -> tuple[str, int | str]:
    print(f"\n>>> {files_desc} : ")

    ref_folder = str(identify_path("folder"))

    if not ref_folder:
        print("\n>>> No folder selected.")
        return "", "NA"

    _, base = display_path_desc(ref_folder, "folder")
    display_message("INFO", f"Verifying contents of folder '{base}' ...")

    ref_contents = os.listdir(ref_folder)
    missing_files = [name for name in fnames if name not in ref_contents]
    num_missing_files = 0

    if missing_files:
        num_missing_files = len(missing_files)
        display_message("WARN", f"Missing files ({num_missing_files}) from '{base}' :")
        print(f"<=>  {'\n<=>  '.join(missing_files)}\n")
    else:
        display_message("INFO", f"All required files in '{base}'.")

    return ref_folder, num_missing_files


def gen_pagination() -> tuple[list[list[str]], str, str, str]:
    """
    :return: csv_data, proj_name, vol_num, title_vol
    """
    try:
        cache = load_proj_cache(PROJ_CACHE)
        work_id, proj_name, title_en, vol_num, _, _ = get_term_details(cache)
        title_vol = f"{title_en}_{int(vol_num):03}"

        print(f"\n<=> Generating pagination data for ' {title_vol} ' ... ")

        csv_data = []

        # Check if CSV file exists from previous run.
        csv_path = os.path.join(
            PARENT_LOCAL, proj_name, f"{csv_name_pre} {title_vol}.csv"
        )

        if os.path.exists(csv_path):
            display_message("INFO", "Pagination data loaded from CSV file ... ")
            csv_data, _ = load_csv(csv_path)

        else:
            # Tkinter method to process pagination data, pasted from webapp.
            csv_data = get_webapp_data(work_id, vol_num, title_vol)
            write_to_csv(csv_path, csv_heads + csv_data)

        return csv_data, proj_name, vol_num, title_vol

    except Exception as e:
        display_message("ERROR", "Failed to generate pagination data.", f"{e}")

        return [], "", "", ""


def get_webapp_data(id: str, vol: str, title_vol: str) -> list[list[str,]]:
    print(f"\n<=> Copy data, filtered for volume (巻数) {vol}, on : ")
    print(f"\n    {SRC_WEBAPP}/{id}?tab=list")

    # Short pause to copy data.
    print(input("\n>>> Press enter to continue ..."))

    try:
        # Define tkinter widget to receive data; where copied data shall be pasted to.
        root = tk.Tk()
        root.title(title_vol)
        root.items = []

        root.lift()
        root.focus_force()

        button_frame = tk.Frame(root)
        button_frame.pack(pady=10)

        instructions = tk.Label(root, text="Paste pagination data below :", anchor="sw")
        instructions.pack(fill="x", padx=20, pady=(10, 0))

        text_area = tk.Text(root, height=20, width=80, font=("Courier", 10, "bold"))
        text_area.pack(padx=20, pady=20)
        text_area.focus_set()

        def clear_text():
            text_area.delete("1.0", "end")

        def parse_list():
            root.items = str_to_list(text_area.get("1.0", "end-1c"))
            root.destroy()

        btn_reset = tk.Button(button_frame, text="Reset", command=clear_text, width=15)
        btn_reset.pack(side="left", padx=10)

        btn_csv = tk.Button(button_frame, text="CSV", command=parse_list, width=15)
        btn_csv.pack(side="left", padx=10)

        root.mainloop()

        display_message("INFO", "Closing down input widget.")

        return root.items

    except Exception as e:
        display_message("ERROR", "Failed to compile data.", f"{e}")

        return []


def str_to_list(raw_text: str) -> list[list[str,]]:
    items = [item.strip() for item in raw_text.split("\n") if item.strip()]

    if not items:
        display_message("WARN", "No data found.")
        return []

    total_count = len(items)

    display_message("INFO", f"Total of {total_count} number of data retrieved.")

    # Perform the Multiple Check.
    remainder = total_count % cols

    if remainder != 0:
        n1 = total_count - remainder

        display_message(
            "ERROR",
            f"Expected {n1}, or {n1 + cols}; or multiples of {cols} number of data.",
        )

        return []

    display_message("SUCCESS", "Pagination data parsed.  Ready to write to CSV.")

    return [items[i : i + cols] for i in range(0, total_count, cols)]


def pre_lang():
    """
    Rename folder (and files) by prefixing two-character ISO language code.
    Creates a copy of the folder/file set.
    """
    print("\n>>> Select folder to process ...")

    dirpath_0 = str(identify_path("folder"))
    parent, base_0 = display_path_desc(dirpath_0, "folder")

    dirpath_1 = parse_pathname(parent, f"{lang_iso_2}_{base_0}", "", "folder")

    display_message("INFO", "New directory to be created.")
    display_path_desc(dirpath_1, "folder")

    # Create new folder.
    if not ensure_path_exists(dirpath_1, "folder"):
        display_message("WARN", "Terminating process.")
        return

    file_list = os.listdir(dirpath_0)

    if len(file_list):
        print("\n>>> Processing files ...")
    else:
        display_message("WARN", "Empty folder.")

    for index, filename in enumerate(file_list):
        print("")
        hor_bar(100, f"Processing '{filename}' ({index + 1} of {len(file_list)})...")

        base, ext = os.path.splitext(filename)

        if not ext.upper() == ".PSD":
            display_message("WARN", f"Skip '{filename}'.")
            continue

        # Copy file to new directory, then rename; filename includes extension name.
        copy_file(dirpath_0, dirpath_1, base, "psd")

        filepath_0 = parse_pathname(dirpath_1, base, "psd", "file")
        filepath_1 = parse_pathname(dirpath_1, f"{lang_iso_2}_{base}", "psd", "file")
        rename_path(filepath_0, filepath_1, "file")

        print("")
        hor_bar(100)


if __name__ == "__main__":
    welcome_sequence([mod_name, f"ver {mod_ver} {date}", email])

    print(input("\n>>> Press enter to continue ..."))

    confirm_exit = False

    while not confirm_exit:
        proper_resp = False
        resp = "C"

        while not proper_resp:
            print(
                "\n>>> Select an option :"
                "\n>>>  [P]repare reference files ?"
                "\n>>>  Prefix [L]anguage code ?"
                "\n>>>  E[X]it and close this window ?"
            )

            resp = input(">>> ").upper()

            proper_resp = True if resp in ["P", "L", "X"] else False

        if resp == "X":
            print("\n<=> Closing down ...")

            confirm_exit = True
        else:
            confirm_exit = False

            if resp == "P":
                prepare_files()

            if resp == "L":
                pre_lang()
