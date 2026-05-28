import os

from box_sdk_gen import (
    BoxClient,
    BoxDeveloperTokenAuth,
    CreateFolderParent,
    FileFull,
    FilesManager,
    FolderFull,
    FolderMini,
    FoldersManager,
    Item,
)
from dotenv import load_dotenv

from lib import display_message, display_path_desc

# Load .env file.
load_dotenv()
BOX_DEV_CONSOLE = os.getenv("BOX_DEV_CONSOLE", "")
TS_PARENT = os.getenv("TS_PARENT", "")


def init_client() -> BoxClient | None:
    try:
        token = ""

        print("\n<=> Generate token at : ")
        print(f"\n      {BOX_DEV_CONSOLE}")
        input("\n>>> Press enter to continue ... ")

        # Input Box Developer Console token.
        while not token:
            token = input("\n>>> Input Box Developer Token ('Q' to quit) : ").strip()

            if not token:
                display_message("WARN", "Token is required.")
            elif token.upper() == "Q":
                display_message("WARN", "Process terminated.")
                return None
            else:
                display_message("INFO", "Creating BoxClient object ... ")

        client = BoxClient(auth=BoxDeveloperTokenAuth(token))

        display_message("SUCCESS", "BoxClient object created.")

        return client

    except Exception as e:
        display_message("ERROR", "Failed to initialise Client object.", f"{e}")
        return None


def init_mngr(
    client: BoxClient, entry_type: str
) -> FoldersManager | FilesManager | None:

    try:
        return getattr(client, f"{entry_type.lower()}s")
    except Exception as e:
        display_message(
            "ERROR", f"Failed to create {entry_type.title()} Manager.", f"{e}"
        )
        return None


def extract_entry_meta(entry_url: str) -> tuple[str, str]:
    entry_type = ""
    entry_id = ""

    parts = entry_url.strip().rstrip("/").split("/")

    if len(parts) > 2 and "app.box.com" in parts:
        entry_type, entry_id = parts[-2:]

        if "?" in entry_id:
            entry_id = entry_id.split("?")[0]

    return entry_type, entry_id


def parse_box_url(entry_type: str, entry_id: str) -> str:
    return f"https://app.box.com/{entry_type}/{entry_id}"


def fetch_entry(
    client: BoxClient, entry_url: str, params: tuple[str, dict]
) -> FolderFull | FileFull | None:
    def def_entry(func, *args, **kwargs):
        return func(*args, **kwargs)

    entry_type, entry_id = extract_entry_meta(entry_url)
    method, kwargs = params

    manager = init_mngr(client, entry_type)

    if not manager:
        return None

    funcs = {
        "info": getattr(manager, f"get_{entry_type}_by_id"),
        "update": getattr(manager, f"update_{entry_type}_by_id"),
        "copy": getattr(manager, f"copy_{entry_type}"),
    }

    if entry_type and entry_id:
        return def_entry(funcs[method], entry_id, **kwargs)

    return None


def display_box_path(client: BoxClient, entry_url: str) -> None:
    entry_type, entry_id = extract_entry_meta(entry_url)

    try:

        def join_path_names(path_entries: list[FolderMini]) -> str:
            display_level = 3
            display_path = ""
            path_names = [entry.name for entry in path_entries if entry.name]

            if len(path_names) > display_level:
                path_names = path_names[-1 * display_level :]
                display_path = ".../"

            display_path += "/".join(path_names)

            return display_path or "---"

        entry = fetch_entry(
            client,
            entry_url,
            ("info", {}),
        )

        if entry:
            entry_type = entry.type.title()
            entry_id = entry.id
            path_entries = get_path_entries(entry)

            print(f"\n<=> Box {entry_type} Details :")
            print(f"<=>  {entry_type} ID   : {entry_id}")
            print(f"<=>  {entry_type} Path : {join_path_names(path_entries)}")
            print(f"<=>  {entry_type} Name : {entry.name}")

    except Exception as e:
        display_message(
            "ERROR",
            f"Failed to display Box {entry_type.lower()} path (ID : {entry_id})",
            f"{e}",
        )


def create_box_folder(
    client: BoxClient, parent_url: str, target_name: str
) -> FolderFull | None:
    _, parent_id = extract_entry_meta(parent_url)
    target = None

    try:
        display_message("INFO", f'Creating "{target_name}" in parent ... ')

        manager = init_mngr(client, "folder")

        if type(manager) is FoldersManager:
            target = manager.create_folder(
                target_name, CreateFolderParent(id=parent_id)
            )

        if target:
            display_message(
                "SUCCESS", f'New folder "{target_name}" created (ID : {target.id}).'
            )

    except Exception as e:
        display_message("ERROR", f'Failed to create "{target_name}" in parent.', f"{e}")

    return target


def rename_box_entry(client: BoxClient, entry_url: str, new_entry_name: str):
    entry_type, entry_id = extract_entry_meta(entry_url)

    try:
        params = [("info", {}), ("update", {"name": new_entry_name})]

        display_message("INFO", f"Renaming {entry_type} ... ")

        for param in params:
            entry = fetch_entry(client, entry_url, param)

            if entry:
                display_box_path(client, entry_url)

        display_message("SUCCESS", f"{entry_type.title()} renamed.")

    except Exception as e:
        display_message(
            "ERROR", f"Failed to rename {entry_type} (ID : {entry_id}).", f"{e}"
        )


