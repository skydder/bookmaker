import argparse
from bookmaker.core import (
    PAPER_SIZES,
    concat_pdfs,
    impose_2up_pdf,
    reorder_pdf,
    resize_pdf,
    rotate_pdf,
    split_pdf,
)


def parse_argument():
    parser = argparse.ArgumentParser(
        prog="bookmaker",
        description="PDF manipulation utilities for booklet making",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # 1. リサイズ (resize)
    p_resize = subparsers.add_parser("resize", help="resize PDF pages")
    p_resize.add_argument("input_file", help="input PDF file")
    p_resize.add_argument("output_file", help="output PDF file")
    group = p_resize.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "-s", "--scale", type=float, help="scale factor (e.g. 1.4142 or 0.7071)"
    )
    group.add_argument(
        "-p", "--paper", choices=list(PAPER_SIZES.keys()), help="target paper size"
    )
    p_resize.add_argument(
        "--landscape", action="store_true", help="use landscape orientation with --paper"
    )

    # 2. 分割 (split)
    p_split = subparsers.add_parser("split", help="split pages in half")
    p_split.add_argument("input_file", help="input PDF file")
    p_split.add_argument("output_file", help="output PDF file")
    p_split.add_argument(
        "--rtl", action="store_true", help="use right-to-left reading order"
    )

    # 3. 並び変え (reorder)
    p_reorder = subparsers.add_parser("reorder", help="reorder pages for booklet printing")
    p_reorder.add_argument("input_file", help="input PDF file")
    p_reorder.add_argument("output_file", help="output PDF file")
    p_reorder.add_argument(
        "--rtl", action="store_true", help="use right-to-left reading order"
    )
    p_reorder.add_argument(
        "-p",
        "--padding",
        choices=["back", "even", "front"],
        default="back",
        help="where to insert blank padding pages (default: back)",
    )
    p_reorder.add_argument(
        "--signature",
        type=int,
        default=None,
        help="sheets per signature (e.g. 4 for 16-page signatures)",
    )

    # 4. 統合 (merge)
    p_merge = subparsers.add_parser(
        "merge", help="merge pages (2-up imposition or file concatenation)"
    )
    p_merge.add_argument(
        "-m",
        "--mode",
        choices=["2up", "concat"],
        default="2up",
        help="2up: impose 2 pages onto 1 sheet (default), concat: join multiple PDFs",
    )
    p_merge.add_argument("inputs", nargs="+", help="input PDF file(s)")
    p_merge.add_argument("-o", "--output", required=True, help="output PDF file")

    # 5. 回転 (rotate)
    p_rotate = subparsers.add_parser("rotate", help="rotate PDF pages")
    p_rotate.add_argument("input_file", help="input PDF file")
    p_rotate.add_argument("output_file", help="output PDF file")
    p_rotate.add_argument(
        "-a",
        "--angle",
        type=int,
        choices=[0, 90, 180, 270, -90, -180, -270],
        required=True,
        help="clockwise rotation angle in degrees (0 can be used with --bake)",
    )
    p_rotate.add_argument(
        "--pages",
        type=str,
        default=None,
        help="target pages (1-indexed, e.g. '1,3,5-8'; default: all pages)",
    )
    p_rotate.add_argument(
        "--bake",
        action="store_true",
        help="apply rotation directly to page content stream instead of /Rotate metadata",
    )

    return parser.parse_args()


def main():
    args = parse_argument()

    if args.command == "resize":
        resize_pdf(
            args.input_file,
            args.output_file,
            scale=args.scale,
            paper_size=args.paper,
            landscape=args.landscape,
        )
    elif args.command == "split":
        split_pdf(
            args.input_file,
            args.output_file,
            right_to_left=args.rtl,
        )
    elif args.command == "reorder":
        reorder_pdf(
            args.input_file,
            args.output_file,
            pad_mode=args.padding,
            right_to_left=args.rtl,
            sheets_per_signature=args.signature,
        )
    elif args.command == "merge":
        if args.mode == "2up":
            if len(args.inputs) != 1:
                raise ValueError("'2up' mode requires exactly 1 input file.")
            impose_2up_pdf(args.inputs[0], args.output)
        elif args.mode == "concat":
            concat_pdfs(args.inputs, args.output)
    elif args.command == "rotate":
        rotate_pdf(
            args.input_file,
            args.output_file,
            angle=args.angle,
            page_spec=args.pages,
            bake=args.bake,
        )