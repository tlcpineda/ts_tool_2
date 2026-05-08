import os

from box_sdk_gen import BoxClient, BoxDeveloperTokenAuth, FolderMini, Item
from dotenv import load_dotenv

from lib import display_message

# Load .env file.
load_dotenv()
BOX_DEV_CONSOLE = os.getenv("BOX_DEV_CONSOLE", "")


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


def display_box_path(client: BoxClient, entry_id: str) -> None:
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
        [client.folders.get_folder_by_id, client.files.get_file_by_id], entry_id
    )

    if entry:
        entry_name = entry.name
        entry_type = entry.type.title()
        path_collection = entry.path_collection
        path_entries = [] if not path_collection else path_collection.entries

        print(f"\n<=> Box {entry_type} Details :")
        print(f"<=>  {entry_type} ID   : {entry_id}")
        print(f"<=>  {entry_type} Path : {join_path_names(path_entries)}")
        print(f"<=>  {entry_type} Name : {entry_name}")


def fetch_entry(funcs, *args, **kwargs):
    def toggle(func):
        try:
            return func(*args, **kwargs)
        except Exception:
            return None

    return [toggle(func) for func in funcs if toggle(func)][0]


def get_box_entries(client: BoxClient, folder_id: str) -> list[Item] | None:
    return client.folders.get_folder_items(folder_id).entries


def extract_entry_id(entry_url: str) -> str:
    entry_id = ""

    if "folder" in entry_url:
        entry_id = entry_url.split("/")[-1]

        if "?" in entry_id:
            entry_id = entry_id.split("?")[0]

    return entry_id


def rename_box_entry(client: BoxClient, entry_id: str, new_entry_name: str):
    entry = fetch_entry(
        [client.folders.update_folder_by_id, client.files.update_file_by_id],
        entry_id,
        name=new_entry_name,
    )

    if entry:
        display_box_path(client, entry.id)


def test():
    c = init_client()
    fid = "2219648284799"  # CH73.pdf
    # id = "379147674223"
    rename_box_entry(c, fid, "en__.pdf")


if __name__ == "__main__":
    test()
