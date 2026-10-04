"""Catalog forms and terminal run actions against a disposable instance."""

import argparse
from uuid import uuid4

from playwright.sync_api import expect, sync_playwright


def run(base_url):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(viewport={"width": 1440, "height": 1000})
        page = context.new_page()
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        suffix = uuid4().hex[:8]
        page.goto(base_url + "/ui/")
        expect(page.locator("#sync-status")).to_have_attribute("data-state", "success")
        page.locator('.nav [data-nav="catalog"]').click()
        ids = {}
        for resource in ("model", "dataset"):
            page.locator(f'[data-action="new-{resource}"]').click()
            dialog = page.get_by_role("dialog")
            name = f"catalog-{resource}-{suffix}"
            dialog.get_by_label("Name", exact=True).fill(name)
            dialog.get_by_label("Version", exact=True).fill("1")
            with page.expect_response(
                lambda response, r=resource: (
                    response.url.endswith(f"/{r}s/")
                    and response.request.method == "POST"
                )
            ) as created:
                dialog.get_by_role("button", name="Create", exact=True).click()
            assert created.value.status == 201
            ids[resource] = created.value.json()["id"]
            expect(dialog).not_to_be_visible()
            expect(page.locator("#catalog-list")).to_contain_text(name)
        page.get_by_role("button", name="New metric-direction", exact=True).click()
        dialog = page.get_by_role("dialog")
        metric = f"catalog-loss-{suffix}"
        dialog.get_by_label("Metric name").fill(metric)
        dialog.get_by_label("Direction", exact=True).select_option("false")
        dialog.get_by_role("button", name="Create", exact=True).click()
        expect(dialog).not_to_be_visible()
        expect(page.locator("#catalog-list")).to_contain_text(metric)
        # Recoverable submission error preserves user input and enables retry.
        page.locator('[data-action="new-model"]').click()
        dialog.get_by_label("Name", exact=True).fill("Preserved input")
        dialog.get_by_label("Version", exact=True).fill("1")
        page.route(
            "**/models/",
            lambda route: route.fulfill(
                status=503, json={"detail": "Synthetic save failure"}
            ),
        )
        dialog.get_by_role("button", name="Create", exact=True).click()
        expect(page.locator("#form-error")).to_contain_text("Synthetic save failure")
        expect(dialog.get_by_label("Name", exact=True)).to_have_value("Preserved input")
        expect(dialog.get_by_role("button", name="Create", exact=True)).to_be_enabled()
        page.unroute("**/models/")
        page.keyboard.press("Escape")
        expect(dialog).not_to_be_visible()
        page.keyboard.press("/")
        expect(page.locator("#global-search")).to_be_focused()
        # Create isolated records for cancel and fail flows.
        project = context.request.post(
            base_url + "/projects/", data={"name": f"terminal-{suffix}"}
        ).json()
        for action, terminal in (("cancel", "cancelled"), ("fail", "failed")):
            response = context.request.post(
                base_url + "/runs/",
                data={
                    "project_id": project["id"],
                    "model_id": ids["model"],
                    "dataset_id": ids["dataset"],
                },
            )
            assert response.status == 201
            run_id = response.json()["id"]
            if action == "fail":
                response = context.request.post(
                    base_url + f"/runs/{run_id}/parameters/",
                    data={"name": "seed", "value": "1"},
                )
                assert response.status == 201
                assert context.request.post(base_url + f"/runs/{run_id}/start").ok
            page.reload()
            expect(page.locator("#sync-status")).to_have_attribute(
                "data-state", "success"
            )
            page.get_by_role("button", name=f"run-{run_id}", exact=True).click()
            page.locator("#detail-content .detail-actions").get_by_role(
                "button",
                name="Cancel" if action == "cancel" else "Mark failed",
                exact=True,
            ).click()
            action_dialog = page.locator("#action-dialog")
            action_dialog.get_by_label("Reason", exact=True).fill(
                "Browser verification"
            )
            action_dialog.get_by_role("button", name="Confirm", exact=True).click()
            expect(page.locator("#detail-content .status")).to_have_text(terminal)
            expect(page.locator("#detail-content")).to_contain_text(
                "Browser verification"
            )
        assert not errors, errors
        browser.close()
        print(
            "Catalog creation, metric direction, form error recovery, search shortcut, "
            "cancel and fail lifecycle workflows passed."
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", required=True)
    run(parser.parse_args().url.rstrip("/"))
