
from pyweaving import Color, BLACK, WHITE, MID


def test_colors():
    # Test creation
    colors = [Color([0, 128, 255]),
              Color()]
    # test creation from existing color
    colors.append(Color(colors[0]))
    colors.append(Color(colors[0], True))
    colors.append(MID)

    # intensity of MID
    assert(int(colors[-1].intensity*100) / 100 == 0.47)

    for col in colors:
        print(col, col.rgb, col.hsl, col.css, col.hex, col.highlight, col.shadow)

