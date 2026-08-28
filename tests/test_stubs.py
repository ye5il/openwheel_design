"""Tests for fixed stub functions: parse_can_message, export_to_csv,
check_pedal_travel, and dynamic_rear warning in brake bias."""
import os
import struct
import tempfile
import warnings

import pytest


def test_parse_can_message_with_dbc():
    """parse_can_message with a dbc_entry decodes raw bytes correctly."""
    from openwheel_design.modules.data_log import parse_can_message

    # Encode RPM = 5000 as a 16-bit little-endian value at start_bit 0
    data = struct.pack('<H', 5000) + b'\x00' * 6

    dbc = {
        "signals": [
            {"name": "rpm", "start_bit": 0, "length": 16,
             "scale": 1, "offset": 0, "byte_order": "little_endian"},
        ]
    }
    result = parse_can_message(0x100, data, dbc_entry=dbc)
    assert result["signals"]["rpm"] == 5000


def test_parse_can_message_scale_offset():
    """parse_can_message applies scale and offset."""
    from openwheel_design.modules.data_log import parse_can_message

    # Raw value 200, scale 0.1, offset -10  =>  200*0.1 + (-10) = 10.0
    data = struct.pack('<H', 200) + b'\x00' * 6
    dbc = {
        "signals": [
            {"name": "temp", "start_bit": 0, "length": 16,
             "scale": 0.1, "offset": -10, "byte_order": "little_endian"},
        ]
    }
    result = parse_can_message(0x202, data, dbc_entry=dbc)
    assert result["signals"]["temp"] == pytest.approx(10.0)


def test_parse_can_message_no_dbc():
    """Without dbc_entry, parse_can_message returns raw byte breakdown."""
    from openwheel_design.modules.data_log import parse_can_message

    data = bytes([0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08])
    result = parse_can_message(0x100, data)
    assert "raw_bytes" in result
    assert result["raw_bytes"] == [1, 2, 3, 4, 5, 6, 7, 8]
    assert result["name"] == "EngineRPM"


def test_parse_can_message_unknown_id():
    """Unknown msg_id without dbc returns raw bytes without name."""
    from openwheel_design.modules.data_log import parse_can_message

    data = b'\xff' * 8
    result = parse_can_message(0x999, data)
    assert "raw_bytes" in result
    assert "name" not in result


def test_export_to_csv_creates_file():
    """export_to_csv actually writes a CSV file."""
    from openwheel_design.modules.data_log import export_to_csv

    data = [
        {"time": 0.0, "rpm": 3000, "speed": 50},
        {"time": 0.1, "rpm": 3200, "speed": 55},
        {"time": 0.2, "rpm": 3400, "speed": 60},
    ]

    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        filepath = f.name

    try:
        result = export_to_csv(data, filepath)
        assert result["exported"] is True
        assert result["rows"] == 3
        assert result["filepath"] == filepath

        with open(filepath, 'r') as f:
            lines = f.readlines()
        # Header + 3 data rows
        assert len(lines) == 4
        assert "time" in lines[0]
        assert "rpm" in lines[0]
    finally:
        os.unlink(filepath)


def test_export_to_csv_no_leading_space_key():
    """The old ' exported' key with a leading space must not exist."""
    from openwheel_design.modules.data_log import export_to_csv

    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        filepath = f.name

    try:
        result = export_to_csv([{"a": 1}], filepath)
        assert " exported" not in result
        assert "exported" in result
    finally:
        os.unlink(filepath)


def test_export_to_csv_empty_data():
    """export_to_csv with empty data creates an empty file."""
    from openwheel_design.modules.data_log import export_to_csv

    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        filepath = f.name

    try:
        result = export_to_csv([], filepath)
        assert result["exported"] is True
        assert result["rows"] == 0
    finally:
        os.unlink(filepath)


def test_check_pedal_travel_varies_with_bore():
    """check_pedal_travel returns different results for different MC bore sizes."""
    from openwheel_design.modules.brakes import check_pedal_travel

    small = check_pedal_travel(mc_bore_mm=15.0)
    large = check_pedal_travel(mc_bore_mm=25.0)

    # Larger MC bore displaces more fluid per stroke -> less pedal travel needed
    assert small["pedal_travel_mm"] != large["pedal_travel_mm"]
    assert small["pedal_travel_mm"] > large["pedal_travel_mm"]


def test_check_pedal_travel_volume_check():
    """check_pedal_travel reports volume sufficiency correctly."""
    from openwheel_design.modules.brakes import check_pedal_travel

    # Generous MC: 25 mm bore, 30 mm stroke, small calipers
    result = check_pedal_travel(mc_bore_mm=25.0, mc_stroke_mm=30.0,
                                caliper_bore_mm=25.0, n_pistons=2,
                                n_calipers=4, pad_clearance_mm=0.1)
    assert result["volume_sufficient"] is True

    # Tiny MC: 10 mm bore, 10 mm stroke, big calipers
    result = check_pedal_travel(mc_bore_mm=10.0, mc_stroke_mm=10.0,
                                caliper_bore_mm=40.0, n_pistons=6,
                                n_calipers=4, pad_clearance_mm=0.3)
    assert result["volume_sufficient"] is False


def test_dynamic_rear_negative_warning():
    """calculate_brake_bias warns and adds 'warning' key when dynamic_rear < 0."""
    from openwheel_design.modules.brakes import calculate_brake_bias

    # Extreme deceleration: 3 g with high CoG should make rear go negative
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        result = calculate_brake_bias(
            front_weight_N=1500, rear_weight_N=1000,
            decel_g=3.0, cog_height_mm=400, wheelbase_mm=1550
        )
        assert result["dynamic_rear_N"] < 0
        assert "warning" in result
        assert len(w) == 1
        assert "negative" in str(w[0].message).lower()


def test_dynamic_rear_no_warning_normal():
    """calculate_brake_bias does not warn under normal deceleration."""
    from openwheel_design.modules.brakes import calculate_brake_bias

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        result = calculate_brake_bias(
            front_weight_N=1500, rear_weight_N=1000,
            decel_g=0.8, cog_height_mm=300, wheelbase_mm=1600
        )
        assert result["dynamic_rear_N"] > 0
        assert "warning" not in result
        assert len(w) == 0
