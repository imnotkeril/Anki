from beartype import beartype


def _dot_high(mora_index_from_1: int | None, accent: int) -> bool:
    """mora_index_from_1 is None for the trailing particle dot."""
    if mora_index_from_1 is None:
        return accent == 0
    if accent == 0:
        return mora_index_from_1 >= 2
    if accent == 1:
        return mora_index_from_1 == 1
    return 2 <= mora_index_from_1 <= accent


@beartype
def render_pitch_svg(morae: list[str], accent: int) -> str:
    n = len(morae)
    width = 32 + 35 * n

    texts = "".join(
        f'<text style="font-size:20px;font-family:sans-serif;fill:#000;" '
        f'x="{5 + 35 * i}" y="67.5">{mora}</text>'
        for i, mora in enumerate(morae)
    )

    dot_y = [5 if _dot_high(j + 1 if j < n else None, accent) else 30 for j in range(n + 1)]
    dot_x = [16 + 35 * j for j in range(n + 1)]

    paths = "".join(
        f'<path d="m {dot_x[k]},{dot_y[k]} 35,{dot_y[k + 1] - dot_y[k]}" '
        f'style="fill:none;stroke:#000;stroke-width:1.5;"></path>'
        for k in range(n)
    )

    circles = "".join(
        f'<circle cx="{dot_x[j]}" cy="{dot_y[j]}" r="5" style="opacity:1;fill:#000;"></circle>'
        for j in range(n + 1)
    )
    circles += (
        f'<circle cx="{dot_x[n]}" cy="{dot_y[n]}" r="3.25" '
        f'style="opacity:1;fill:#fff;"></circle>'
    )

    return (
        f'<svg class="pitch" height="75px" viewbox="0 0 {width} 75" width="{width}px">'
        f'{texts}{paths}{circles}</svg>'
    )
