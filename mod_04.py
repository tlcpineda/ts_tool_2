import os
import time

from box_lib import (
    display_box_path,
    extract_entry_meta,
    fetch_entry,
    get_box_entries,
    init_client,
    move_box_entry,
    rename_box_entry,
)
from lib import (
    clean_number,
    continue_sequence,
    copy_file,
    display_message,
    display_path_desc,
    ensure_path_exists,
    hor_bar,
    identify_path,
    parse_pathname,
    welcome_sequence,
)

# Module variables
mod_name = "Box API Operations"
mod_ver = "1"
date = "09 May 2026"
email = "tlcpineda.projects@gmail.com"
lang_iso_2 = "en"


def box_delay(sec: int) -> None:
    time.sleep(sec)


def parse_box_url(entry_type: str, entry_id: str) -> str:
    return f"https://app.box.com/{entry_type}/{entry_id}"


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
            display_box_path(client, parent_url)

            folder_entries = get_box_entries(client, parent_url)
            target_names = ["JPEG", "PSD", "JPG"]

            target_folders = [
                entry
                for entry in folder_entries
                if (entry.name or "").upper() in target_names and entry.type == "folder"
            ]

            len_targets = len(target_folders)

            if not len_targets:
                display_message(
                    "ERROR",
                    f"Subfolders 'JPEG' and 'PSD'  not found in folder (ID : {parent_id}).",
                )
                continue

            for folder_index, folder in enumerate(folder_entries):
                display_message(
                    "INFO",
                    f'Processing folder " {folder.name} " ({folder_index + 1} / {len_targets}) ... ',
                )

                subfolder_url = parse_box_url("folder", folder.id)
                subfolder_entries = get_box_entries(client, subfolder_url)
                len_sub_entries = len(subfolder_entries)

                if not len_sub_entries:
                    continue

                for entry_i, entry in enumerate(subfolder_entries):
                    display_message(
                        "INFO",
                        f"Processing '{entry.name}' ({entry_i + 1} / {len_sub_entries}) ... ",
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
                box_delay(3)  # 3-sec delay between folders.
            break

        except Exception as e:
            display_message("ERROR", "Failed to append language code to files.", f"{e}")
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
                "\n>>>  [M]ove file to term folder ?"
                "\n>>>  E[X]it and close this window ?"
            )

            resp = input(">>> ").upper()

            proper_resp = True if resp in ["B", "M", "X"] else False

        if resp == "X":
            print("\n<=> Closing down ...")

            confirm_exit = True
        else:
            confirm_exit = False

            if resp == "B":
                prefix_lang_code()

            if resp == "M":
                move_pdf()
