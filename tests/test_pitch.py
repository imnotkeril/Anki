import pytest

from jpvocab.pitch import render_pitch_svg


def test_heiban_sore():
    svg = render_pitch_svg(morae=["そ", "れ"], accent=0)
    assert svg == (
        '<svg class="pitch" height="75px" viewbox="0 0 102 75" width="102px">'
        '<text style="font-size:20px;font-family:sans-serif;fill:#000;" x="5" y="67.5">そ</text>'
        '<text style="font-size:20px;font-family:sans-serif;fill:#000;" x="40" y="67.5">れ</text>'
        '<path d="m 16,30 35,-25" style="fill:none;stroke:#000;stroke-width:1.5;"></path>'
        '<path d="m 51,5 35,0" style="fill:none;stroke:#000;stroke-width:1.5;"></path>'
        '<circle cx="16" cy="30" r="5" style="opacity:1;fill:#000;"></circle>'
        '<circle cx="51" cy="5" r="5" style="opacity:1;fill:#000;"></circle>'
        '<circle cx="86" cy="5" r="5" style="opacity:1;fill:#000;"></circle>'
        '<circle cx="86" cy="5" r="3.25" style="opacity:1;fill:#fff;"></circle>'
        '</svg>'
    )


def test_atamadaka_ni():
    svg = render_pitch_svg(morae=["に"], accent=1)
    assert svg == (
        '<svg class="pitch" height="75px" viewbox="0 0 67 75" width="67px">'
        '<text style="font-size:20px;font-family:sans-serif;fill:#000;" x="5" y="67.5">に</text>'
        '<path d="m 16,5 35,25" style="fill:none;stroke:#000;stroke-width:1.5;"></path>'
        '<circle cx="16" cy="5" r="5" style="opacity:1;fill:#000;"></circle>'
        '<circle cx="51" cy="30" r="5" style="opacity:1;fill:#000;"></circle>'
        '<circle cx="51" cy="30" r="3.25" style="opacity:1;fill:#fff;"></circle>'
        '</svg>'
    )


def test_odaka_ichi():
    svg = render_pitch_svg(morae=["い", "ち"], accent=2)
    assert svg == (
        '<svg class="pitch" height="75px" viewbox="0 0 102 75" width="102px">'
        '<text style="font-size:20px;font-family:sans-serif;fill:#000;" x="5" y="67.5">い</text>'
        '<text style="font-size:20px;font-family:sans-serif;fill:#000;" x="40" y="67.5">ち</text>'
        '<path d="m 16,30 35,-25" style="fill:none;stroke:#000;stroke-width:1.5;"></path>'
        '<path d="m 51,5 35,25" style="fill:none;stroke:#000;stroke-width:1.5;"></path>'
        '<circle cx="16" cy="30" r="5" style="opacity:1;fill:#000;"></circle>'
        '<circle cx="51" cy="5" r="5" style="opacity:1;fill:#000;"></circle>'
        '<circle cx="86" cy="30" r="5" style="opacity:1;fill:#000;"></circle>'
        '<circle cx="86" cy="30" r="3.25" style="opacity:1;fill:#fff;"></circle>'
        '</svg>'
    )


def test_nakadaka_nichiyoubi():
    svg = render_pitch_svg(morae=["に", "ち", "よ", "う", "び"], accent=3)
    assert svg == (
        '<svg class="pitch" height="75px" viewbox="0 0 207 75" width="207px">'
        '<text style="font-size:20px;font-family:sans-serif;fill:#000;" x="5" y="67.5">に</text>'
        '<text style="font-size:20px;font-family:sans-serif;fill:#000;" x="40" y="67.5">ち</text>'
        '<text style="font-size:20px;font-family:sans-serif;fill:#000;" x="75" y="67.5">よ</text>'
        '<text style="font-size:20px;font-family:sans-serif;fill:#000;" x="110" y="67.5">う</text>'
        '<text style="font-size:20px;font-family:sans-serif;fill:#000;" x="145" y="67.5">び</text>'
        '<path d="m 16,30 35,-25" style="fill:none;stroke:#000;stroke-width:1.5;"></path>'
        '<path d="m 51,5 35,0" style="fill:none;stroke:#000;stroke-width:1.5;"></path>'
        '<path d="m 86,5 35,25" style="fill:none;stroke:#000;stroke-width:1.5;"></path>'
        '<path d="m 121,30 35,0" style="fill:none;stroke:#000;stroke-width:1.5;"></path>'
        '<path d="m 156,30 35,0" style="fill:none;stroke:#000;stroke-width:1.5;"></path>'
        '<circle cx="16" cy="30" r="5" style="opacity:1;fill:#000;"></circle>'
        '<circle cx="51" cy="5" r="5" style="opacity:1;fill:#000;"></circle>'
        '<circle cx="86" cy="5" r="5" style="opacity:1;fill:#000;"></circle>'
        '<circle cx="121" cy="30" r="5" style="opacity:1;fill:#000;"></circle>'
        '<circle cx="156" cy="30" r="5" style="opacity:1;fill:#000;"></circle>'
        '<circle cx="191" cy="30" r="5" style="opacity:1;fill:#000;"></circle>'
        '<circle cx="191" cy="30" r="3.25" style="opacity:1;fill:#fff;"></circle>'
        '</svg>'
    )


def test_out_of_range_accent_raises():
    with pytest.raises(ValueError):
        render_pitch_svg(morae=["に"], accent=5)
