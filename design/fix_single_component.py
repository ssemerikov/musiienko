#!/usr/bin/env python3
"""
Re-download a single missing component from case 8588.
"""

import asyncio
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from naqa_scraper.browser import BrowserManager
from naqa_scraper.extractor import Extractor

async def main():
    case_id = "8588"
    component_name = "ОДЗ.06 Психологія творчості"
    component_index = 17  # 0-indexed, this is component 18

    case_url = f"https://public.naqa.gov.ua/v2/form-se/{case_id}/view"
    output_dir = Path(f"data/downloads_by_level/Бакалавр/{case_id}/components/017_ОДЗ.06_Психологія_творчості")
    text_dir = Path(f"data/text_by_level/Бакалавр/{case_id}/components/017_ОДЗ.06_Психологія_творчості")

    output_dir.mkdir(parents=True, exist_ok=True)
    text_dir.mkdir(parents=True, exist_ok=True)

    print(f"Downloading missing component: {component_name}")

    browser_manager = BrowserManager()

    try:
        page = await browser_manager.start()
        await page.goto(case_url, wait_until="networkidle", timeout=60000)
        await asyncio.sleep(3)

        # Navigate to Tab 12 (Table 1)
        tab_selector = '[role="tab"]'
        tabs = await page.query_selector_all(tab_selector)
        if len(tabs) > 12:
            await tabs[12].click()
            await asyncio.sleep(2)

        # Find component rows
        rows = await page.query_selector_all('table tbody tr')
        print(f"Found {len(rows)} component rows")

        if component_index < len(rows):
            row = rows[component_index]

            # Find download button in this row
            download_btn = await row.query_selector('button[title*="Переглянути"], button:has-text("Переглянути")')

            if not download_btn:
                # Try finding any button in the row
                buttons = await row.query_selector_all('button')
                for btn in buttons:
                    btn_text = await btn.inner_text()
                    if 'Переглянути' in btn_text or 'pdf' in btn_text.lower():
                        download_btn = btn
                        break

            if download_btn:
                # Set up download handler
                async with page.expect_download(timeout=60000) as download_info:
                    await download_btn.click()

                download = await download_info.value
                filename = download.suggested_filename or f"{component_name}.pdf"
                safe_filename = filename.replace(" ", "_").replace("/", "_")

                save_path = output_dir / safe_filename
                await download.save_as(save_path)
                print(f"Downloaded: {save_path}")

                # Extract text
                result = subprocess.run(
                    ["pdftotext", "-layout", str(save_path), "-"],
                    capture_output=True, text=True, timeout=60
                )
                if result.returncode == 0 and result.stdout.strip():
                    txt_path = text_dir / (safe_filename.replace(".pdf", ".txt"))
                    with open(txt_path, "w", encoding="utf-8") as f:
                        f.write(result.stdout)
                    print(f"Extracted text: {txt_path}")
            else:
                print("Could not find download button for this component")
        else:
            print(f"Component index {component_index} out of range")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        await browser_manager.stop()

if __name__ == "__main__":
    asyncio.run(main())
