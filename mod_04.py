import os
import time
from datetime import datetime

import win32com.client as win32
from dotenv import load_dotenv

from box_lib import (
    copy_box_entry,
    display_box_path,
    dl_box_entry,
    ensure_box_folder_exists,
    extract_entry_meta,
    fetch_entry,
    find_box_entry_by_name,
    get_box_entries,
    init_client,
    move_box_entry,
    parse_box_url,
    rename_box_entry,
)
from lib import (
    LogManager,
    display_message,
    display_path_desc,
    expand_path,
    get_cached_proj_details,
    get_term_details,
    hor_bar,
    load_proj_cache,
    parse_pathname,
    show_table,
    welcome_sequence,
)

# Module variables
mod_name = "Box API Operations"
mod_ver = "2"
date = "15 May 2026"
email = "tlcpineda.projects@gmail.com"
lang_iso_2 = "en"

# Load .env file.
load_dotenv()
PROJ_CACHE = expand_path(os.getenv("PROJ_CACHE", ""))
TS_PARENT = os.getenv("TS_PARENT", "")
TL_REVIEWED = os.getenv("TL_REVIEWED", "")
CR_PARENT = os.getenv("CR_PARENT", "")
CR_FEEDBACK = os.getenv("CR_FEEDBACK", "")
PARENT_LOCAL = expand_path(os.getenv("PARENT_LOCAL", ""))


def box_delay(sec: int) -> None:
    time.sleep(sec)


def prefix_lang_code():
    """
    Affix two-character ISO language code to files already in Box;
    intended as an ad-hoc function.
    """

    # Input developer token.
    client = init_client()

    if not client:
        return

    while True:
        parent_urls = input(
            '\n>>> Input URL(s) of folder(s), comma-separated, to be processed ("Q" to quit) : '
        ).strip()

        if not parent_urls:
            display_message("WARN", "No URL input.")
            continue

        parents_split = [url.strip() for url in parent_urls.split(",")]

        if parent_urls[0].upper() == "Q":
            display_message("WARN", "Terminating process.")
            break

        len_parents_split = len(parents_split)

        for parent_index, parent_u in enumerate(parents_split):
            parent_type, parent_id = extract_entry_meta(parent_u)

            if not parent_id or parent_type != "folder":
                display_message("ERROR", "Invalid URL input.")
                continue

            try:
                parent = fetch_entry(client, parent_u, ("info", {}))

                if not parent:
                    display_message("ERROR", "Invalid Box folder URL.")

                hor_bar(100)
                display_message(
                    "INFO",
                    f"Processing folder (ID : {parent_id}) ({parent_index + 1} / {len_parents_split}) ... ",
                )
                display_box_path(client, parent_u)

                folder_entries = get_box_entries(client, parent_u)
                target_names = ["JPEG", "PSD", "JPG"]

                target_folders = [
                    entry
                    for entry in folder_entries
                    if (entry.name or "").upper() in target_names
                    and entry.type == "folder"
                ]

                len_targets = len(target_folders)

                if not len_targets:
                    display_message(
                        "ERROR",
                        f'Subfolders "JPEG" and "PSD"  not found in folder (ID : {parent_id}).',
                    )
                    continue

                for folder_index, folder in enumerate(folder_entries):
                    display_message(
                        "INFO",
                        f'Processing folder "{folder.name}" ({folder_index + 1} / {len_targets}) ... ',
                    )

                    subfolder_url = parse_box_url("folder", folder.id)
                    subfolder_entries = get_box_entries(client, subfolder_url)
                    len_sub_entries = len(subfolder_entries)

                    if not len_sub_entries:
                        continue

                    for entry_i, entry in enumerate(subfolder_entries):
                        display_message(
                            "INFO",
                            f'Processing "{entry.name}" ({entry_i + 1} / {len_sub_entries}) ... ',
                        )

                        if entry.type == "file":
                            if (entry.name or "").startswith(lang_iso_2):
                                print("<=>  Skip file.")
                            else:
                                file_url = parse_box_url("file", entry.id)

                                rename_box_entry(
                                    client, file_url, f"{lang_iso_2}_{entry.name}"
                                )

                        box_delay(1)  # 1-sec delay between files.
                    hor_bar(100)
                    box_delay(1)  # 2-sec delay between folders.

            except Exception as e:
                display_message(
                    "ERROR", "Failed to append language code to files.", f"{e}"
                )
                break
        break


