@echo off
echo ================================
echo Indian Product Scraper
echo ================================
echo.

echo Installing required packages...
pip install requests beautifulsoup4 lxml

echo.
echo Starting product scraping...
echo This may take 5-10 minutes depending on your internet connection.
echo.

python fetcher_to_feeder.py

echo.
echo ================================
echo Scraping completed!
echo ================================
echo.
echo Files generated:
echo 1. products_curl.txt - Ready to execute curl commands
echo 2. scraped_products.csv - Product data for review
echo.

if exist indian_products_curl.txt (
    echo Success! Found %0 curl commands ready to execute.
    echo.
    echo To add products to your system, run:
    echo for /f "tokens=*" %%i in (products_curl.txt) do %%i
    echo.
) else (
    echo Warning: No curl file generated. Check the output above for errors.
)

pause