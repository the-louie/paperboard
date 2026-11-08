"""Layout validation errors name the exact path, with probatio and voluptuous."""

import pytest
import voluptuous

from custom_components.paperboard.schema import format_errors, vol


@pytest.mark.parametrize("lib", [vol, voluptuous])
def test_error_paths(lib) -> None:
    schema = lib.Schema({lib.Required("widgets"): [{lib.Required("type"): str,
                                                    lib.Required("area"): str}]})
    with pytest.raises(lib.Invalid) as info:
        schema({"widgets": [{"type": "now", "area": "a"}, {"type": "x", "area": 5}]})
    assert format_errors(info.value) == ["widgets[1].area: expected str"]
