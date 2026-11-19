import copy
from pypdf import PageObject, PdfReader, PdfWriter, Transformation


def compile_booklet_order(
    input_file,
    output_file,
    pad_mode="back",
    right_to_left=False,
):
    reader = PdfReader(input_file)
    pages = list(reader.pages)

    width = reader.pages[0].mediabox.width
    height = reader.pages[0].mediabox.height
    blank = PageObject.create_blank_page(width=width, height=height)

    reordered = reorder_in_booklet_order(
        pages,
        blank,
        pad_mode=pad_mode,
        right_to_left=right_to_left,
    )

    writer = PdfWriter()
    for page in reordered:
        writer.add_page(page)

    with open(output_file, "wb") as f:
        writer.write(f)


def split_and_enlarge_a4(input_file, output_file, right_to_left=False):
    reader = PdfReader(input_file)
    pages = list(reader.pages)

    processed = split_and_enlarge_pages(pages, right_to_left=right_to_left)

    writer = PdfWriter()
    for page in processed:
        writer.add_page(page)

    with open(output_file, "wb") as f:
        writer.write(f)


def split_and_enlarge_pages(pages, right_to_left=False):
    scale_factor = 2**0.5
    result = []

    for orig_page in pages:
        page = copy.deepcopy(orig_page)
        page.transfer_rotation_to_content()

        width = float(page.mediabox.width)
        height = float(page.mediabox.height)

        if width > height:
            half_width = width / 2

            left_page = copy.deepcopy(page)
            left_page.mediabox.upper_right = (half_width, height)
            left_page.cropbox.upper_right = (half_width, height)
            left_page.scale_by(scale_factor)

            right_page = copy.deepcopy(page)
            right_page.add_transformation(
                Transformation().translate(tx=-half_width, ty=0)
            )
            right_page.mediabox.lower_left = (0, 0)
            right_page.mediabox.upper_right = (half_width, height)
            right_page.cropbox.lower_left = (0, 0)
            right_page.cropbox.upper_right = (half_width, height)
            right_page.scale_by(scale_factor)

            if right_to_left:
                result.extend([right_page, left_page])
            else:
                result.extend([left_page, right_page])
        else:
            half_height = height / 2

            top_page = copy.deepcopy(page)
            top_page.add_transformation(
                Transformation().translate(tx=0, ty=-half_height)
            )
            top_page.mediabox.lower_left = (0, 0)
            top_page.mediabox.upper_right = (width, half_height)
            top_page.cropbox.lower_left = (0, 0)
            top_page.cropbox.upper_right = (width, half_height)
            top_page.scale_by(scale_factor)

            bottom_page = copy.deepcopy(page)
            bottom_page.mediabox.upper_right = (width, half_height)
            bottom_page.cropbox.upper_right = (width, half_height)
            bottom_page.scale_by(scale_factor)

            result.extend([top_page, bottom_page])

    return result


def reorder_in_booklet_order(
    pages,
    padding,
    pad_mode="back",
    right_to_left=False,
):
    pages = list(pages)
    add_padding(pages, padding, mode=pad_mode)
    reordered = []
    page_count = len(pages)

    for i in range(int(page_count / 4)):
        p1 = page_count - 1 - (i * 2)
        p2 = 0 + (i * 2)
        p3 = 1 + (i * 2)
        p4 = page_count - 2 - (i * 2)

        if right_to_left:
            reordered.extend([pages[p2], pages[p1], pages[p4], pages[p3]])
        else:
            reordered.extend([pages[p1], pages[p2], pages[p3], pages[p4]])

    return reordered


def add_padding(pages, padding, mode="back"):
    remainder = len(pages) % 4
    if remainder == 0:
        return

    pad_count = 4 - remainder

    if mode == "even":
        front_pads = pad_count // 2
        back_pads = pad_count - front_pads
    elif mode == "front":
        front_pads = pad_count
        back_pads = 0
    else:  # "back"
        front_pads = 0
        back_pads = pad_count

    pages[:] = ([padding] * front_pads) + pages + ([padding] * back_pads)