import os

from PIL import Image

from lib import (
    continue_sequence,
    display_message,
    display_path_desc,
    ensure_path_exists,
    identify_path,
    welcome_sequence,
)

# Module variables
mod_name = "Compile Revision Files"
mod_ver = "1"
date = "13 Apr 2026"
email = "tlcpineda.projects@gmail.com"
compile_dir_base = "COMPILED-JPG TO PDF"
jpeg_res = 72  # dpi


def compile_revision() -> None:
    print(">>> Select source PSD folder ...")

    path = str(identify_path("folder"))

    if not path:
        print("\n<=> No folder selected.")
        return

    input_path = os.path.normpath(path)  # Normalise path.

    display_message("INFO", "Processing files in folder ...")

    parent, base = display_path_desc(input_path, "folder")
    psd_dir, jpeg_dir, pdf_name = gen_revision_pathnames(parent, base)
    psd_files = filter_files(input_path)

    if not psd_files:
        print("\n<=> No PSD file fit to be compiled.")
        return

    psd_files.sort()
    for_pdf_pages = []

    try:
        # Ensure that destination folders exists.
        ensure_path_exists(psd_dir, "folder")
        ensure_path_exists(jpeg_dir, "folder")

        for file_ind, filename in enumerate(psd_files):
            source_file = os.path.join(input_path, filename)

            display_message(
                "INFO", f"Processing file {file_ind} of {len(psd_files)}..."
            )
            display_path_desc(source_file, "file")

            # Create matchng JPEG file.
            with Image.open(source_file) as img:
                base_filename = os.path.splitext(filename)[0]
                rgb_img = img.convert("RGB")
                jpeg_path = save_jpeg(rgb_img, jpeg_dir, base_filename)

                # Append path of saved JPEG file, file PDF compilation.
                for_pdf_pages.append(jpeg_path)

            copy_psd(source_file, psd_dir, base_filename)

        if for_pdf_pages:
            for_pdf_pages = [p for p in for_pdf_pages if p.strip()]
            compile_pdf_file(for_pdf_pages, pdf_name)

        return

    except Exception as e:
        display_message("ERROR", "Failed to compile revision folder.", f"{e}")

        return


def save_jpeg(rgb: Image.Image, dest_path: str, jpeg_name: str) -> str:
    jpeg_path = compile_dest_path(dest_path, jpeg_name, "jpg", "file")

    try:
        # Save JPEG to local directory.
        rgb.save(jpeg_path, "JPEG", dpi=(jpeg_res, jpeg_res))

        display_message("SUCCESS", "JPEG file saved to revision folder.")
        display_path_desc(jpeg_path, "file")

        return jpeg_path

    except Exception as e:
        display_message("ERROR", "Failed to save file.", f"{e}")

        return ""


def copy_psd(source_path: str, dest_path: str, psd_name: str) -> None:
    # Creates a copy of the PSD file (Manual Binary Copy) to revision folder.
    psd_path = compile_dest_path(dest_path, psd_name, "psd", "file")

    try:
        with open(source_path, "rb") as f_src:
            with open(psd_path, "wb") as f_dst:
                # Copying in 1MB chunks to be safe with large PSD files
                while True:
                    chunk = f_src.read(1024 * 1024)
                    if not chunk:
                        break
                    f_dst.write(chunk)

        display_message("SUCCESS", "PSD file copied to revision folder.")
        display_path_desc(psd_path, "file")

    except Exception as e:
        display_message("ERROR", "Failed to copy PSD file.", f"{e}")


def compile_pdf_file(image_paths: list, pdf_path: str) -> None:
    def img_generator(image_paths):
        for path in image_paths:
            with Image.open(path) as img:
                yield img.convert("RGB")

    try:
        # Open the first image as the anchor.
        with Image.open(image_paths[0]) as first_img:
            base_img = first_img.convert("RGB")

            # The 'append_images' parameter accepts the generator
            base_img.save(
                pdf_path,
                "PDF",
                resolution=jpeg_res,
                save_all=True,
                append_images=img_generator(image_paths[1:]),
            )

        display_message("SUCCESS", "Revision PDF file created.")
        display_path_desc(pdf_path, "file")

    except Exception as e:
        display_message("ERROR", "Failed to compile revision PDF file.", f"{e}")


def compile_dest_path(
    parent_dir: str, basename: str, extname: str, pathtype: str
) -> str:
    if pathtype == "file":
        dest_path = os.path.join(parent_dir, f"{basename}.{extname}")
    else:  # folder
        dest_path = os.path.join(parent_dir, f"{basename}/{extname}")

    return os.path.normpath(dest_path)


