import math
import os

from PIL import Image

import re


def generate_gestalt_image(directory: str, name: str):
    all_images = [f for f in os.listdir(directory) if re.match(r'.*.jpg', f)]
    all_images.sort()
    images = [Image.open(f'{directory}/{x}') for x in all_images]
    widths, heights = zip(*(i.size for i in images))

    widest_width = max(widths)
    tallest_height = max(heights)
    grid_area = widest_width * tallest_height * len(images)
    perfect_square_side = math.sqrt(grid_area)

    smallest_diff = None
    best_column_count = None
    this_grid_number_of_columns = 0

    for i in images:
        this_grid_number_of_columns += 1
        this_grid_number_of_rows = int(
            math.ceil(len(images) / this_grid_number_of_columns))
        # Get this grid's difference from the perfect square width:
        this_grid_width = widest_width * this_grid_number_of_columns
        x_diff = abs(perfect_square_side - this_grid_width)
        # Get this grid's difference from the perfect square height:
        this_grid_height = tallest_height * this_grid_number_of_rows
        y_diff = abs(perfect_square_side - this_grid_height)
        diff = x_diff + y_diff
        # Test to see if this is the best candidate so far
        if best_column_count is not None:
            if diff <= smallest_diff:
                smallest_diff = diff
                best_column_count = this_grid_number_of_columns
        else:
            smallest_diff = diff
            best_column_count = this_grid_number_of_columns

    total_width = 24 + (widest_width + 24) * best_column_count
    max_height = 24 + (tallest_height + 24) * int(
        math.ceil(len(images) / best_column_count))
    new_im = Image.new('RGB', (total_width, max_height))
    x_offset = 24
    y_offset = 24
    col_count = 0
    for im in images:
        new_im.paste(im, (x_offset, y_offset))
        x_offset += widest_width + 24
        col_count += 1
        if col_count == best_column_count:
            x_offset = 24
            y_offset += tallest_height + 24
            col_count = 0

    count = 0
    filename = f'{name}.jpg'
    while True:
        if os.path.exists(f'./images/{filename}'):
            count += 1
            filename = f'{name} {count}.jpg'
        else:
            break
    new_im.save(f'./images/{filename}')
