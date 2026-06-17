import pytest
from datetime import datetime, timedelta
from genetic_algorithm import bundle_packages
from package import Package

BASE = datetime(2025, 1, 1, 8, 0)  # 8:00 AM baseline

def make_package(pid, address, deadline=None, delay=None, weight=1, refrigerated=False):
    return Package(pid, address, deadline, weight, "", refrigerated, delay_time=delay)


class TestBundleSeparation:
    def test_different_addresses_are_separate_bundles(self):
        packages = {
            1: make_package(1, "123 Main St"),
            2: make_package(2, "456 Oak Ave"),
        }
        bundles = bundle_packages(packages)
        addresses = {b["address"] for b in bundles.values()}
        assert len(bundles) == 2
        assert "123 Main St" in addresses
        assert "456 Oak Ave" in addresses

    def test_compatible_packages_share_a_bundle(self):
        packages = {
            1: make_package(1, "123 Main St"),
            2: make_package(2, "123 Main St"),
        }
        bundles = bundle_packages(packages)
        assert len(bundles) == 1
        bundle = list(bundles.values())[0]
        assert set(bundle["package_ids"]) == {1, 2}

    def test_delay_plus_buffer_exceeds_deadline_splits_bundle(self):
        # delay 9:20 + 45min buffer = 10:05, which exceeds deadline 10:00
        deadline = BASE.replace(hour=10, minute=0)
        delay    = BASE.replace(hour=9,  minute=20)
        packages = {
            1: make_package(1, "123 Main St", deadline=deadline),
            2: make_package(2, "123 Main St", delay=delay),
        }
        bundles = bundle_packages(packages)
        assert len(bundles) == 2

    def test_delay_plus_buffer_within_deadline_allows_bundle(self):
        # delay 9:00 + 45min buffer = 9:45, which is before deadline 10:00
        deadline = BASE.replace(hour=10, minute=0)
        delay    = BASE.replace(hour=9,  minute=0)
        packages = {
            1: make_package(1, "123 Main St", deadline=deadline),
            2: make_package(2, "123 Main St", delay=delay),
        }
        bundles = bundle_packages(packages)
        assert len(bundles) == 1

    def test_deadline_before_existing_delay_splits_bundle(self):
        # deadline 9:00 is before existing delay 10:00 — impossible to satisfy both
        delay    = BASE.replace(hour=10, minute=0)
        deadline = BASE.replace(hour=9,  minute=0)
        packages = {
            1: make_package(1, "123 Main St", delay=delay),
            2: make_package(2, "123 Main St", deadline=deadline),
        }
        bundles = bundle_packages(packages)
        assert len(bundles) == 2

    def test_buffer_boundary_exact_match_splits_bundle(self):
        # delay + buffer == deadline exactly: 9:15 + 45min = 10:00 == 10:00
        # condition is strictly greater-than, so this should NOT split
        deadline = BASE.replace(hour=10, minute=0)
        delay    = BASE.replace(hour=9,  minute=15)
        packages = {
            1: make_package(1, "123 Main St", deadline=deadline),
            2: make_package(2, "123 Main St", delay=delay),
        }
        bundles = bundle_packages(packages)
        assert len(bundles) == 1

    def test_no_constraints_bundles_freely(self):
        packages = {i: make_package(i, "123 Main St") for i in range(5)}
        bundles = bundle_packages(packages)
        assert len(bundles) == 1
        assert len(list(bundles.values())[0]["package_ids"]) == 5


class TestBundleProperties:
    def test_bundle_uses_tightest_deadline(self):
        early = BASE.replace(hour=9,  minute=0)
        late  = BASE.replace(hour=11, minute=0)
        packages = {
            1: make_package(1, "123 Main St", deadline=early),
            2: make_package(2, "123 Main St", deadline=late),
        }
        bundles = bundle_packages(packages)
        assert len(bundles) == 1
        assert list(bundles.values())[0]["deadline"] == early

    def test_bundle_uses_latest_delay(self):
        delay_a = BASE.replace(hour=9,  minute=0)
        delay_b = BASE.replace(hour=10, minute=0)
        packages = {
            1: make_package(1, "123 Main St", delay=delay_a),
            2: make_package(2, "123 Main St", delay=delay_b),
        }
        bundles = bundle_packages(packages)
        assert len(bundles) == 1
        assert list(bundles.values())[0]["delay_time"] == delay_b

    def test_bundle_weight_is_summed(self):
        packages = {
            1: make_package(1, "123 Main St", weight=4),
            2: make_package(2, "123 Main St", weight=7),
        }
        bundles = bundle_packages(packages)
        assert list(bundles.values())[0]["total_weight"] == 11

    def test_bundle_refrigerated_if_any_package_requires_it(self):
        packages = {
            1: make_package(1, "123 Main St", refrigerated=False),
            2: make_package(2, "123 Main St", refrigerated=True),
        }
        bundles = bundle_packages(packages)
        assert list(bundles.values())[0]["refrigerated"] is True

    def test_bundle_not_refrigerated_if_no_package_requires_it(self):
        packages = {
            1: make_package(1, "123 Main St", refrigerated=False),
            2: make_package(2, "123 Main St", refrigerated=False),
        }
        bundles = bundle_packages(packages)
        assert list(bundles.values())[0]["refrigerated"] is False
