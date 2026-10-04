"""Deterministic UI checks for activity, filters, empty states and reduced motion.

uv run --with playwright==1.63.0 python tests/browser/insights.py --url URL
API fixtures are intercepted in the browser; no database writes.
"""

import argparse
from datetime import datetime, timedelta, timezone

from playwright.sync_api import expect, sync_playwright


def run(base_url):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(timezone_id="UTC")
        page = context.new_page()
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        now = datetime(2026, 9, 19, 12, tzinfo=timezone.utc)
        page.clock.set_fixed_time(now)
        runs = []
        for index, (age, status) in enumerate(
            [
                (0, "completed"),
                (0, "running"),
                (6, "completed"),
                (13, "failed"),
                (29, "cancelled"),
                (30, "waiting"),
                (None, "waiting"),
            ],
            start=1,
        ):
            runs.append(
                {
                    "id": index,
                    "project_id": 1,
                    "model_id": 1,
                    "dataset_id": 1,
                    "status": status,
                    "notes": "",
                    "is_ignored": False,
                    "start_time": (now - timedelta(days=age)).isoformat()
                    if age is not None
                    else None,
                }
            )
        fixtures = {
            "projects": [{"id": 1, "name": "UI fixture", "description": "Test only"}],
            "models": [{"id": 1, "name": "Model", "version": "1"}],
            "datasets": [{"id": 1, "name": "Dataset", "version": "1"}],
            "metric-directions": [],
            "runs": runs,
        }
        for resource in fixtures:
            page.route(
                f"**/{resource}/",
                lambda route: route.fulfill(
                    json=fixtures[route.request.url.rstrip("/").rsplit("/", 1)[-1]]
                ),
            )
        page.goto(base_url + "/ui/")
        expect(page.locator("#sync-status")).to_have_attribute("data-state", "success")
        expect(page.locator("#run-body tr")).to_have_count(7)
        expect(page.locator("#activity-total")).to_have_text("4")
        expect(page.locator("#completion-rate")).to_have_text("29%")
        for period, total in [(7, 3), (30, 5), (14, 4)]:
            page.locator(f'[data-period="{period}"]').click()
            expect(page.locator(".activity-bar")).to_have_count(period)
            expect(page.locator("#activity-total")).to_have_text(str(total))
        today = page.locator('[data-day="2026-09-19"]')
        today.focus()
        expect(page.locator("#activity-hover")).to_contain_text("2 runs started")
        page.keyboard.press("Enter")
        expect(page.locator("#run-body tr")).to_have_count(2)
        expect(today).to_have_attribute("aria-pressed", "true")
        page.locator('[data-status-filter="running"]').click()
        expect(page.locator("#run-body tr")).to_have_count(1)
        expect(page.locator("#status-filter")).to_have_value("running")
        page.locator('[data-status-filter="running"]').click()
        expect(page.locator("#run-body tr")).to_have_count(2)
        page.locator("#clear-day").click()
        expect(page.locator("#run-body tr")).to_have_count(7)
        page.locator('[data-day="2026-09-18"]').click()
        expect(page.locator("#table-state")).to_contain_text("No runs match")
        page.locator('[data-period="7"]').click()
        expect(page.locator("#day-filter")).not_to_be_visible()
        expect(page.locator("#run-body tr")).to_have_count(7)
        page.locator("#status-filter").select_option("failed")
        expect(page.locator('[data-status-filter="failed"]')).to_have_attribute(
            "aria-pressed", "true"
        )
        page.locator('[data-action="refresh-runs"]').click()
        expect(page.locator("#sync-status")).to_have_attribute("data-state", "success")
        expect(page.locator("#status-filter")).to_have_value("failed")
        expect(page.locator("#run-body tr")).to_have_count(1)
        for width in (320, 375, 414, 768, 1440):
            page.set_viewport_size({"width": width, "height": 1000})
            page.locator('[data-period="30"]').click()
            assert page.evaluate("document.body.scrollWidth <= innerWidth"), width
            assert page.evaluate(
                "document.documentElement.scrollWidth <= innerWidth"
            ), width
        page.emulate_media(reduced_motion="reduce")
        assert (
            page.locator(".activity-fill").first.evaluate(
                "el => getComputedStyle(el).animationName"
            )
            == "none"
        )
        # Empty workspace is honest: no invented percentage or runs.
        fixtures["runs"] = []
        page.reload()
        expect(page.locator("#sync-status")).to_have_attribute("data-state", "success")
        expect(page.locator("#activity-total")).to_have_text("0")
        expect(page.locator("#completion-rate")).to_have_text("—")
        expect(page.locator("#onboarding")).to_be_visible()
        expect(page.locator("#onboarding-action")).to_have_text("Register a metric")
        page.locator("#onboarding-action").click()
        registration = page.get_by_role("dialog", name="New metric direction")
        expect(registration.get_by_label("Direction", exact=True)).to_be_visible()
        page.keyboard.press("Escape")
        fixtures["metric-directions"] = [{"name": "loss", "maximize": False}]
        page.reload()
        expect(page.locator("#onboarding-action")).to_have_text("Log your first run")
        # Fonts and downloaded icon sprite are served without third-party requests.
        for asset in [
            "fonts/sora.ttf",
            "fonts/dm-sans.ttf",
            "fonts/ibm-plex-mono.ttf",
            "icons/sprite.svg",
            "icons/LICENSE.txt",
        ]:
            response = context.request.get(base_url + "/ui/static/" + asset)
            assert response.ok, asset
        assert not errors, errors
        browser.close()
        print(
            "Activity aggregation, date/status filtering, refresh preservation, "
            "keyboard activation, 30-day mobile layout, reduced motion, "
            "empty workspace and local assets passed."
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", required=True)
    run(parser.parse_args().url.rstrip("/"))
