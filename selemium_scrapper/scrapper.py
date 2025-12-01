from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
)
import pandas as pd
import time
import argparse
# import sys
import random
import re

## Extra functions for improved scrolling and data gathering -- Start
def setup_driver(headless: bool = False):
    options = webdriver.ChromeOptions()
    if headless:
        options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=options)
    return driver


def extract_table(driver):
    try:
        table = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, "table")))
    except TimeoutException:
        raise RuntimeError("Timed out waiting for a table element on the page")

    headers = []
    try:
        thead = table.find_element(By.TAG_NAME, "thead")
        ths = thead.find_elements(By.TAG_NAME, "th")
        headers = [((th.text or '').strip() or f"col_{i}") for i, th in enumerate(ths)]
    except NoSuchElementException:
        try:
            first = table.find_element(By.TAG_NAME, "tr")
            headers = [f"col_{i}" for i, _ in enumerate(first.find_elements(By.TAG_NAME, "td"))]
        except Exception:
            headers = []

    rows_data = []
    try:
        tbody = table.find_element(By.TAG_NAME, "tbody")
        rows = tbody.find_elements(By.TAG_NAME, "tr")
    except NoSuchElementException:
        rows = table.find_elements(By.TAG_NAME, "tr")

    for r in rows:
        cells = r.find_elements(By.TAG_NAME, "td")
        if not cells:
            continue
        row_vals = []
        for c in cells:
            try:
                raw = c.get_attribute("innerText") or c.text
            except Exception:
                raw = c.text
            text = (raw or '').strip()
            row_vals.append(text)

        if headers and len(headers) == len(row_vals):
            rows_data.append({h: v for h, v in zip(headers, row_vals)})
        else:
            row_dict = {}
            for i, v in enumerate(row_vals):
                row_dict[f"col_{i}"] = v
            rows_data.append(row_dict)

    return rows_data, headers


def save_to_csv(rows, headers, output_path: str):
    if not rows:
        print("No rows extracted; nothing to save.")
        return
    df = pd.DataFrame(rows)
    
    if headers:
        cols = [c for c in headers if c in df.columns] + [c for c in df.columns if c not in headers]
        df = df[cols]
    df.to_csv(output_path, index=False)
    print(f"Saved {len(df)} rows to {output_path}")


def human_sleep(min_s: float, max_s: float):
    """IMPORTANT: Sleep a small random amount between min_s and max_s to mimic human behaviour."""
    if min_s <= 0 and max_s <= 0:
        return
    wait = random.uniform(min_s, max_s) if max_s > min_s else min_s
    time.sleep(wait)


def find_scrollable_container_for_table(driver):
    try:
        table = driver.find_element(By.TAG_NAME, "table")
    except Exception:
        return None

    script = """
    const table = arguments[0];
    let el = table.parentElement;
    while (el) {
        const style = window.getComputedStyle(el);
        const overflowY = style.overflowY || '';
        if (el.scrollHeight > el.clientHeight && (overflowY.indexOf('auto') !== -1 || overflowY.indexOf('scroll') !== -1)) {
            return el;
        }
        el = el.parentElement;
    }
    return null;
    """
    try:
        container = driver.execute_script(script, table)
        return container
    except Exception:
        return None


def get_total_results_count(driver):
    try:
        el = driver.find_element(By.XPATH, "//div[contains(., 'Showing') and contains(., 'result')]")
        text = el.text
        # find the largest number in the text
        nums = re.findall(r"[0-9,]+", text)
        if not nums:
            return None
        # choose the largest numeric value (likely total)
        vals = [int(n.replace(',', '')) for n in nums]
        return max(vals)
    except Exception:
        return None


def parse_row_element(r):
    """Parse a <tr> element into a list of cell texts (strings)."""
    cells = r.find_elements(By.TAG_NAME, 'td')
    vals = []
    for c in cells:
        try:
            raw = c.get_attribute('innerText') or c.text
        except Exception:
            raw = c.text
        vals.append((raw or '').strip())
    return vals


