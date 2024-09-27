from argparse import ArgumentParser


def add_common_args(parser: ArgumentParser):
    parser.add_argument(
        "--env_name", help="Environment to run the script in", default="dev"
    )
    return parser
