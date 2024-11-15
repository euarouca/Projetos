from selenium_driverless import webdriver
from selenium_driverless.types.by import By
import asyncio
import os
from asynciolimiter import Limiter


rate_limiter = Limiter(1/5)
async def get_data(driver, url):
    await rate_limiter.wait()
    new_context = await driver.new_context()
    await new_context.get(url)
    schema = await new_context.find_element(By.CSS, "script[type='application/ld+json']")
    print(await schema.text)
    await new_context.close()
    
async def main():
    options = webdriver.ChromeOptions()
    async with webdriver.Chrome(options=options) as driver:
        await driver.get('https://www.zara.com/br/pt/man-all-products-l7465.html?v1=2481812', wait_load=True)
        await asyncio.sleep(10)
        
        products = await driver.find_elements(By.CSS, 'div.product-grid-product__figure')
        urls = []
        for p in products:
            data = await p.find_element(By.CSS, 'a')
            link = await data.get_dom_attribute('href')
            urls.append(link)
        
        tasks = [get_data(driver, url) for url in urls]
        await asyncio.gather(*tasks)
        
        
asyncio.run(main())