def gather_all_rows_by_scrolling(driver, min_wait, max_wait, expected_total=None, max_cycles=200):
    try:
        table = driver.find_element(By.TAG_NAME, 'table')
    except Exception:
        return [], []

    headers = []
    try:
        thead = table.find_element(By.TAG_NAME, 'thead')
        ths = thead.find_elements(By.TAG_NAME, 'th')
        headers = [((th.text or '').strip() or f'col_{i}') for i, th in enumerate(ths)]
    except Exception:
        headers = []

    container = find_scrollable_container_for_table(driver)
    if not container:
        return extract_table(driver)

    try:
        scroll_height = driver.execute_script('return arguments[0].scrollHeight;', container)
        client_height = driver.execute_script('return arguments[0].clientHeight;', container)
    except Exception:
        try:
            container = driver.find_element(By.XPATH, "//table/ancestor::*[contains(@style,'overflow') or @role='presentation']")
            scroll_height = driver.execute_script('return arguments[0].scrollHeight;', container)
            client_height = driver.execute_script('return arguments[0].clientHeight;', container)
        except Exception:
            return extract_table(driver)

    if not scroll_height or not client_height:
        return extract_table(driver)

    step = max(int(client_height * 0.75), 200)

    seen = {}
    rows_out = []

    try:
        driver.execute_script('arguments[0].scrollTop = 0;', container)
    except Exception:
        pass

    offset = 0
    iterations = 0
    max_iterations = 20000
    last_collected = len(seen)

    while iterations < max_iterations and (expected_total is None or len(seen) < expected_total):
        try:
            scroll_height = driver.execute_script('return arguments[0].scrollHeight;', container)
            client_height = driver.execute_script('return arguments[0].clientHeight;', container)
        except Exception:
            break

        if offset > scroll_height:
            if len(seen) == last_collected:
                break
            last_collected = len(seen)
            offset = 0

        try:
            driver.execute_script('arguments[0].scrollTop = arguments[1];', container, offset)
        except Exception:
            try:
                driver.execute_script('arguments[0].scrollTop = arguments[0].scrollTop + arguments[0].clientHeight;', container)
            except Exception:
                break

        human_sleep(min_wait, max_wait)

        try:
            cur_top = driver.execute_script('return arguments[0].scrollTop;', container)
            cur_sh = driver.execute_script('return arguments[0].scrollHeight;', container)
            cur_ch = driver.execute_script('return arguments[0].clientHeight;', container)
            elements = driver.find_elements(By.CSS_SELECTOR, 'table tbody tr')
            print(f"scrollTop={cur_top} / {cur_sh} (client={cur_ch}) — visible rows={len(elements)} — collected={len(seen)}")
        except Exception:
            elements = driver.find_elements(By.CSS_SELECTOR, 'table tbody tr')

        new_found = False
        for el in elements:
            vals = parse_row_element(el)
            if not vals:
                continue
            key = (vals[0] if len(vals) > 0 else '', vals[1] if len(vals) > 1 else '')
            if key in seen:
                continue
            seen[key] = True
            if headers and len(headers) == len(vals):
                rows_out.append({h: v for h, v in zip(headers, vals)})
            else:
                rowd = {f'col_{i}': v for i, v in enumerate(vals)}
                rows_out.append(rowd)
            new_found = True

        offset += step
        iterations += 1

        if new_found:
            human_sleep(min_wait, max_wait)

        if expected_total and len(seen) >= expected_total:
            break

    return rows_out, headers

## Extra functions for improved scrolling and data gathering -- End

def main():
    parser = argparse.ArgumentParser(description="Scrape THE world university rankings (latest) table")
    parser.add_argument("--output", "-o", default="the_world_ranking.csv", help="CSV output path")
    parser.add_argument("--headless", action="store_true", help="Run browser in headless mode")
    parser.add_argument("--dry-run", action="store_true", help="Don't save CSV, just check extraction")
    parser.add_argument("--min-wait", type=float, default=0.8, help="Minimum human-like wait between actions (seconds)")
    parser.add_argument("--max-wait", type=float, default=2.0, help="Maximum human-like wait between actions (seconds)")
    parser.add_argument("--url", default="https://www.timeshighereducation.com/world-university-rankings/latest/world-ranking", help="Page URL to scrape")
    args = parser.parse_args()

    driver = None
    try:
        driver = setup_driver(headless=args.headless)
        print(f"Loading {args.url} ...")
        driver.get(args.url)

        # wait for table or main content
        try:
            WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, "table")))
        except TimeoutException:
            print("No table located within timeout. The page structure may have changed or requires interaction.")

        human_sleep(args.min_wait, args.max_wait)
        total_expected = get_total_results_count(driver)
        rows, headers = gather_all_rows_by_scrolling(driver, args.min_wait, args.max_wait, expected_total=total_expected)

        print(f"Extracted {len(rows)} rows; {len(headers) if headers else 0} headers found.")


        # Dry-run check: NOT REQUIRED, The code works as is. For future change considerations.
        if args.dry_run:
            print("Dry-run enabled — not saving CSV.")
        else:
            save_to_csv(rows, headers, args.output)

    except Exception as e:
        print("Error:", e)
        raise
    finally:
        if driver:
            driver.quit()


if __name__ == "__main__":
    main()