def move_pdf():
    client = init_client()

    if not client:
        return

    while True:
        parent_url = input(
            "\n>>> Input URL of folder to be processed ('Q' to quit) : "
        ).strip()

        if not parent_url:
            display_message("WARN", "No URL input.")
            continue

        if parent_url.upper() == "Q":
            display_message("WARN", "Terminating process.")
            break

        parent_type, parent_id = extract_entry_meta(parent_url)

        if not parent_id or parent_type != "folder":
            display_message("ERROR", "Invalid Box folder URL.")
            continue

        try:
            parent = fetch_entry(client, parent_url, ("info", {}))

            if not parent:
                display_message("ERROR", "Invalid Box folder URL.")

            hor_bar(100)
            display_message("INFO", f"Processing folder (ID : {parent_id})")

            folder_entries = get_box_entries(client, parent_url)
            len_f_entries = len(folder_entries)

            for folder_i, folder in enumerate(folder_entries):
                # folder_id = folder.id
                folder_url = parse_box_url("folder", folder.id)
                folder_name = folder.name

                display_message(
                    "INFO",
                    f"Processing folder ( {folder_i + 1} / {len_f_entries} ) ... ",
                )
                display_box_path(client, folder_url)
                display_message("INFO", "Retrieving Box entries ... ")

                subentries = get_box_entries(client, folder_url)
                target_name = f"{folder_name}.pdf"
                target_entry = [
                    entry
                    for entry in subentries
                    if (entry.type == "file" and entry.name == target_name)
                ]

                if len(target_entry) != 1:
                    display_message(
                        "ERROR",
                        f"Something wrong with target PDF file, {target_name}.\
                        \nVerify contents of parent folder ( {folder_url} )",
                    )
                    break

                target_url = parse_box_url("file", target_entry[0].id)

                move_box_entry(client, target_url, True)
                # print(f'Moving "{target_url}" ... ')

                hor_bar(100)
                box_delay(1)
            break

        except Exception as e:
            display_message("ERROR", "Failed to move PDF files to term folder.", f"{e}")
            break


def create_term_tree() -> dict[str, str]:
    chapter_urls = {}
    parent_url = TS_PARENT
    client = init_client()

    if not client:
        display_message("ERROR", "Failed to create BoxClient object.")
        return {}

    cache = load_proj_cache(PROJ_CACHE)
    _, proj_name, title_en, _, term, ch = get_term_details(cache)
    box_delay(2)

    try:
        for branch_name in [term, proj_name, ch]:
            if isinstance(branch_name, str):
                hor_bar(100)
                box_delay(2)

                branch_id = ensure_box_folder_exists(client, parent_url, branch_name)

                if branch_id:
                    parent_url = parse_box_url("folder", branch_id)

            elif isinstance(branch_name, list):
                for sibling in branch_name:
                    hor_bar(100)
                    box_delay(2)
                    sibling_id = ensure_box_folder_exists(client, parent_url, sibling)
                    chapter_urls[sibling] = parse_box_url("folder", sibling_id)

        hor_bar(100)

        show_table(
            f"New Box Folders for {term} : {proj_name.split(' ')[0]} {title_en}",
            [3, 10, 50],
            ["", "Chapters", "Folder URL"],
            [[i + 1, k, v] for i, (k, v) in enumerate(chapter_urls.items())],
        )

        return chapter_urls

    except Exception as e:
        display_message("ERROR", "Failed to create term tree in Box.", f"{e}")
        return {}


def copy_ts_files():
    """
    Copy latest revision typesetting files (PDF/JPEG)
    where chapter has no client feedback/request for revisions.
    """
    client = init_client()

    # Terminate process when BoxClient is not created.
    if not client:
        return

    cache = load_proj_cache(PROJ_CACHE)
    source_parent = TS_PARENT
    dest_parent = CR_PARENT
    sources = {}

    _, proj_name, _, _, term, ch = get_term_details(cache)

    if not client:
        display_message("ERROR", "Failed to create BoxClient object.")
        return

    try:
        # Find folders (IDs) containing files to be copied (by chapter) from Typesetting folder;
        # and, the folder (ID) where the files are to be sent revisions folder.
        for folder_name in [term, proj_name, ch]:
            if isinstance(folder_name, str):
                source = find_box_entry_by_name(
                    client, source_parent, "folder", folder_name
                )

                if source:  # source becomes source_parent.
                    source_parent = parse_box_url("folder", source.id)

                # Assign new destination parent; create new, when required.
                dest_id = ensure_box_folder_exists(client, dest_parent, folder_name)
                dest_parent = parse_box_url("folder", dest_id)

            elif isinstance(folder_name, list):
                for sibling in folder_name:
                    source = find_box_entry_by_name(
                        client, source_parent, "folder", sibling
                    )

                    if source:
                        source_id = source.id
                        sources[sibling] = parse_box_url("folder", source_id)

        # Copy source folders to destination.
        for ch, url in sources.items():
            hor_bar(100)
            box_delay(1)  # 2-sec delay between sources
            copy_box_entry(client, url, dest_parent)

    except Exception as e:
        display_message("ERROR", f"Failed to copy typesetting files.{e}")


