"""Debug script to download file from Table 1"""

import asyncio
import os
from playwright.async_api import async_playwright


async def debug_table1_download():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(locale="uk-UA", accept_downloads=True)
        page = await context.new_page()

        # Navigate to Form SE page directly
        form_url = "https://public.naqa.gov.ua/v2/form-se/14698/view"
        print(f"Navigating to: {form_url}")
        await page.goto(form_url)
        await page.wait_for_timeout(5000)

        # Get tabs and click on Tab 12 (Таблиця 1)
        role_tabs = await page.locator('[role="tab"]').all()
        print(f"Found {len(role_tabs)} tabs")

        print("\n=== CLICKING TAB 12 (Таблиця 1) ===")
        await role_tabs[12].click()
        await page.wait_for_timeout(3000)

        # Find the table
        table = page.locator("table").first
        rows = await table.locator("tbody tr").all()
        print(f"Found {len(rows)} rows in Table 1")

        # Click on first row's first column (component name)
        if rows:
            first_row = rows[0]
            cells = await first_row.locator("td").all()
            if cells:
                first_cell = cells[0]  # First column: Назва освітнього компонента
                cell_text = await first_cell.text_content()
                print(f"\n=== CLICKING ON FIRST COMPONENT: {cell_text[:50]}... ===")

                await first_cell.click()
                await page.wait_for_timeout(2000)

                # Look for "Переглянути" button
                print("\n=== LOOKING FOR 'Переглянути' BUTTON ===")
                view_btn = page.locator('button:has-text("Переглянути"):visible')
                if await view_btn.count() > 0:
                    print("Found visible 'Переглянути' button, clicking...")

                    # Set up download handler
                    download_path = "/tmp/test_download"
                    os.makedirs(download_path, exist_ok=True)

                    # Try to capture the download
                    try:
                        async with page.expect_download(timeout=15000) as download_info:
                            await view_btn.first.click()
                        download = await download_info.value
                        print(f"  Download triggered!")
                        print(f"  Suggested filename: {download.suggested_filename}")
                        print(f"  URL: {download.url}")

                        # Save the file
                        save_path = f"{download_path}/{download.suggested_filename}"
                        await download.save_as(save_path)
                        print(f"  Saved to: {save_path}")

                        # Check file size
                        file_size = os.path.getsize(save_path)
                        print(f"  File size: {file_size} bytes")

                    except Exception as e:
                        print(f"  Download failed or no download triggered: {e}")

                        # Check if a new tab or popup opened
                        await page.wait_for_timeout(3000)
                        pages = context.pages
                        print(f"  Pages open: {len(pages)}")
                        for i, pg in enumerate(pages):
                            print(f"    Page {i}: {pg.url[:100]}")

                        # Check for blob URL in current page
                        current_url = page.url
                        print(f"  Current page URL: {current_url}")

                        # Try clicking again with different approach
                        print("\n=== TRYING ALTERNATIVE APPROACH ===")
                        await view_btn.first.click()
                        await page.wait_for_timeout(5000)

                        # Check all pages again
                        pages = context.pages
                        print(f"  Pages after click: {len(pages)}")
                        for i, pg in enumerate(pages):
                            url = pg.url
                            print(f"    Page {i}: {url[:100]}")
                            if "blob:" in url:
                                print(f"    ^ This is a blob URL!")

                else:
                    print("No visible 'Переглянути' button found")

                    # Look at what's visible
                    print("\n=== VISIBLE BUTTONS ===")
                    all_buttons = await page.locator("button:visible").all()
                    for btn in all_buttons[:10]:
                        text = await btn.text_content()
                        if text.strip():
                            print(f"  Button: '{text.strip()[:40]}'")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(debug_table1_download())
