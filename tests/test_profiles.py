"""Panel profile resolution."""

from custom_components.paperboard.profiles import names, resolve


def test_registry_loaded() -> None:
    assert len(names()) > 50 and "og_png" in names() and "v2" in names()


def test_owner_device_alias() -> None:
    p = resolve("xiao_epaper_display", 800, 480)
    assert (p.width, p.height, p.bit_depth, p.byte_limit) == (800, 480, 1, 90_000)


def test_known_model_and_depth_cap() -> None:
    x = resolve("v2")
    assert (x.width, x.height, x.scale_factor) == (1872, 1404, 1.8)
    assert x.bit_depth == 4
    assert resolve("amazon_kindle_7").bit_depth == 4  # 8-bit panels get 16 greys
    assert resolve("og_plus").bit_depth == 2


def test_fallbacks() -> None:
    assert resolve("unknown_thing", 800, 480).model == "og_png"
    assert resolve("unknown_thing", 1448, 1072).model == "amazon_kindle_paperwhite_7th_gen" \
        or resolve("unknown_thing", 1448, 1072).width == 1448
    assert resolve(None).model == "og_png"
