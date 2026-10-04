"""Browser regression checks against a disposable running SentinelML instance.

uv run --with playwright==1.63.0 python tests/browser/smoke.py --url URL
Creates synthetic records; never point this at a production database.
"""

import argparse
import csv
import io
import json
import re
from uuid import uuid4

from playwright.sync_api import expect, sync_playwright


def run(base_url):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 1000})
        page = context.new_page()
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        suffix = uuid4().hex[:8]

        def create(path, data):
            response = context.request.post(base_url + path, data=data)
            assert response.status == 201, response.text()
            return response.json()

        dataset = create(
            "/datasets/", {"name": f"browser-data-{suffix}", "version": "1"}
        )
        model = create("/models/", {"name": f"browser-model-{suffix}", "version": "1"})
        metric_name = f"browser-loss-{suffix}"
        page.goto(base_url + "/ui/")
        expect(page.locator("#sum-total")).not_to_have_text("—")
        expect(page.locator("#sync-status")).to_have_attribute("data-state", "success")

        # Create via UI, including characters that must never be rendered as HTML.
        project_name = f"browser-{suffix} <script>"
        page.get_by_role("button", name="Create project", exact=True).click()
        dialog = page.get_by_role("dialog", name="New project", exact=True)
        dialog.get_by_label("Name", exact=True).fill(project_name)
        dialog.get_by_label("Description").fill("Synthetic browser verification")
        with page.expect_response(
            lambda r: r.url.endswith("/projects/") and r.request.method == "POST"
        ) as created:
            dialog.get_by_role("button", name="Create", exact=True).click()
        project_id = created.value.json()["id"]
        expect(dialog).not_to_be_visible()
        expect(
            page.locator("#project-filter option", has_text=project_name)
        ).to_have_count(1)

        # Register a run using the actual form, then exercise lifecycle guardrails.
        page.get_by_role("button", name=re.compile("^New run")).click()
        dialog = page.get_by_role("dialog", name="Log a new run")
        dialog.get_by_label("Project", exact=True).select_option(str(project_id))
        dialog.get_by_label("Dataset", exact=True).select_option(str(dataset["id"]))
        dialog.get_by_label("Model", exact=True).select_option(str(model["id"]))
        notes = '=HYPERLINK("https://example.test")\rSynthetic browser record'
        dialog.get_by_label("Notes").fill(notes)
        with page.expect_response(
            lambda r: r.url.endswith("/runs/") and r.request.method == "POST"
        ) as created:
            dialog.get_by_role("button", name="Log run", exact=True).click()
        run_id = created.value.json()["id"]
        expect(dialog).not_to_be_visible()
        page.get_by_role("button", name=f"run-{run_id}", exact=True).click()
        page.get_by_role("button", name="Start run", exact=True).click()
        expect(page.locator("#detail-state")).to_contain_text("parameter")
        page.get_by_label("parameter name", exact=True).fill("learning_rate")
        page.get_by_label("parameter value", exact=True).fill("0.001")
        page.locator(".inline-form").get_by_role(
            "button", name="Add", exact=True
        ).click()
        expect(page.locator("#detail-content")).to_contain_text("learning_rate")
        # Correct parameters without creating a duplicate, including error recovery.
        draft = (notes + "\nUnsaved draft").replace("\r", "\n")
        page.get_by_label("Run notes", exact=True).fill(draft)
        page.get_by_role("button", name="Catalog", exact=True).click()
        page.get_by_role("button", name="Experiments", exact=True).click()
        page.get_by_role("button", name=f"run-{run_id}", exact=True).click()
        expect(page.get_by_label("Run notes", exact=True)).to_have_value(draft)
        edit = page.get_by_role(
            "button", name="Edit parameter learning_rate", exact=True
        )
        edit.click()
        page.get_by_label("parameter value", exact=True).fill("0.002")
        page.route(
            "**/parameters/*",
            lambda route: (
                route.fulfill(status=503, json={"detail": "Synthetic edit failure"})
                if route.request.method == "PATCH"
                else route.continue_()
            ),
        )
        page.locator(".inline-form").get_by_role(
            "button", name="Save", exact=True
        ).click()
        expect(page.locator(".inline-error")).to_contain_text("Synthetic edit failure")
        expect(page.get_by_label("parameter value", exact=True)).to_have_value("0.002")
        page.unroute("**/parameters/*")
        page.locator(".inline-form").get_by_role(
            "button", name="Save", exact=True
        ).click()
        expect(page.locator("#detail-content .value")).to_have_text("0.002")
        expect(page.get_by_label("Run notes", exact=True)).to_have_value(draft)
        edit.click()
        page.get_by_label("parameter value", exact=True).fill("wrong")
        page.get_by_role("button", name="Cancel edit", exact=True).click()
        expect(page.locator("#detail-content .value")).to_have_text("0.002")
        page.get_by_role("button", name="Start run", exact=True).click()
        expect(page.get_by_role("button", name="Complete", exact=True)).to_be_visible()
        expect(page.get_by_label("Run notes", exact=True)).to_have_value(draft)
        expect(
            page.get_by_role("button", name="Edit parameter learning_rate", exact=True)
        ).to_have_count(0)
        # Register a result from the run, without losing the notes draft.
        page.get_by_role("button", name="Register a metric", exact=True).click()
        registration = page.get_by_role("dialog", name="New metric direction")
        registration.get_by_label("Metric name").fill(metric_name)
        registration.get_by_label("Direction", exact=True).select_option("false")
        registration.get_by_role("button", name="Create", exact=True).click()
        expect(registration).not_to_be_visible()
        expect(
            page.locator(f'#registered-metrics option[value="{metric_name}"]')
        ).to_have_count(1)
        expect(page.get_by_label("Run notes", exact=True)).to_have_value(draft)
        expect(page.get_by_label("parameter name", exact=True)).to_have_count(0)
        page.get_by_label("metric name", exact=True).fill(metric_name)
        page.get_by_label("metric value", exact=True).fill("-0.25")
        page.locator(".inline-form").get_by_role(
            "button", name="Add", exact=True
        ).click()
        expect(page.locator("#detail-content")).to_contain_text("-0.25")
        page.get_by_role(
            "button", name=f"Edit metric {metric_name}", exact=True
        ).click()
        page.get_by_label("metric value", exact=True).fill("-0.5")
        page.locator(".inline-form").get_by_role(
            "button", name="Save", exact=True
        ).click()
        expect(page.locator("#detail-content")).to_contain_text("-0.500000")
        metric_path = base_url + f"/runs/{run_id}/metrics/"
        recorded = context.request.get(metric_path).json()
        assert len(recorded) == 1 and recorded[0]["value"] == -0.5
        page.get_by_role(
            "button", name=f"Edit metric {metric_name}", exact=True
        ).click()
        page.get_by_label("metric value", exact=True).fill("-0.25")
        page.locator(".inline-form").get_by_role(
            "button", name="Save", exact=True
        ).click()
        expect(page.locator("#detail-content")).to_contain_text("-0.250000")
        # Dirty drafts warn on reload; declining keeps the current run and draft.
        with page.expect_event("dialog") as unload:
            page.evaluate("setTimeout(() => location.reload(), 0)")
        assert unload.value.type == "beforeunload"
        unload.value.dismiss()
        expect(page.get_by_label("Run notes", exact=True)).to_have_value(draft)
        page.set_viewport_size({"width": 320, "height": 960})
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
        page.set_viewport_size({"width": 1440, "height": 1000})
        page.get_by_role("button", name="Complete", exact=True).click()
        expect(page.locator("#detail-content .status")).to_have_text("completed")
        expect(page.get_by_label("metric name", exact=True)).to_have_count(0)
        expect(
            page.get_by_role("button", name=f"Edit metric {metric_name}", exact=True)
        ).to_have_count(0)
        expect(page.get_by_label("Run notes", exact=True)).to_have_value(draft)
        page.get_by_label("Run notes", exact=True).fill(notes + "\nReviewed")
        page.get_by_role("button", name="Save notes", exact=True).click()
        expect(page.locator(".notes-form")).to_contain_text("Notes saved.")
        page.get_by_role("button", name="Ignore", exact=True).click()
        action_dialog = page.get_by_role("dialog", name="Ignore run", exact=True)
        action_dialog.get_by_label("Ignore reason").fill("Synthetic review")
        action_dialog.get_by_role("button", name="Confirm", exact=True).click()
        expect(page.get_by_role("button", name="Unignore", exact=True)).to_be_visible()
        page.get_by_role("button", name="Unignore", exact=True).click()
        expect(page.get_by_role("button", name="Ignore", exact=True)).to_be_visible()

        second = create(
            "/runs/",
            {
                "project_id": project_id,
                "dataset_id": dataset["id"],
                "model_id": model["id"],
            },
        )
        page.reload()
        expect(page.locator("#sum-total")).not_to_have_text("—")
        expect(page.locator("#sync-status")).to_have_attribute("data-state", "success")
        page.get_by_label("Filter by project").select_option(str(project_id))
        expect(page.locator("#run-body tr")).to_have_count(2)
        # Newest-first order and toggled numeric sort.
        expect(page.locator("#run-body .run-link").first).to_have_text(
            f"run-{second['id']}"
        )
        page.locator('[data-sort="id"]').click()
        expect(page.locator("#run-body .run-link").first).to_have_text(f"run-{run_id}")

        with page.expect_download() as download_info:
            page.locator('[data-action="export-json"]').click()
        records = json.loads(download_info.value.path().read_text())
        assert {r["id"] for r in records} == {run_id, second["id"]}
        with page.expect_download() as download_info:
            page.locator('[data-action="export-csv"]').click()
        records = list(
            csv.DictReader(io.StringIO(download_info.value.path().read_text()))
        )
        assert len(records) == 2
        exported_note = next(r["notes"] for r in records if int(r["run_id"]) == run_id)
        assert not exported_note.startswith("="), exported_note

        page.get_by_label(f"Select run {run_id} for comparison", exact=True).check()
        page.get_by_label(
            f"Select run {second['id']} for comparison", exact=True
        ).check()
        page.get_by_role("button", name="Compare selected", exact=True).click()
        expect(page.locator("#comparison")).to_contain_text("-0.25")
        expect(page.locator("#comparison")).to_contain_text("waiting")
        expect(page.locator("#comparison")).to_contain_text("completed")

        for width in (320, 375, 414, 768, 1440):
            page.set_viewport_size({"width": width, "height": 960})
            assert page.evaluate("document.body.scrollWidth <= innerWidth"), width
            assert page.evaluate(
                "document.documentElement.scrollWidth <= innerWidth"
            ), width
            for nav in ("Projects", "Catalog", "Experiments"):
                page.locator(".nav").get_by_role("button", name=nav, exact=True).click()
                expect(page.locator("#crumb")).to_have_text(nav)
            assert page.evaluate(
                "document.documentElement.scrollWidth <= innerWidth"
            ), width

        # A failed load exposes a recoverable error instead of a blank workbench.
        page.route(
            "**/projects/",
            lambda route: route.fulfill(
                status=503, json={"detail": "Synthetic connection failure"}
            ),
        )
        page.reload()
        expect(page.locator("#table-state")).to_contain_text(
            "Synthetic connection failure"
        )
        page.unroute("**/projects/")
        page.get_by_role("button", name="Retry", exact=True).click()
        expect(page.locator("#run-table-wrap")).to_be_visible()
        assert not errors, errors
        browser.close()
        print(
            "Browser workflows, exports, responsive navigation, "
            "and error recovery passed."
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", required=True)
    run(parser.parse_args().url.rstrip("/"))
