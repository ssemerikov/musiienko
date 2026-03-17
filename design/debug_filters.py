#!/usr/bin/env python3
"""Debug script to find the degree level dropdown"""

import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(locale='uk-UA', viewport={'width': 1920, 'height': 1080})
        page = await context.new_page()
        
        print("Navigating to NAQA...")
        await page.goto("https://public.naqa.gov.ua", wait_until="networkidle")
        await page.wait_for_timeout(5000)
        
        # Click filter button
        btn = page.locator('[class*="filter"] button')
        await btn.first.click()
        await page.wait_for_timeout(3000)
        
        # Find the "Рівень вищої освіти" label and its sibling/following elements
        print("\nLooking for 'Рівень вищої освіти' dropdown...")
        
        # Get the label element
        label = page.locator('label:has-text("Рівень вищої освіти")')
        if await label.count() > 0:
            print("Found label!")
            
            # Get parent container
            parent = label.locator("xpath=..")
            parent_html = await parent.evaluate("el => el.outerHTML")
            print(f"\nParent HTML:\n{parent_html[:1500]}")
            
            # Find any select/dropdown in the same container
            following_select = parent.locator("select, ng-multiselect-dropdown, [class*='dropdown'], input")
            if await following_select.count() > 0:
                print(f"\nFound {await following_select.count()} input elements near label")
                for i in range(await following_select.count()):
                    elem = following_select.nth(i)
                    tag = await elem.evaluate("el => el.tagName")
                    classes = await elem.get_attribute("class") or ""
                    print(f"  {i}: {tag} class={classes[:50]}")
        
        # Try to find ng-multiselect-dropdown after the label
        print("\nAll ng-multiselect-dropdown elements with context:")
        dropdowns = await page.locator("ng-multiselect-dropdown").all()
        for i, dd in enumerate(dropdowns):
            # Get preceding label
            prev_label = dd.locator("xpath=preceding-sibling::label | preceding::label[1]")
            label_text = "unknown"
            if await prev_label.count() > 0:
                label_text = await prev_label.first.text_content() or "unknown"
            
            # Get placeholder text
            placeholder = await dd.locator(".dropdown-btn span, .c-btn span").first.text_content()
            
            print(f"  {i}: label='{label_text.strip()}', placeholder='{placeholder.strip() if placeholder else 'N/A'}'")
        
        await browser.close()

asyncio.run(main())
