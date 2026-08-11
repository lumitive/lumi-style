"""Tests for sea_route.py's pure core — the 425-line router 0.1.415 shipped
with no coverage at all (it was not even in the old py_compile list).

The expensive parts (mask rasterization, real-world routing) stay untested
here: CI's build_geography/build_trade_registry checks own the shipped
artifacts. What is tested is the grid geometry and the pathfinder, on a
synthetic all-water world small enough to run in milliseconds.
"""
import math

import pytest
import sea_route


def test_cell_lonlat_roundtrip_within_half_cell():
    for lon, lat in ((0.0, 0.0), (-179.9, -89.9), (179.9, 89.9),
                     (103.8, 1.35), (-70.0, -33.0)):
        j, i = sea_route._cell(lon, lat)
        lon2, lat2 = sea_route._lonlat(j, i)
        cell = 1.0 / sea_route.RES
        assert abs(lat2 - lat) <= cell
        # longitude wraps
        dlon = abs((lon2 - lon + 180) % 360 - 180)
        assert dlon <= cell


def test_cell_clamps_poles_and_wraps_longitude():
    j, _ = sea_route._cell(0.0, 90.0)
    assert j == sea_route.NY - 1
    _, i_a = sea_route._cell(-180.0, 0.0)
    _, i_b = sea_route._cell(180.0, 0.0)
    assert i_a == i_b  # the seam is one column, not two


def test_hav_zero_and_quarter_turn():
    assert sea_route._hav((0.0, 0.0), (0.0, 0.0)) == 0.0
    assert sea_route._hav((0.0, 0.0), (90.0, 0.0)) == pytest.approx(math.pi / 2)
    # symmetric
    a, b = (12.0, 34.0), (-56.0, 7.0)
    assert sea_route._hav(a, b) == pytest.approx(sea_route._hav(b, a))


def test_great_circle_endpoints_and_count():
    pts = sea_route._great_circle((0.0, 0.0), (90.0, 0.0), 10)
    assert len(pts) == 11
    assert pts[0] == pytest.approx((0.0, 0.0))
    assert pts[-1][0] == pytest.approx(90.0)


def _water_world():
    """An all-water planet: every cell navigable, zero coast cost."""
    sea = bytearray([1]) * (sea_route.NX * sea_route.NY)
    cost = bytearray(sea_route.NX * sea_route.NY)
    return sea, cost


def test_dijkstra_open_water_path_is_connected():
    sea, cost = _water_world()
    start = sea_route._cell(0.0, 0.0)
    goal = sea_route._cell(4.0, 3.0)
    path = sea_route.dijkstra(sea, cost, start, goal)
    assert path is not None
    assert path[0] == start and path[-1] == goal
    for (j1, i1), (j2, i2) in zip(path, path[1:]):
        assert abs(j1 - j2) <= 1
        assert min(abs(i1 - i2), sea_route.NX - abs(i1 - i2)) <= 1


def test_dijkstra_blocked_goal_returns_none():
    sea, cost = _water_world()
    goal = sea_route._cell(4.0, 3.0)
    gj, gi = goal
    # wall the goal cell in: it exists but nothing reaches it
    for dj in (-1, 0, 1):
        for di in (-1, 0, 1):
            if dj or di:
                sea[(gj + dj) * sea_route.NX + (gi + di) % sea_route.NX] = 0
    start = sea_route._cell(0.0, 0.0)
    assert sea_route.dijkstra(sea, cost, start, goal) is None


def test_on_water_reads_the_mask():
    sea, _ = _water_world()
    assert sea_route.on_water(sea, 0.0, 0.0)
    j, i = sea_route._cell(0.0, 0.0)
    sea[j * sea_route.NX + i] = 0
    assert not sea_route.on_water(sea, 0.0, 0.0)
