from pypdf import PdfReader, PdfWriter
from pypdf import PageObject
import copy

def compile_booklet_order(input_file, output_file):
    reader = PdfReader(input_file)
    pages = list(reader.pages)

    width = reader.pages[0].mediabox.width
    height = reader.pages[0].mediabox.height
    blank = PageObject.create_blank_page(width=width, height=height)

    reordered = reorder_in_booklet_order(pages, blank)

    writer = PdfWriter()
    for page in reordered:
        writer.add_page(page)
 
    with open(output_file, "wb") as f:
        writer.write(f)

def reorder_in_booklet_order(pages, padding):
    pages = list(pages)
    add_padding(pages, padding)
    reordered = []
    page_count = len(pages)
    
    for i in range(int(page_count / 4)):
        p1 = page_count - 1 - (i * 2)
        p2 = 0 + (i * 2)
        p3 = 1 + (i * 2)
        p4 = page_count - 2 - (i * 2)

        reordered.append(pages[p1])
        reordered.append(pages[p2])
        reordered.append(pages[p3])
        reordered.append(pages[p4])

    return reordered

def add_padding(pages, padding):
    while len(pages) % 4 != 0:
        pages.append(padding)
