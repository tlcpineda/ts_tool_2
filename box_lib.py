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

from lib import display_message

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
                display_message("INFO", f"Token input : {token}")

        client = BoxClient(auth=BoxDeveloperTokenAuth(token))

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
    print(manager)

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

            return display_path

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
            display_message("SUCCESS", f'New folder "{target_name}" created.')

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
    entry_type, entry_id = extract_entry_meta(entry_url)
    new_parent_id = ""
    dest_url = ""

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


# def copy_box_entry(client: BoxClient, entry_url: str):
#     entry_type, entry_id = extract_entry_meta(entry_url)
#     new_parent_id = ""
#     dest_url = ""

#     try:
#         params = [
#             ("info", lambda: {}),
#             ("copy", lambda: {"parent": {"id": new_parent_id}}),
#         ]

#         # somethng else here

#     except Exception as e:
#         display_message(
#             "ERROR", f"Failed to copy {entry_type} (ID : {entry_id}).", f"{e}"
#         )


def ensure_box_path_exists(client: BoxClient, parent_url: str, target_name: str) -> str:
    _, parent_id = extract_entry_meta(parent_url)
    display_message(
        "INFO", f'Checking folder " {target_name} " in parent (ID : {parent_id}) ... '
    )
    display_box_path(client, parent_url)

    target_id = ""

    try:
        children = get_box_entries(client, parent_url)

        if children:
            target = [child for child in children if child.name == target_name]

            if target:
                display_message(
                    "INFO", f'Folder " {target_name} " already exists in parent.'
                )
                target_id = target[0].id
            else:
                display_message(
                    "WARN", f'Folder " {target_name} " not found in parent.'
                )
        else:
            display_message("WARN", f'Folder " {target_name} " not found in parent.')

        if not target_id:
            print(f'>>> Creating " {target_name} " in parent ... ')
            target = create_box_folder(client, parent_url, target_name)

            if target:
                target_id = target.id

    except Exception as e:
        display_message(
            "ERROR",
            f'Failed to verify presence and/or create " {target_name} " in parent.',
            f"{e}",
        )

    return target_id


def get_path_entries(entry: FolderFull | FileFull) -> list[FolderMini]:
    path_collection = entry.path_collection
    return path_collection.entries if path_collection else []


def get_box_entries(client: BoxClient, folder_url: str) -> list[Item]:
    _, folder_id = extract_entry_meta(folder_url)

    try:
        box_items = client.folders.get_folder_items(folder_id)
        box_entries = box_items.entries
        entries_count = box_items.total_count or 0
        disp_msg_i = "No entries found on"

        if entries_count:
            disp_msg_i = f"Total of {entries_count} item{'s' if entries_count > 1 else ''} retrieved from"

        display_message(
            "SUCCESS",
            f"{disp_msg_i} folder (ID : {folder_id}) .",
        )

        return box_entries or []

    except Exception as e:
        display_message(
            "ERROR", f"Failed to get entries in folder (ID : {folder_id})", f"{e}"
        )

        return []
