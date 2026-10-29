# Site crawl and inventory

`scripts/full_site_audit.py` HEAD-checks every sitemap URL and GETs a fixed priority set plus the machine-readable files.

Read `reports/crawl_summary.json` after a run. Failures are HTTP status other than 200. The script does not store HTML bodies, so the report stays small.

Inventory fields that matter: `status_200_rate`, `service_area_urls`, `prefix_counts`, `priority_pages[].bytes`, `markdown_twins`.
