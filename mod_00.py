import csv
import json
import math
import os
import sys
import tkinter as tk
from datetime import datetime, timezone

from dotenv import load_dotenv
from PIL import Image

from lib import (
    clean_number,
    continue_sequence,
    copy_file,
    display_message,
    display_path_desc,
    ensure_path_exists,
    expand_path,
    hor_bar,
    identify_path,
    load_csv,
    parse_pathname,
    rename_path,
    welcome_sequence,
    write_to_csv,
)

# Module variables
mod_name = "Preliminary Works"
mod_ver = "1"
date = "23 Apr 2026"
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

# For table listing project cache data.
heads = ["Work ID", "LIT ID", "Title (JP)", "Title (EN)"]
col_widths = [7, 6, 20, 20]

cols = 8  # Currently eight (8) columns are set in pagination webpage.

# PSD file properties
psd_res = 600  # dpi
psd_h = 2560  # px

# Load .env file.
load_dotenv()
SRC_WEBAPP = os.getenv("WEBAPP", "")
PROJ_CACHE = expand_path(os.getenv("PROJ_CACHE", ""))
PROJ_DIR = expand_path(os.getenv("PARENT_LOCAL", ""))


class LogManager:
    def __init__(self, log_path):
        self.log_path = os.path.normpath(log_path)
        self.log = self.load()

    def __getitem__(self, index):
        return self.log[index]

    def __iter__(self):
        return iter(self.log)

    def __len__(self):
        return len(self.log)

    def add(self, entry):
        """
        Adds the new entry (dict) to log (list).
        """
        self.log.append(entry)
        return self.save()

    def load(self):
        """Read the JSON log file; returns a list."""
        if os.path.exists(self.log_path):
            try:
                with open(self.log_path, "r", encoding="utf-8") as log_file:
                    data = json.load(log_file)
                    return data if isinstance(data, list) else []

            except (json.JSONDecodeError, IOError) as e:
                display_message(
                    "WARN",
                    f"Cannot read log file : {os.path.basename(self.log_path)}",
                    f"{e}",
                )

                return []
        return []

    def save(self):
        """Save data to specified log file."""
        base = os.path.basename(self.log_path)
        temp_path = self.log_path + ".tmp"  # in case of fatal error in write process

        try:
            with open(temp_path, "w", encoding="utf-8") as log_file:
                json.dump(self.log, log_file, indent=2, ensure_ascii=False)

            # Replace the official file, by the temp file.
            os.replace(temp_path, self.log_path)
            display_message("INFO", f'New entry added to "{base}".')
            return True
        except Exception as e:
            if os.path.exists(temp_path):
                os.remove(temp_path)

            display_message("WARN", f"File save failed : {base}", f"{e}")
            display_path_desc(self.log_path, "file")
            return False


