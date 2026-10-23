import argparse
from bookmaker.core import compile_booklet_order

def main() -> None:
    parser = argparse.ArgumentParser(
        prog="bookmaker",
        description="make books",
    )
    parser.add_argument("input_file", help="pdf file")
    parser.add_argument("output_file", help="pdf file")
    args = parser.parse_args()

    compile_booklet_order(args.input_file, args.output_file)