def fetch_client_cr() -> None:
    def get_range_from_name(entry_name) -> range:
        id_range = range(0)

        base, _ = os.path.splitext(entry_name)
        str_range = base.split("No.")[1]

        i, o = str_range.split("-")

        id_range = range(int(i), int(o) + 1)

        return id_range

    def purge_xlsx(xlsx_path: str, tab_name: str, work_id: str):
        """
        Open a local Excel file natively through Windows COM.
        Keep first two tabs and the project tab,
        and delete all other tabs.
        """
        excel_app = win32.Dispatch("Excel.Application")
        excel_app.Visible = False
        excel_app.DisplayAlerts = False

        display_message("INFO", "Purging Client CR file ... ")
        _, base = display_path_desc(xlsx_path, "file")

        try:
            workbook = excel_app.Workbooks.Open(
                Filename=xlsx_path, CorruptLoad=win32.constants.xlRepairFile
            )

            # Delete the unnecessary tabs. Loop backwards; prevents index shift.
            for i in range(len(workbook.Sheets), 2, -1):
                sheet = workbook.Sheets(i)
                sheetname = sheet.Name

                if sheetname == tab_name:
                    display_message(
                        "INFO", f"Project sheet encountered ( {sheetname} )."
                    )
                    sheet.Name = f"{work_id}. {sheetname}"
                    display_message("INFO", "Sheet renamed.")
                else:
                    display_message("INFO", f"Deleting sheet : {sheetname} ... ")
                    sheet.Delete()
                    # shell.SendKeys("{ENTER}")
                    display_message("SUCCESS", "Sheet deleted.")

            # Save the changes back to the original file.
            workbook.SaveAs(Filename=xlsx_path)
            workbook.Close()
            display_message("SUCCESS", f"Client CR file ( {base} ) purged.")

        except Exception as e:
            display_message(
                "ERROR", f"Failed to purge client CR file ( {base} ).", f"{e}"
            )

        finally:
            excel_app.Quit()

    try:
        client = init_client()

        # Terminate process if BoxClient is not created.
        if not client:
            raise Exception("Failed to create Box client.")

        proj_cache = load_proj_cache(PROJ_CACHE)
        proj_det = get_cached_proj_details(proj_cache)
        work_id = proj_det["work_id"]
        title_jp = proj_det["title_jp"]

        feedback_files = get_box_entries(client, CR_FEEDBACK)
        req_file_id = ""

        for item in feedback_files:
            item_name = item.name or ""

            if "No." not in item_name:
                continue

            work_id_range = get_range_from_name(item_name)

            if int(work_id) in work_id_range:
                req_file_id = item.id

                display_message("SUCCESS", "Required Client CR file identified.")
                display_box_path(client, parse_box_url("file", req_file_id))
                break

        if not req_file_id:
            raise Exception("Failed to identify required file.")

        dl_name = f"{datetime.now().strftime('%Y%m%d')} CR - {work_id}"
        display_message(
            "INFO",
            f'Downloading required file as "{dl_name}.xlsx" ... ',
        )

        dl_dest_path = parse_pathname(PARENT_LOCAL, dl_name, "xlsx", "file")
        dl_stat = dl_box_entry(client, req_file_id, dl_dest_path)

        if dl_stat:
            purge_xlsx(dl_dest_path, title_jp, work_id)

    except Exception as e:
        display_message("ERROR", "Failed to fetch CR file.", f"{e}")


