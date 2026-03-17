"""Playwright browser automation with anti-detection and polite scraping"""

import asyncio
import logging
import random
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from playwright.async_api import Browser, BrowserContext, Page, async_playwright

from .config import settings

logger = logging.getLogger(__name__)


class BrowserManager:
    """Manages Playwright browser with anti-detection settings"""

    def __init__(self):
        self.browser: Browser | None = None
        self.context: BrowserContext | None = None
        self.page: Page | None = None
        self._playwright = None
        self._last_request_time: float = 0

    async def start(self) -> Page:
        """Initialize browser with anti-detection settings"""
        self._playwright = await async_playwright().start()

        # Launch browser with anti-detection
        self.browser = await self._playwright.chromium.launch(
            headless=settings.headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ],
        )

        # Create context with realistic settings
        self.context = await self.browser.new_context(
            viewport={"width": settings.viewport_width, "height": settings.viewport_height},
            locale=settings.locale,
            timezone_id="Europe/Kyiv",
            accept_downloads=True,
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        )

        # Disable webdriver detection
        await self.context.add_init_script(
            """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """
        )

        # Set default timeouts
        self.context.set_default_timeout(settings.element_timeout)
        self.context.set_default_navigation_timeout(settings.navigation_timeout)

        self.page = await self.context.new_page()
        logger.info("Browser started with anti-detection settings")

        return self.page

    async def stop(self) -> None:
        """Clean up browser resources"""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self._playwright:
            await self._playwright.stop()
        logger.info("Browser stopped")

    async def human_delay(self, min_sec: float | None = None, max_sec: float | None = None) -> None:
        """Add human-like random delay between actions"""
        min_delay = min_sec if min_sec is not None else settings.min_delay_seconds
        max_delay = max_sec if max_sec is not None else settings.max_delay_seconds
        delay = random.uniform(min_delay, max_delay)
        logger.debug(f"Waiting {delay:.2f} seconds (human delay)")
        await asyncio.sleep(delay)

    async def rate_limited_navigate(self, url: str) -> None:
        """Navigate to URL with rate limiting"""
        await self.human_delay()
        logger.info(f"Navigating to: {url}")
        await self.page.goto(url, wait_until="networkidle")

    async def safe_click(self, selector: str, timeout: int | None = None) -> bool:
        """Click element with error handling and human delay"""
        try:
            await self.human_delay(0.5, 1.5)  # Short delay before click
            element = self.page.locator(selector)
            await element.wait_for(state="visible", timeout=timeout or settings.element_timeout)
            await element.click()
            return True
        except Exception as e:
            logger.warning(f"Failed to click {selector}: {e}")
            return False

    async def safe_fill(self, selector: str, value: str) -> bool:
        """Fill input with error handling"""
        try:
            await self.human_delay(0.3, 0.8)
            element = self.page.locator(selector)
            await element.wait_for(state="visible")
            await element.fill(value)
            return True
        except Exception as e:
            logger.warning(f"Failed to fill {selector}: {e}")
            return False

    async def wait_for_load(self, timeout: int | None = None) -> None:
        """Wait for page to finish loading"""
        await self.page.wait_for_load_state("networkidle", timeout=timeout)

    async def scroll_to_bottom(self) -> None:
        """Scroll to bottom of page gradually"""
        await self.page.evaluate(
            """
            async () => {
                const delay = ms => new Promise(resolve => setTimeout(resolve, ms));
                const height = document.body.scrollHeight;
                const step = window.innerHeight / 2;
                for (let i = 0; i < height; i += step) {
                    window.scrollTo(0, i);
                    await delay(100);
                }
                window.scrollTo(0, document.body.scrollHeight);
            }
        """
        )


@asynccontextmanager
async def get_browser() -> AsyncGenerator[BrowserManager, None]:
    """Context manager for browser lifecycle"""
    manager = BrowserManager()
    try:
        await manager.start()
        yield manager
    finally:
        await manager.stop()
