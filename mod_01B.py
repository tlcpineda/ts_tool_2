import csv

from lib import (
    continue_sequence,
    display_message,
    load_csv,
    welcome_sequence,
    write_to_csv,
)

# Module variables
mod_name = "Normal Coordinates Calculator"
mod_ver = "1"
date = "11 Apr 2026"
email = "tlcpineda.projects@gmail.com"
csv_name = "translations.csv"  # The filename of the output CSV file


def finalise_csv():
    try:
        csv_data, csv_path = load_csv()

        if csv_path:
            updated_list = calc_coords(csv_data)

            write_to_csv(csv_path, updated_list)

    except Exception as e:
        display_message(
            "ERROR",
            f"Failed to calculate coordinates.  Verify file '{csv_name}'.",
            f"{e}",
        )


def calc_coords(data) -> list:
    """
    Calculates x0 and y0 using direct indices.
    [0]page_num, [1]panel, [2]x0, [3]y0, [4]w_box, [5]h_box, [6]text
    """
    if not data or len(data) < 2:
        return data

    header = data[0]
    rows = data[1:]

    # Configuration constants
    vertical_step = 0.10
    horizontal_step = 0.12
    top_margin = 0.05

    current_page = 0
    current_panel = 0
    right_cursor = 1.0

    for row in rows:
        page = int(row[0])
        panel = int(row[1])

        # Reset R-to-L cursor if we hit a new panel or page.
        if page != current_page or panel != current_panel:
            current_page = page
            current_panel = panel
            right_cursor = 1.0

        # Calculate y0: Stays the same for all boxes in the same panel.
        y0 = top_margin + ((panel - 1) * vertical_step)
        row[3] = round(y0, 5)

        # Calculate x0: Moves left as more boxes are added to the panel.
        x0 = right_cursor - horizontal_step
        row[2] = round(x0, 5)

        # Update cursor for the next text block in this panel.
        right_cursor = x0

        # Stringify page number; padded to have three digits.
        row[0] = f"{page:03}"

        # Remove panel number column.
        row.pop(1)

    header.pop(1)
    rows = sort_rtl(rows, True)

    return [header] + rows


def sort_rtl(page_data: list, rtl: bool) -> list:
    """
    Sort the comments according to (x0, y0).
    :param page_data: The list of comments for the current page
    :param rtl: True follows Japanese manga reading order.
    :return: The reversed list of sorted comments; which reverts to proper order when transferred to Photoshop.
    """
    sorted_data = sorted(page_data, key=lambda x: (x[0], -x[2], x[1] * rtl))

    # Truncate x0, y0 to (at most) 6 decimal places.
    return list(map(lambda x: [x[0], f"{x[1]:g}", f"{x[2]:g}"] + x[3:], sorted_data))


if __name__ == "__main__":
    welcome_sequence([mod_name, f"ver {mod_ver} {date}", email])

    print(input("\n>>> Press enter to continue ..."))

    confirm_exit = False

    while not confirm_exit:
        finalise_csv()
        confirm_exit = continue_sequence()