def sort_files() -> None:
    try:
        display_message("INFO", "Sorting reference files ... ")

        pagination_data, proj_name, vol_num, title_vol = gen_pagination()
        # List of reference PSD files.
        psd_filenames = [f"{row[2]}.psd" for row in pagination_data if row[6] == "—"]
        # List of referene JPEG files.
        jpg_filenames = [f"{row[3]}.jpg" for row in pagination_data if row[6] == "—"]

        # ### algo
        # for row in pagination_data:
        #     _, _, psd_name, jpeg_jp_name, ch_num, page_num, exclude_page, gtn = row

        #     if exclude_page == "—":
        #         psd_filenames.append(f"{psd_name}.psd")
        #         jpg_filenames.append(f"{jpeg_jp_name}.jpg")

        #         ch, is_main = clean_number(ch_num)
        #         print(f"\nCH : {ch}\n")

        #         ch_formatted = f"{'CH' if not ch.startswith('EX') else ''}{ch if is_main else ch.split('.')[0]}"

        #         ch_float = 1000 if ch.startswith("EX") else float(ch)
        #         ch_log = math.log(ch_float * (10 if ch_float < 10 else 1), 10)
        #         lead_0 = (
        #             ""
        #             if ch.startswith("EX") or ch_log > 3
        #             else "0" * (4 - math.floor(ch_log + 1))
        #         )

        #         print(f"{psd_name}.psd >>> {jpeg_jp_name}.jpeg : ")

        #         print(f"\nParent directory : {PROJ_DIR}\\{proj_name}:")
        #         print("    keep size and name")
        #         print(f" 1. /{int(float(vol_num))}.1 PSD/{ch_formatted}")
        #         print(f" 2. /{int(float(vol_num))}.2 JPEG/{ch_formatted}")

        #         is_GTNP = gtn == "○"
        #         gtn_marker = "GTN " if is_GTNP else ""
        #         psd_filename = (
        #             f"{gtn_marker}{title_vol}_{lead_0}{ch}_{int(page_num):03}"
        #         )
        #         print(f"\nWorking PSD files to be renamed as ' {psd_filename}.psd '.")
        #         print(f"      resize to {psd_res}dpi; height {psd_h}px")
        #         print(f"      is_GTNP : {is_GTNP}")
        #         print(
        #             f" 3. /V{int(vol_num):02} - {ch_formatted}/{title_vol}_{lead_0}{ch}"
        #         )
        #         print(
        #             "+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++\n"
        #         )
        # ### end algo

        print("\n>>> Identify folders containing reference files ...")

        jpeg_jp_dir, jpeg_num_missing = verify_contents_ref_folder(
            jpg_filenames, "Japanese JPEG files"
        )
        psd_files_dir, psd_num_missing = verify_contents_ref_folder(
            psd_filenames, "Typesetting files (PSD)"
        )

        # Proceed with sorting process only if both sets of files are complete.
        if jpeg_num_missing or psd_num_missing:
            display_message("WARN", "Incomplete reference files.")
            col_len = max(len(str(num)) for num in [jpeg_num_missing, psd_num_missing])
            print(f"<=>   Number of missing JPEG files : {jpeg_num_missing:>{col_len}}")
            print(f"<=>   Number of missing PSD files  : {psd_num_missing:>{col_len}}")
            return

        # Sorting files.
        # Parent of both chapter working files, and reference files.
        proj_parent = parse_pathname(PROJ_DIR, proj_name, "", "folder")

        # Parse parent directory local destination of reference files.
        # to be appended by chapter folders.
        ref_psd_parent = parse_pathname(
            proj_parent, f"{int(float(vol_num))}.1 PSD", "", "folder"
        )
        ref_jpg_parent = parse_pathname(
            proj_parent, f"{int(float(vol_num))}.2 JPEG", "", "folder"
        )

        for row in pagination_data:
            _, _, psd_name, jpeg_jp_name, ch_num, page_num, exclude_page, gtn = row

            if exclude_page == "—":  # "—" > False; ie row describes a working file.
                # Save a copy of the pair of files to reference directories.
                ch_name, ch_4 = parse_ch_name(ch_num)
                psd_dest = parse_pathname(ref_psd_parent, ch_name, "", "folder")
                jpg_dest = parse_pathname(ref_jpg_parent, ch_name, "", "folder")
                ensure_path_exists(psd_dest, "folder")
                ensure_path_exists(jpg_dest, "folder")
                copy_file(psd_files_dir, psd_dest, psd_name, "psd")
                copy_file(jpeg_jp_dir, jpg_dest, jpeg_jp_name, "jpg")

                # Resize PSD (600 dpi, 2560px H, proportional W), then save to working folder.
                psd_dest_w = parse_pathname(
                    proj_parent,
                    f"V{int(vol_num):02} - {ch_name}",
                    f"{title_vol}_{ch_4}",
                    "folder",
                )
                ensure_path_exists(psd_dest_w, "folder")
                psd_name_w = f"{'GTNP' if gtn == '○' else ''}{title_vol}_{ch_4}_{int(page_num):03}"
                resize_psd(psd_files_dir, psd_name, psd_dest_w, psd_name_w)

    except Exception as e:
        display_message(
            "ERROR", "Failed to sort reference files to working directories.", f"{e}"
        )


