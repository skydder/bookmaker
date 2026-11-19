import copy
from pypdf import PageObject, PdfReader, PdfWriter, Transformation


def compile_booklet_order(
    input_file,
    output_file,
    pad_mode="back",
    right_to_left=False,
    sheets_per_signature=None,
):
    reader = PdfReader(input_file)
    pages = list(reader.pages)

    width = float(reader.pages[0].mediabox.width)
    height = float(reader.pages[0].mediabox.height)
    blank = PageObject.create_blank_page(width=width, height=height)

    reordered = reorder_in_booklet_order(
        pages,
        blank,
        pad_mode=pad_mode,
        right_to_left=right_to_left,
        sheets_per_signature=sheets_per_signature,
    )

    imposed = impose_2up_landscape(reordered, width, height)

    writer = PdfWriter()
    for sheet in imposed:
        writer.add_page(sheet)

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
    sheets_per_signature=None,
):
    pages = list(pages)
    add_padding(pages, padding, mode=pad_mode)

    if sheets_per_signature:
        chunk_size = sheets_per_signature * 4
    else:
        chunk_size = len(pages)

    reordered = []
    for start in range(0, len(pages), chunk_size):
        chunk = pages[start : start + chunk_size]
        chunk_len = len(chunk)

        for i in range(chunk_len // 4):
            p1 = chunk_len - 1 - (i * 2)
            p2 = 0 + (i * 2)
            p3 = 1 + (i * 2)
            p4 = chunk_len - 2 - (i * 2)

            if right_to_left:
                reordered.extend([chunk[p2], chunk[p1], chunk[p4], chunk[p3]])
            else:
                reordered.extend([chunk[p1], chunk[p2], chunk[p3], chunk[p4]])

    return reordered


def impose_2up_landscape(pages, orig_width, orig_height):
    # A4縦 (orig_width x orig_height) -> A4横 (orig_height x orig_width)
    sheet_width = orig_height
    sheet_height = orig_width
    scale = 1 / (2**0.5)
    half_sheet_width = sheet_width / 2

    imposed_sheets = []

    for i in range(0, len(pages), 2):
        sheet = PageObject.create_blank_page(
            width=sheet_width, height=sheet_height
        )

        # 左ページ配置
        left = copy.deepcopy(pages[i])
        left.transfer_rotation_to_content()
        sheet.merge_transformed_page(
            left,
            Transformation().scale(sx=scale, sy=scale).translate(tx=0, ty=0),
        )

        # 右ページ配置
        if i + 1 < len(pages):
            right = copy.deepcopy(pages[i + 1])
            right.transfer_rotation_to_content()
            sheet.merge_transformed_page(
                right,
                Transformation()
                .scale(sx=scale, sy=scale)
                .translate(tx=half_sheet_width, ty=0),
            )

        imposed_sheets.append(sheet)

    return imposed_sheets


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