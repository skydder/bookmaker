from pypdf import PdfReader, PdfWriter
from pypdf import PageObject

def compile_booklet_order(input_file, output_file):
    reader = PdfReader(input_file)
    writer = PdfWriter()

    pages = list(reader.pages)
    total_pages = len(pages)

    while len(pages) % 4 != 0:
        width = reader.pages[0].mediabox.width
        height = reader.pages[0].mediabox.height
        blank = PageObject.create_blank_page(width=width, height=height)
        pages.append(blank)

    total_pages = len(pages)

    for i in range(int(total_pages / 4)):
        p1 = total_pages - 1 - (i * 2)
        p2 = 0 + (i * 2)
        p3 = 1 + (i * 2)
        p4 = total_pages - 2 - (i * 2)

        writer.add_page(pages[p1])
        writer.add_page(pages[p2])
        writer.add_page(pages[p3])
        writer.add_page(pages[p4])

    with open(output_file, "wb") as f:
        writer.write(f)