def gen_revision_pathnames(parent_dir, basename) -> tuple[str, ...]:
    def clean_number(num: str) -> tuple:
        """
        Strip leading/trailing zeroes from chapter numbers.
        Main chapters (including extra chapters) are numbered with integers.
        """
        ch_num = 0
        is_main_ch = False

        try:
            if num.startswith("EX"):  # Handle extra chapters; ie "EX01", "EX02".
                ch_num = num.upper()
                is_main_ch = True

            else:  # Handle numeric chapters ("0068", "0068.5", etc)
                n = float(num)

                if n.is_integer():
                    ch_num = int(n)
                    is_main_ch = True
                else:
                    ch_num = n
                    is_main_ch = False
        except ValueError as v:
            display_message(
                "ERROR", f"Invalid chapter format, {num}.  Check folder name.", f"{v}"
            )

        except Exception as e:
            display_message("ERROR", "Failed to extract chapter number.", f"{e}")

        return ch_num, is_main_ch

    psd_path = ""
    jpeg_path = ""
    pdf_path = ""
    ch_num, is_main_ch = clean_number(basename.split("_")[-1].strip())
    current_num_rev_dir = count_rev_dirs(parent_dir, is_main_ch)

    display_message(
        "INFO",
        f"Creating pathnames for chapter {ch_num} (rev. {current_num_rev_dir}) ...",
    )

    try:
        current_rev_dir = f"{compile_dir_base}{current_num_rev_dir}"
        # pdf_name = f"CH{ch_num}"
        # pdf_name = ch_num if ch_num.startswith("EX") else f"CH{ch_num}"

        psd_path = compile_dest_path(parent_dir, current_rev_dir, "PSD", "folder")
        jpeg_path = compile_dest_path(parent_dir, current_rev_dir, "JPEG", "folder")
        pdf_path = compile_dest_path(
            os.path.join(parent_dir, current_rev_dir),
            ch_num if ch_num.startswith("EX") else f"CH{ch_num}",
            "pdf",
            "file",
        )

        for path in [psd_path, jpeg_path, pdf_path]:
            display_path_desc(path, "file" if path == pdf_path else "folder")

        display_message("SUCCESS", "Path names created.  Pending actual creation.")

    except Exception as e:
        display_message("ERROR", "Failed to generated revision directory.", f"{e}")

    return psd_path, jpeg_path, pdf_path


def count_rev_dirs(directory: str, is_main: bool) -> str:
    rev_num = ""

    # List folders that starts with {compile_dir_base}.
    rev_dirs = [d for d in os.listdir(directory) if d.startswith(compile_dir_base)]

    # Return revision number based on filtered list for revisions either for main or sub chapters.
    if is_main:
        rev_dirs = [d for d in rev_dirs if "." not in d]
        rev_num = str(len(rev_dirs) + 1)
    else:
        rev_dirs = [d for d in rev_dirs if "." in d]
        rev_num = f"{len(rev_dirs) + 1}.5"

    return rev_num


def filter_files(source_path: str) -> list:
    """
    Filter files that follow the filename pattern, with the last two/three digits as the page markers.
    :param folder: The parent folder of the PSD files
    :return filtered_files: The list of filtered PSD files to be compiled
    """
    display_message("INFO", "Filtering files ...")
    parent_folder, base_folder = display_path_desc(source_path, "folder")

    source_files = os.listdir(source_path)

    try:
        filtered_files = []

        for f in source_files:
            filename, extname = os.path.splitext(f)

            if (
                filename.startswith(base_folder) and extname.lower() == ".psd"
            ):  # Append file to return list if page_marker exists.
                filtered_files.append(f)
                print(f"\n<=>  {f} -> INCLUDE")
            else:
                print(f"\n<=>  {f} -> EXCLUDE")

        display_message(
            "SUCCESS",
            f"Total of {len(filtered_files)} out of {len(source_files)} files found.",
        )

        return filtered_files

    except Exception as e:
        display_message("ERROR", f"Failed to filter files in {source_path}.", f"{e}")

        return []  # Return empty list.


if __name__ == "__main__":
    welcome_sequence([mod_name, f"ver {mod_ver} {date}", email])

    print(input("\n>>> Press enter to continue ..."))

    confirm_exit = False

    while not confirm_exit:
        compile_revision()
        confirm_exit = continue_sequence()
