from argparse import ArgumentParser
from pathlib import Path


def add_arguments(parser: ArgumentParser) -> ArgumentParser:

    juicepress_group = parser.add_argument_group(
        "JuicePress", "Options to handle JuicePress extensions"
    )

    juicepress_group.add_argument(
        "--jp-profile",
        action="store_true",
        default=False,
        help="Enable queue profiling",
    )

    juicepress_group.add_argument(
        "--jp-profile-root",
        type=Path,
        default=Path("./juicepress/profile"),
        help="Queue profiling destination folder",
    )

    juicepress_group.add_argument(
        "--jp-queue",
        action="store_true",
        default=False,
        help="Enable JuicePress priority queueing",
    )

    juicepress_group.add_argument(
        "--jp-queue-file",
        type=Path,
        default=Path("juicepress.json"),
        help="Juicepress priority file",
    )

    return parser
