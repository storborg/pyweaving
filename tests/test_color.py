
from pyweaving import Color, BLACK, WHITE, MID


def test_colors():
    # Test creation
    colors = [Color([30,40,50]),
              Color()]
    # test creation from existing color
    colors.append(Color(colors[0]))
    colors.append(Color(colors[0], True))

    for col in colors:
        print(col, col.rgb, col.hsl, col.css, col.hex, col.highlight, col.shadow)