def move_box_entry(client: BoxClient, entry_url: str, default_loc: bool):
    # Move entry one level up within path_collection; index -2 of path collection
    move_up_one = -2
    new_parent_id = ""
    dest_url = ""
    entry_type, entry_id = extract_entry_meta(entry_url)

    try:
        params = [
            ("info", lambda: {}),
            ("update", lambda: {"parent": {"id": new_parent_id}}),
        ]

        if not default_loc:
            dest_url = input(">>> Input new parent URL : ").strip()

        display_message("INFO", f"Moving {entry_type} ... ")

        for method, get_kwargs in params:
            entry = fetch_entry(client, entry_url, (method, get_kwargs()))

            display_box_path(client, entry_url)

            if entry:
                # Default to "move up".
                path_entries = get_path_entries(entry)
                new_parent_id = path_entries[move_up_one].id

                if dest_url:
                    _, new_parent_id = extract_entry_meta(dest_url)

        display_message("SUCCESS", f"{entry_type.title()} moved.")

    except Exception as e:
        display_message(
            "ERROR", f"Failed to move {entry_type} (ID : {entry_id}).", f"{e}"
        )


def copy_box_entry(client: BoxClient, entry_url: str, dest_url: str) -> str:
    entry_type, entry_id = extract_entry_meta(entry_url)
    dest_type, dest_id = extract_entry_meta(dest_url)

    dest = fetch_entry(client, dest_url, ("info", {}))

    if dest_type != "folder" or not dest:
        display_message("ERROR", "Invalid destination URL.")
        return ""

    try:
        params = [
            ("info", {}),
            ("copy", {"parent": {"id": dest_id}}),
        ]

        display_message("INFO", f"Copying {entry_type} ... ")

        for param in params:
            entry = fetch_entry(client, entry_url, param)

            if entry:
                entry_id = entry.id
                entry_type = entry.type.lower()
                entry_url = parse_box_url(entry_type, entry_id)

            display_box_path(client, entry_url)

        display_message(
            "SUCCESS", f"{entry_type.title()} copied to destination folder."
        )
        return entry_url

    except Exception as e:
        display_message(
            "ERROR", f"Failed to copy {entry_type} (ID : {entry_id}).", f"{e}"
        )

        return ""


def dl_box_entry(client: BoxClient, entry_id: str, dl_to_path: str) -> bool:
    """
    :param entry_id: ID of the entry to be downloaded.
    future to include download of folders and its contents
    """
    try:
        box_stream = client.downloads.download_file(entry_id)

        if not box_stream:
            raise Exception("Box API issue client.downloads.download_file().")

        with open(dl_to_path, "wb") as local_file:
            chunk_size = 65536

            while True:
                chunk = box_stream.read(chunk_size)

                if not chunk:
                    break

                local_file.write(chunk)

        display_message("INFO", "Download complete.")
        display_path_desc(dl_to_path, "file")
        return True

    except Exception as e:
        display_message("ERROR", f"Failed to download file (ID : {entry_id})", f"{e}")
        return False


def ensure_box_folder_exists(
    client: BoxClient, parent_identifier: str, folder_name: str
) -> str:
    """
    parent_identifier : could be URL or ID; URL preferred.
    """
    parent_url = parent_identifier  # Default to URL as identifier.
    _, parent_id = extract_entry_meta(parent_url)

    if not parent_id:
        parent_url = parse_box_url("folder", parent_identifier)

    target = None

    try:
        target = find_box_entry_by_name(client, parent_url, "folder", folder_name)

        if not target:
            target = create_box_folder(client, parent_url, folder_name)

        return target.id if target else ""

    except Exception as e:
        display_message(
            "ERROR",
            f'Failed to verify presence and/or create "{folder_name}" in parent.',
            f"{e}",
        )

        return ""


def find_box_entry_by_name(
    client: BoxClient, parent_url: str, entry_type: str, entry_name: str
) -> Item | None:
    """
    :param parent_url: URL of the folder containing the item.
    :param entry_type: Either "folder" or "file".
    :param entry_name: Case-sensitive, including extension name for the case of "file" entries.
    """

    def disp_msg(state: bool) -> None:
        disp_stat = "INFO" if state else "WARN"
        disp_msg = f'{entry_type.title()} entry "{entry_name}" {"" if state else "not "}found in parent.'

        display_message(disp_stat, disp_msg)

    _, parent_id = extract_entry_meta(parent_url)
    entry_type = entry_type.lower()

    display_message(
        "INFO",
        f'Checking for {entry_type} "{entry_name}" in parent (ID : {parent_id}) ... ',
    )
    display_box_path(client, parent_url)

    entry = None

    try:
        # Get children of parent folder; check if target entry is one of the children.
        children = get_box_entries(client, parent_url)

        if children:
            entry0 = [
                child
                for child in children
                if (child.name == entry_name and child.type == entry_type)
            ]
            entry = entry0[0] if entry0 else None

        disp_msg(bool(entry))

    except Exception as e:
        display_message("ERROR", f'Failed to find "{entry_name}" in parent.', f"{e}")

    return entry


def get_path_entries(entry: FolderFull | FileFull) -> list[FolderMini]:
    path_collection = entry.path_collection
    return path_collection.entries if path_collection else []


def get_box_entries(client: BoxClient, folder_url: str) -> list[Item]:
    _, folder_id = extract_entry_meta(folder_url)

    try:
        box_items = client.folders.get_folder_items(folder_id)
        box_entries = box_items.entries
        entries_count = box_items.total_count or 0
        disp_stat = "WARN"
        disp_msg_i = "No entries found on"

        if entries_count:
            disp_stat = "INFO"
            disp_msg_i = f"Total of {entries_count} item{'s' if entries_count > 1 else ''} retrieved from"

        display_message(
            disp_stat,
            f"{disp_msg_i} folder (ID : {folder_id}) .",
        )

        return box_entries or []

    except Exception as e:
        display_message(
            "ERROR", f"Failed to get entries in folder (ID : {folder_id})", f"{e}"
        )

        return []
