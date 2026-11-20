import copy
from pypdf import PageObject, PdfReader, PdfWriter, Transformation

# 標準用紙サイズ (ポイント単位: 1pt = 1/72 inch)
PAPER_SIZES = {
    "a3": (841.89, 1190.55),
    "a4": (595.28, 841.89),
    "a5": (419.53, 595.28),
    "b4": (728.50, 1031.81),
    "b5": (515.91, 728.50),
}


def _read_pages(input_file):
    reader = PdfReader(input_file)
    return list(reader.pages)


def _write_pages(pages, output_file):
    writer = PdfWriter()
    for page in pages:
        writer.add_page(page)
    with open(output_file, "wb") as f:
        writer.write(f)


def _parse_page_indices(page_spec, total_pages):
    """'1,3,5-7' のような1始まりのページ指定文字列を0始まりのインデックス集合に変換する"""
    if not page_spec:
        return set(range(total_pages))

    indices = set()
    for part in page_spec.split(","):
        part = part.strip()
        if "-" in part:
            start_s, end_s = part.split("-", 1)
            start = int(start_s) - 1
            end = int(end_s) - 1
            if start < 0 or end >= total_pages or start > end:
                raise ValueError(f"Invalid page range: {part} (total pages: {total_pages})")
            indices.update(range(start, end + 1))
        else:
            idx = int(part) - 1
            if idx < 0 or idx >= total_pages:
                raise ValueError(f"Invalid page number: {part} (total pages: {total_pages})")
            indices.add(idx)
    return indices


# ==========================================
# 1. リサイズ (Resize)
# ==========================================
def resize_pdf(input_file, output_file, scale=None, paper_size=None, landscape=False):
    pages = _read_pages(input_file)
    processed = resize_pages(pages, scale=scale, paper_size=paper_size, landscape=landscape)
    _write_pages(processed, output_file)


def resize_pages(pages, scale=None, paper_size=None, landscape=False):
    if scale is None and paper_size is None:
        raise ValueError("Specify either 'scale' or 'paper_size'.")

    result = []
    for orig_page in pages:
        page = copy.deepcopy(orig_page)

        if scale is not None:
            page.scale_by(scale)
            result.append(page)
        elif paper_size is not None:
            target_w, target_h = PAPER_SIZES[paper_size.lower()]
            if landscape:
                target_w, target_h = target_h, target_w

            orig_w = float(page.mediabox.width)
            orig_h = float(page.mediabox.height)

            ratio = min(target_w / orig_w, target_h / orig_h)
            new_sheet = PageObject.create_blank_page(width=target_w, height=target_h)

            tx = (target_w - orig_w * ratio) / 2
            ty = (target_h - orig_h * ratio) / 2

            new_sheet.merge_transformed_page(
                page,
                Transformation().scale(sx=ratio, sy=ratio).translate(tx=tx, ty=ty),
            )
            result.append(new_sheet)

    return result


# ==========================================
# 2. 分割 (Split)
# ==========================================
def split_pdf(input_file, output_file, right_to_left=False):
    pages = _read_pages(input_file)
    processed = split_pages(pages, right_to_left=right_to_left)
    _write_pages(processed, output_file)


def split_pages(pages, right_to_left=False):
    result = []

    for orig_page in pages:
        page = copy.deepcopy(orig_page)

        width = float(page.mediabox.width)
        height = float(page.mediabox.height)

        if width > height:
            half_width = width / 2

            left_page = copy.deepcopy(page)
            left_page.mediabox.upper_right = (half_width, height)
            left_page.cropbox.upper_right = (half_width, height)

            right_page = copy.deepcopy(page)
            right_page.add_transformation(
                Transformation().translate(tx=-half_width, ty=0)
            )
            right_page.mediabox.lower_left = (0, 0)
            right_page.mediabox.upper_right = (half_width, height)
            right_page.cropbox.lower_left = (0, 0)
            right_page.cropbox.upper_right = (half_width, height)

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

            bottom_page = copy.deepcopy(page)
            bottom_page.mediabox.upper_right = (width, half_height)
            bottom_page.cropbox.upper_right = (width, half_height)

            result.extend([top_page, bottom_page])

    return result


# ==========================================
# 3. 並び変え (Reorder)
# ==========================================
def reorder_pdf(
    input_file,
    output_file,
    pad_mode="back",
    right_to_left=False,
    sheets_per_signature=None,
):
    pages = _read_pages(input_file)
    width = float(pages[0].mediabox.width)
    height = float(pages[0].mediabox.height)
    blank = PageObject.create_blank_page(width=width, height=height)

    reordered = reorder_in_booklet_order(
        pages,
        blank,
        pad_mode=pad_mode,
        right_to_left=right_to_left,
        sheets_per_signature=sheets_per_signature,
    )
    _write_pages(reordered, output_file)


def reorder_in_booklet_order(
    pages,
    padding,
    pad_mode="back",
    right_to_left=False,
    sheets_per_signature=None,
):
    pages = list(pages)
    add_padding(pages, padding, mode=pad_mode)

    chunk_size = sheets_per_signature * 4 if sheets_per_signature else len(pages)

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
    else:
        front_pads = 0
        back_pads = pad_count

    pages[:] = ([padding] * front_pads) + pages + ([padding] * back_pads)


# ==========================================
# 4. 統合 (Impose / Merge)
# ==========================================
def impose_2up_pdf(input_file, output_file):
    pages = _read_pages(input_file)
    orig_width = float(pages[0].mediabox.width)
    orig_height = float(pages[0].mediabox.height)

    imposed = impose_2up_landscape(pages, orig_width, orig_height)
    _write_pages(imposed, output_file)


def impose_2up_landscape(pages, orig_width, orig_height):
    sheet_width = orig_height
    sheet_height = orig_width
    scale = 1 / (2**0.5)
    half_sheet_width = sheet_width / 2

    imposed_sheets = []

    for i in range(0, len(pages), 2):
        sheet = PageObject.create_blank_page(
            width=sheet_width, height=sheet_height
        )

        left = copy.deepcopy(pages[i])
        sheet.merge_transformed_page(
            left,
            Transformation().scale(sx=scale, sy=scale).translate(tx=0, ty=0),
        )

        if i + 1 < len(pages):
            right = copy.deepcopy(pages[i + 1])
            sheet.merge_transformed_page(
                right,
                Transformation()
                .scale(sx=scale, sy=scale)
                .translate(tx=half_sheet_width, ty=0),
            )

        imposed_sheets.append(sheet)

    return imposed_sheets


def concat_pdfs(input_files, output_file):
    writer = PdfWriter()
    for path in input_files:
        reader = PdfReader(path)
        for page in reader.pages:
            writer.add_page(page)
    with open(output_file, "wb") as f:
        writer.write(f)


# ==========================================
# 5. 回転 (Rotate)
# ==========================================
def rotate_pdf(input_file, output_file, angle, page_spec=None, bake=False):
    pages = _read_pages(input_file)
    target_indices = _parse_page_indices(page_spec, len(pages))
    processed = rotate_pages(pages, angle=angle, target_indices=target_indices, bake=bake)
    _write_pages(processed, output_file)


def rotate_pages(pages, angle, target_indices=None, bake=False):
    if angle % 90 != 0:
        raise ValueError("Rotation angle must be a multiple of 90.")

    result = []
    for idx, orig_page in enumerate(pages):
        page = copy.deepcopy(orig_page)
        if target_indices is None or idx in target_indices:
            if angle != 0:
                page.rotate(angle)
            if bake:
                page.transfer_rotation_to_content()
        result.append(page)

    return result