import csv
import json
import os
import tkinter as tk
from datetime import datetime, timezone
from tkinter import filedialog as fd


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


def copy_file(source_dir: str, dest_dir: str, filename: str, extname: str) -> None:
    # Creates a copy of the file (Manual Binary Copy) to revision folder.
    file_path_0 = parse_pathname(source_dir, filename, extname, "file")
    file_path_1 = parse_pathname(dest_dir, filename, extname, "file")

    try:
        with open(file_path_0, "rb") as f_src:
            with open(file_path_1, "wb") as f_dst:
                # Copying in 1MB chunks to be safe with large files
                while True:
                    chunk = f_src.read(1024 * 1024)
                    if not chunk:
                        break
                    f_dst.write(chunk)

        display_message("SUCCESS", f"File copied to '{os.path.basename(dest_dir)}'.")
        display_path_desc(file_path_1, "file")

    except Exception as e:
        display_message("ERROR", "Failed to copy file.", f"{e}")


def parse_pathname(parent_dir: str, basename: str, extname: str, pathtype: str) -> str:
    if pathtype == "file":
        dest_path = os.path.join(parent_dir, f"{basename}.{extname}")
    else:  # folder
        dest_path = os.path.join(parent_dir, basename, extname)

    return os.path.normpath(dest_path)


def show_proj_in_cache(cache: list) -> None:
    heads = ["Work ID", "LIT ID", "Title (EN)", "Title (JP)"]
    col_widths = [7, 6, 30, 30]

    table_title = "PROJECT CACHE DATA"
    table = [
        [row["work_id"], row["lit_id"], row["title_en"], row["title_jp"]]
        for row in cache
    ]

    # Show table of project titles.
    show_table(table_title, col_widths, heads, table)


def load_proj_cache(cache_path: str) -> LogManager:
    display_message("INFO", "Loading project cache ... ")
    display_path_desc(cache_path, "file")

    cache = LogManager(cache_path)

    if not cache.load():
        display_message(
            "WARN", "File not found, or file is empty.  Add first entry ..."
        )
        cache.add(get_proj_details())

    return cache


def parse_chapters(ch_in: str) -> list[str] | None:
    def list_strip(items: str, sep: str) -> list[str]:
        list_items = [item.strip() for item in items.split(sep)]

        if sep == "-":
            t0, t1 = list_items
            rng = range(int(float(t0)) + 1, int(float(t1)) + 1)
            list_items = flat([t0, [str(s) for s in rng], t1])

        return list_items

    def flat(items: list[str | list[str]]) -> list[str]:
        flat_list = []

        for item in items:
            if isinstance(item, list):
                for i in item:
                    flat_list.append(i)
            else:
                flat_list.append(item)

        return flat_list

    ch_list = None

    # Split by comma separation.
    ch_list = list_strip(ch_in, ",")

    # Check if any element is a range; then list range elements.
    ch_list = flat([ch if "-" not in ch else list_strip(ch, "-") for ch in ch_list])

    # Prefix "CH" on chapter numbers, except for extra chapters (startswith "EX").
    ch_list = [
        ch.upper() if ch.upper().startswith("EX") else f"CH{clean_number(ch)[0]}"
        for ch in ch_list
    ]

    # Return list of unique entries.
    return sorted(list(set(ch_list)))


def get_cached_proj_details(cache: LogManager) -> dict:
    proj_det = {}
    work_id = ""
    resp = False
    projects = cache.load()
    work_ids = [proj["work_id"] for proj in projects]

    show_proj_in_cache(projects)
    while not resp:
        work_id = input(
            '\n>>> Enter "Work ID" to select project (or "0" for a new project) : '
        ).strip()

        if work_id in work_ids or work_id == "0":
            resp = True
        else:
            display_message("WARN", f'"{work_id}" is not a valid input.')

    if int(work_id):
        # Extract project details based on work_id (ultimately from index of the project on the cache).
        proj_index = work_ids.index(work_id)
        proj_det = cache.__getitem__(proj_index)
        display_message("INFO", "Project selected from cache.")

    else:  # work_id == 0; input new project details.
        # TODO loop system to be able to edit input if needed.
        proj_det = get_proj_details()  # Get details as user input.
        work_id = proj_det["work_id"]
        cache.add(proj_det)
        display_message("INFO", "New project details added to cache.")

    print(
        f"<=>  #{work_id} LIT{int(proj_det['lit_id']):03} {proj_det['title_jp']} ( {proj_det['title_en']} )"
    )

    return proj_det


def get_term_details(
    cache: LogManager,
) -> tuple[str, str, str, str, str, list[str]]:
    """
    Get details for the term from user input.
    :param cache:
    :return work_id, proj_name, title_en, vol_num, term, chapters:
    """
    vol_num = ""
    term = ""
    chapters = []

    proj_det = get_cached_proj_details(cache)
    work_id = proj_det["work_id"]
    title_en = proj_det["title_en"]
    proj_name = f"LIT{int(proj_det['lit_id']):03} {proj_det['title_jp']}"

    vol_num = input("\n>>> Enter volume number : ").strip()
    vol_num, _ = clean_number(vol_num)

    while not term:
        term_num = input("\n>>> Enter term number (0#) : ").strip()

        if term_num:
            term = f"Term {int(term_num):02}"
        else:
            display_message("WARN", "Term number cannot be blank.")

    while not chapters:
        print(
            "\n>>> Enter chapters numbers ... \
            \n>>>  [1] As a range, dash          : 48.5 - 50     ---> [48.5, 48 ,49, 50]\
            \n>>>  [2] As comma-separated values : 46.5, 49, 55  ---> [46.5, 49, 55]\
            \n>>>  [3] Or, both                  : 46, 49 - 52.5 ---> [46, 49, 50, 51, 52, 52.5]"
        )
        ch_numbers = input(">>> ").strip()
        chapters = parse_chapters(ch_numbers)

    hor_bar(100)

    show_table(
        "Input Summary",
        [
            3,
            16,
            max(40, min(len(f"{chapters}"), 81)),
        ],
        ["", "Parameters", "Input Value(s)"],
        [
            ["1", "Work ID", work_id],
            ["2", "Project Name", proj_name],
            ["3", "Title (EN)", title_en],
            ["4", "Volume", vol_num],
            ["5", "Term", term],
            ["6", "Chapter List", f"{chapters}"],
        ],
    )
    print("")

    return work_id, proj_name, title_en, vol_num, term, chapters


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
    line_width = max(
        3 + sum(col_width) + len(col_width) * 3 + 2, len(main_head) + 2 * (2 + 5)
    )

    print("")

    hor_bar(line_width, main_head.upper())

    print("")

    for index, row in enumerate([heads] + table):
        line = "<=>  "

        for jndex, item in enumerate(row):
            col_len = col_width[jndex]

            terminal_bar = " " if jndex == len(row) - 1 else "|"

            if index == 0:
                line += f" {item:^{col_len}} {terminal_bar}"
            else:
                if jndex == 0 or jndex == 1:
                    line += f" {item:>{col_len}} {terminal_bar}"
                else:
                    line += f" {item if len(item) <= col_len else f'{item[: col_len - 3]}...':<{col_len}} {terminal_bar}"

        print(line)

    print("")
    hor_bar(line_width)
