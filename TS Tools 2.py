"""
A compilation of modules to assist in local processes during typesetting.
"""

from lib import hor_bar, welcome_sequence
from mod_01A import create_pre_csv
from mod_01B import finalise_csv
from mod_03 import compile_revision

# App variables
app_name = "Typesetting Tools 2"
app_ver = "2.00.00"
date = "13 Apr 2026"
email = "tlcpineda.projects@gmail.com"
options = [
    {
        "menu": "[S]crape translations",
        "shortkey": "S",
        "func": create_pre_csv,
    },
    {
        "menu": "[F]inalise translations CSV",
        "shortkey": "F",
        "func": finalise_csv,
    },
    {
        "menu": "Compile [R]evision files",
        "shortkey": "R",
        "func": compile_revision,
    },
    {"menu": "E[X]it and close window", "shortkey": "X"},
]


def display_menu():
    print("")

    hor_bar(60, "MENU")

    for option in options:
        print(f"{' ':5}{option['menu']}")

    hor_bar(60)

    print("\n>>> Select an option ...")


if __name__ == "__main__":
    welcome_sequence(
        [
            app_name,
            f"ver {app_ver} {date}",
            email,
        ]
    )

    confirm_exit = False

    while not confirm_exit:
        display_menu()
        user_input = None

        while not user_input:
            resp = input(">>> ").upper()

            if resp in [option["shortkey"] for option in options]:
                user_input = resp

        if user_input == "X":
            hor_bar(60, "CLOSING DOWN ...")
            confirm_exit = True
        else:
            print("")

            selected_option = [
                option for option in options if option["shortkey"] == user_input
            ][0]
            func_selected = selected_option["func"]  # requires input_path

            hor_bar(60, f"RUNNING : {func_selected.__name__}()")
            func_selected()
            hor_bar(60, f"COMPLETE : {func_selected.__name__}()")