def resize_psd(src_dir, name_0, dest_dir, name_1) -> None:
    psd_src = parse_pathname(src_dir, name_0, "psd", "file")
    psd_dest = parse_pathname(dest_dir, name_1, "psd", "file")

    try:
        display_message("INFO", f"Processing file : {name_0}.psd ... ")

        with Image.open(psd_src) as img:
            # File resolution check.
            file_res_0 = img.info.get("dpi", (72, 72))[0]
            resampling_tech = Image.Resampling.LANCZOS

            # Reassign resampling technique with user preferrence or default value.
            if file_res_0 < psd_res:
                display_message(
                    "WARN",
                    f"Current file resolution ({file_res_0}) less than required ({psd_res}).",
                )
                resampling_tech = get_pref_tech()

            aspect_ratio = img.width / img.height
            width_1 = int(aspect_ratio * psd_h)

            # Resize and save image to destination directory.
            img_to_dest = img.resize((width_1, psd_h), resampling_tech)
            img_to_dest.save(
                psd_dest,
                dpi=(psd_res, psd_res),
                icc_profile=img.info.get("icc_profile"),
            )

        display_message("SUCCESS", "File resized and renamed.")
        display_path_desc(psd_dest, "file")

    except Exception as e:
        display_message("ERROR", f"Failed to process PSD file {name_0}.", f"{e}")


def get_pref_tech() -> Image.Resampling:
    RESAMPLING_OPTIONS = [
        ("NEAREST", Image.Resampling.NEAREST),
        ("LANCZOS", Image.Resampling.LANCZOS),
        ("BILINEAR", Image.Resampling.BILINEAR),
        ("BICUBIC", Image.Resampling.BICUBIC),
        ("BOX", Image.Resampling.BOX),
        ("HAMMING", Image.Resampling.HAMMING),
    ]
    tech_def = Image.Resampling.BICUBIC

    show_table(
        "Resampling Options",
        [3, 8],
        ["Index", "Name"],
        [[ind, name] for ind, (name, _) in enumerate(RESAMPLING_OPTIONS)],
    )

    while True:
        user_pref = input(
            f"\n>>> Select preferred technique. Default '{str(tech_def).split('.')[-1]}' : "
        ).strip()

        if user_pref == "":
            return tech_def  # Default value; no user input.

        if user_pref in list(range(len(RESAMPLING_OPTIONS))):
            return RESAMPLING_OPTIONS[int(user_pref)][1]
        else:
            display_message(
                "WARN", "Invalid option. Select an index from '0' up to '5' only."
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
    filenames: list[str], files_descriptor: str
) -> tuple[str, int]:
    print(f"\n>>>  {files_descriptor} : ")

    ref_folder = str(identify_path("folder"))

    _, base = display_path_desc(ref_folder, "folder")
    display_message("INFO", f"Verifying contents of folder '{base}' ...")

    ref_contents = os.listdir(ref_folder)
    missing_files = [name for name in filenames if name not in ref_contents]
    num_missing_files = 0

    if missing_files:
        num_missing_files = len(missing_files)
        display_message("WARN", f"Missing files ({num_missing_files}) from '{base}' :")
        print(f"<=>  {'\n<=>  '.join(missing_files)}\n")
    else:
        display_message("INFO", f"All required files in '{base}'.")

    return ref_folder, num_missing_files


def gen_pagination() -> tuple[list[list[str]], str, str, str]:
    try:
        cache = load_proj_cache()

        table_title = "PROJECT CACHE DATA"
        table = [
            [row["work_id"], row["lit_id"], row["title_jp"], row["title_en"]]
            for row in cache.load()
        ]

        # Show table of project titles.
        show_table(table_title, col_widths, heads, table)
        work_id, proj_name, title_en, vol_num = get_vol_details(cache)
        title_vol = f"{title_en}_{int(vol_num):03}"

        print(f"\n<=> Generating pagination data for ' {title_vol} ' ... ")

        csv_data = []

        # Check if CSV file exists from previous run.
        csv_path = os.path.join(PROJ_DIR, proj_name, f"{csv_name_pre} {title_vol}.csv")

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