def fetch_tl() -> None:
    try:
        client = init_client()

        if not client:
            raise Exception("Failed to create Box client.")

        cache = load_proj_cache(PROJ_CACHE)
        _, proj_name, _, vol_num, term, chapters = get_term_details(cache)
        proj_code, _ = proj_name.split(" ")
        source_parent = TL_REVIEWED

        # Search Box parent folder containing translation documents.
        for folder_name in [term, proj_code]:
            if isinstance(folder_name, str):
                source = find_box_entry_by_name(
                    client, source_parent, "folder", folder_name
                )

                if source:  # source becomes source_parent.
                    source_parent = parse_box_url("folder", source.id)
                else:
                    raise Exception("Failed to trace parentage.")

        tl_docs = get_box_entries(client, source_parent)

        if not tl_docs:
            raise Exception(f"Failed to list translation documents for {term}.")

        dl_info = {}

        # Loop through user-specified chapters to get matching translation document.
        for ch in chapters:
            display_message("INFO", f"File Selection for {ch} ... ")

            show_table(
                f"{term}-{proj_code} Reviewed Translations",
                [3, 13, 50],
                ["DOC", "Box ID", "Filename"],
                [[i + 1, doc.id, doc.name] for i, doc in enumerate(tl_docs)],
            )

            # Select file to download by "DOC" number.
            resp = False
            doc_num = 0
            tl_id = ""
            tl_bname = ""
            tl_extname = ""

            while not resp:
                doc_num = int(
                    input(
                        f'\n>>> Enter "DOC" number for {ch} ("0" to skip chapter): '
                    ).strip()
                )

                if doc_num in range(1, len(tl_docs) + 1):
                    resp = True
                elif doc_num == 0:
                    display_message("WARN", f"Skip {ch}.")
                    resp = True
                else:
                    display_message("WARN", f'"{doc_num}" is not a valid input.')

            if doc_num:
                # Pick entry ID based on DOC number; index of tl_docs.
                tl_file = tl_docs[int(doc_num) - 1]
                tl_id = tl_file.id
                tl_bname, tl_extname = os.path.splitext(tl_file.name or "")
                entry_url = parse_box_url("file", tl_id)

                display_message("INFO", "Translation file selected for download.")
                display_box_path(client, entry_url)

                tl_dest_p = os.path.join(PARENT_LOCAL, proj_name, f"V{vol_num} - {ch}")
                tl_dest = parse_pathname(tl_dest_p, tl_bname, tl_extname[1:], "file")

                dl_info[ch] = {"box_id": tl_id, "dest_path": tl_dest}

        for k, v in dl_info.items():
            f_id = v["box_id"]
            f_dest = v["dest_path"]

            display_message("INFO", f"Downloading Box file (ID : {f_id}) ... ")
            display_path_desc(f_dest, "file")

            dl_stat = dl_box_entry(client, f_id, f_dest)

            if dl_stat:
                display_message("SUCCESS", "File successfully download.")
            else:
                raise Exception("Failed to download file.")

        return None

    except Exception as e:
        display_message("ERROR", "Failed to fetch translation document.", f"{e}")
        return None


def fetch_data_files() -> None:
    def get_source_url(cache: LogManager, work_id: str) -> tuple[str, str]:
        url_jpeg = ""
        url_psd = ""
        projects = cache.load()
        req_proj = [proj for proj in projects if proj["work_id"] == work_id]

        if req_proj:
            url_jpeg = req_proj[0]["source_url_jpeg"]
            url_psd = req_proj[0]["source_url_psd"]

        return url_jpeg, url_psd

    try:
        cache = load_proj_cache(PROJ_CACHE)
        work_id, proj_name, _, vol_num, _, _ = get_term_details(cache)
        url_j, url_p = get_source_url(cache, work_id)

        client = init_client()

        if not client:
            raise Exception("Failed to create Box client.")

        for ext in ["PSD", "JPEG"]:
            url = url_j if ext == "JPEG" else url_p

            print(
                f"\n<=> Get source folder ({ext}) URL for {proj_name} V{vol_num} starting at : "
            )
            print(f"\n      {url}")
            input("\n>>> Press ENTER to continue ... ")
            source_url = input(f"\n>>> Input source URL for {ext} files : ").strip()

            zip_dest_path = parse_pathname(
                os.path.join(PARENT_LOCAL, proj_name),
                f"{work_id} - {int(vol_num)} {ext}",
                "zip",
                "file",
            )

            e_type, e_id = extract_entry_meta(source_url)
            dl_stat = dl_box_entry(client, [(e_id, e_type)], zip_dest_path)

            if dl_stat:
                display_message("SUCCESS", f"Source {ext} files downloaded.")
            else:
                raise Exception("Failed to download file.")

    except Exception as e:
        display_message("ERROR", "Failed to fetch typesetting data from Box.", f"{e}")


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
                "\n>>>  Rename [B]ox files (EN) ?"
                "\n>>>  [C]reate typesetting term folder ?"
                "\n>>>  [M]ove PDF files to term folder ?"
                "\n>>>  F[E]tch revision file/tab ?"
                "\n>>>  Fetc[H] translation file/s ?"
                "\n>>>  [D]ownload source files ?"
                "\n>>>  Copy [T]ypesetting files to Revisions folder ?"
                "\n>>>  E[X]it and close this window ?"
            )

            resp = input(">>> ").upper()

            proper_resp = (
                True if resp in ["B", "C", "D", "E", "H", "M", "T", "X"] else False
            )

        if resp == "X":
            print("\n<=> Closing down ...")

            confirm_exit = True
        else:
            confirm_exit = False

            if resp == "B":
                prefix_lang_code()

            elif resp == "M":
                move_pdf()

            elif resp == "C":
                create_term_tree()

            elif resp == "T":
                copy_ts_files()

            elif resp == "E":
                fetch_client_cr()

            elif resp == "H":
                fetch_tl()

            elif resp == "D":
                fetch_data_files()
