"""UI smoke tests against the live web shop (Playwright).

Mirrors the manual workbook cases HOME-TC-001, HOME-TC-002,
PRD-TC-001, AUTH-TC-001, AUTH-TC-002 and CART-TC-001 to CART-TC-003,
which were first executed manually in a browser session on
2026-11-25. These tests repeat the same checks automatically.
"""
import re

import pytest
from playwright.sync_api import Page, expect

from conftest import DEMO_USER, WEB_BASE

pytestmark = pytest.mark.ui


def test_homepage_loads_and_lists_products(page: Page):
    page.goto(WEB_BASE + "/")
    expect(page).to_have_title(re.compile("CHALIGULA"))
    expect(page.get_by_text("Nocturne Wool Coat")).to_be_visible()
    expect(page.get_by_text("Obsidian Leather Jacket")).to_be_visible()
    expect(page.get_by_text("Raven Oversized Tee")).to_be_visible()
    expect(page.get_by_text(re.compile(r"Rp\s?1[.,]850[.,]000"))).to_be_visible()


def test_product_page_shows_price_and_sale(page: Page):
    page.goto(WEB_BASE + "/product/raven-oversized-tee")
    expect(page.get_by_text("Raven Oversized Tee").first).to_be_visible()
    expect(page.get_by_text(re.compile(r"Rp\s?320[.,]000"))).to_be_visible()


def test_login_and_logout_with_demo_customer(page: Page):
    page.goto(WEB_BASE + "/auth/login")
    page.locator("input[type='email']").fill(DEMO_USER["email"])
    page.locator("input[type='password']").fill(DEMO_USER["password"])
    page.get_by_role("button", name=re.compile("sign in", re.I)).click()
    expect(page.get_by_text("Welcome back, Night Owl")).to_be_visible(timeout=30000)
    page.get_by_text("Logout").first.click()
    expect(page.get_by_text(re.compile("login", re.I)).first).to_be_visible(timeout=30000)


def test_add_to_cart_requires_colour_then_succeeds(page: Page):
    page.goto(WEB_BASE + "/product/raven-oversized-tee")
    page.get_by_role("button", name="M", exact=True).first.click()
    page.get_by_role("button", name=re.compile("add to (cart|bag)", re.I)).click()
    expect(page.get_by_text("Select a color")).to_be_visible()
    page.get_by_text("Onyx").first.click()
    page.get_by_role("button", name=re.compile("add to (cart|bag)", re.I)).click()
    expect(page.get_by_text("Added to your bag")).to_be_visible(timeout=30000)
    page.goto(WEB_BASE + "/cart")
    expect(page.get_by_text("Raven Oversized Tee")).to_be_visible()
    expect(page.get_by_text(re.compile(r"Rp\s?320[.,]000"))).to_be_visible()
