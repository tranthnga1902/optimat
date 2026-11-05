"""Run on the isolated qa-excel route when its candidate is available."""
import argparse
import csv
from pathlib import Path
from playwright.sync_api import sync_playwright

parser = argparse.ArgumentParser()
parser.add_argument("url")
args = parser.parse_args()
out = Path(__file__).resolve().parent
with sync_playwright() as playwright:
    browser = playwright.chromium.launch(channel="chrome")
    for name, width, height in [("desktop", 1440, 900), ("mobile", 390, 844)]:
        context = browser.new_context(viewport={"width": width, "height": height},
                                      permissions=["clipboard-read", "clipboard-write"])
        page = context.new_page()
        page.goto(args.url)
        table = page.locator(".xl table")
        table.get_by_role("columnheader", name="STT").wait_for()
        assert table.locator("tbody tr").count() == 3
        page.get_by_role("searchbox", name="Lọc").fill("Gạch")
        table.get_by_role("button", name="Số lượng").click()
        codes = table.locator("tbody tr td:nth-child(2)")
        assert codes.all_text_contents() == ["QA-01", "QA-02"]
        page.get_by_role("button", name="Sao chép bảng").click()
        page.get_by_role("status").filter(has_text="2 dòng").wait_for()
        text = page.evaluate("navigator.clipboard.readText()")
        assert [r[0] for r in csv.reader(text.splitlines(), delimiter="\t")][1:] == codes.all_text_contents()
        codes.first.click()
        page.keyboard.press("Control+c")
        assert page.evaluate("navigator.clipboard.readText()") == "QA-01"
        with page.expect_download() as dl:
            page.get_by_role("button", name="Tải CSV (Excel)").click()
        with open(dl.value.path(), encoding="utf-8-sig", newline="") as f:
            assert [r[0] for r in csv.reader(f)][1:] == ["QA-01", "QA-02"]
        wrapper = page.locator(".xl")
        if name == "mobile":
            x = table.locator(".rn").first.bounding_box()["x"]
            moved = wrapper.evaluate("(e) => { e.scrollLeft=e.scrollWidth; return e.scrollLeft; }")
            assert moved > 0 and abs(table.locator(".rn").first.bounding_box()["x"] - x) <= 1
            wrapper.evaluate("e => {e.scrollLeft=0}")
        assert page.evaluate("document.documentElement.scrollWidth") <= width
        page.screenshot(path=out / f"excel-{name}.png")
        context.close()
    browser.close()