def load_proj_cache() -> LogManager:
    cache_path = PROJ_CACHE

    display_message("INFO", "Loading project cache ... ")
    display_path_desc(cache_path, "file")

    cache = LogManager(cache_path)

    if not cache.load():
        display_message(
            "WARN", "File not found, or file is empty.  Add first entry ..."
        )
        cache.add(get_proj_details())

    return cache


def get_proj_details():
    created = datetime.now(timezone.utc).isoformat()
    proj_det = {
        "created": created,
        "work_id": "",
        "lit_id": "",
        "title_jp": "",
        "title_en": "",
    }

    print("\n>>> Add new project details ... ")

    keys = proj_det.keys()
    max_len_key = max(len(key) for key in keys)

    for key in keys:
        proj_val = proj_det[key]
        while not proj_val:
            proj_val = input(f">>>  {key:<{max_len_key}} : ").strip()
            if proj_val:
                proj_det[key] = proj_val

    return proj_det


def show_table(main_head: str, col_width: list, heads: list, table: list) -> None:
    line_width = 3 + sum(col_width) + len(col_width) * 3 + 2

    print("")

    hor_bar(line_width, main_head)

    print("")

    for index, row in enumerate([heads] + table):
        line = "<=> |"

        for jndex, item in enumerate(row):
            col_len = col_width[jndex]

            if index == 0:
                line += f" {item:^{col_len}} |"
            else:
                if jndex == 0 or jndex == 1:
                    line += f" {item:>{col_len}} |"
                else:
                    line += f" {item if len(item) <= col_len else f'{item[: col_len - 3]}...':<{col_len}} |"

        print(line)

    print("")
    hor_bar(line_width)


def get_vol_details(proj_cache: LogManager) -> tuple[str, ...]:
    proj_det = {}
    lit_id = ""
    title_en = ""
    vol_num = ""

    work_ids = [proj["work_id"] for proj in proj_cache.load()]

    resp = False
    work_id = ""

    while not resp:
        work_id = input(
            "\n>>> Enter 'Work ID' to select project (or '0' for a new project): "
        ).strip()

        if work_id in work_ids or work_id == "0":
            resp = True
        else:
            display_message(
                "WARN",
                f"'{work_id}' is not a valid input.",
            )

    if int(work_id):
        # Extract project details based on work_id (ultimately from index of the project on the cache).
        proj_index = work_ids.index(work_id)
        proj_det = proj_cache.__getitem__(proj_index)
        display_message("INFO", "Project selected from cache.")

    else:
        proj_det = get_proj_details()  # Get details as user input.
        proj_cache.add(proj_det)

    lit_id = proj_det["lit_id"]
    title_en = proj_det["title_en"]
    proj_name = f"LIT{int(lit_id):03} {proj_det['title_jp']}"

    print(f"<=>  #{work_id} {proj_name} ( {title_en} )")

    vol_num = input("\n>>> Enter volume number : ").strip()
    vol_num, _ = clean_number(vol_num)

    return work_id, proj_name, title_en, vol_num


def get_webapp_data(id: str, vol: str, title_vol: str) -> list[list[str,]]:
    print(f"\n<=> Copy data, filtered for volume (巻数) {vol}, on : ")
    print(f"\n    {SRC_WEBAPP}/{id}?tab=list")

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


if __name__ == "__main__":
    welcome_sequence([mod_name, f"ver {mod_ver} {date}", email])

    print(input("\n>>> Press enter to continue ..."))

    confirm_exit = False

    while not confirm_exit:
        # gen_pagination()
        sort_files()
        confirm_exit = continue_sequence()
