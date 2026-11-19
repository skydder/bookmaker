import argparse
from bookmaker.core import compile_booklet_order, split_and_enlarge_a4


def main():
    parser = argparse.ArgumentParser(
        prog="bookmaker",
        description="make books",
    )
    parser.add_argument("input_file", help="pdf file")
    parser.add_argument("output_file", help="pdf file")
    parser.add_argument(
        "-s",
        "--split",
        action="store_true",
        help="split A4 pages in half and enlarge each half back to A4",
    )
    parser.add_argument(
        "--rtl",
        action="store_true",
        help="use right-to-left reading order (for both booklet and split)",
    )
    parser.add_argument(
        "-p",
        "--padding",
        choices=["back", "even", "front"],
        default="back",
        help="where to insert blank padding pages (default: back)",
    )
    args = parser.parse_args()

    if args.split:
        split_and_enlarge_a4(
            args.input_file,
            args.output_file,
            right_to_left=args.rtl,
        )
    else:
        compile_booklet_order(
            args.input_file,
            args.output_file,
            pad_mode=args.padding,
            right_to_left=args.rtl,
        )