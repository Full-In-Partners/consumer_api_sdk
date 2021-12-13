# Harmonic Consumer API SDK

## python
currently python SDK is only python3 compatible

See [README](python/README.md) for installation details

### Quick Start
```
from harmonic.api import HarmonicClient
client = HarmonicClient('YOUR_API_KEY')
# fetch companies with id 1 and 4
companies = client.get_companies_by_ids([1, 4])
print(companies)
```

Checkout below demos for advanced usage
* [Search Demo](python/search_demo.py) 
```
keywords = "San Francisco machine learning sequoia"
keyword_serach_res = client.search(
    keywords,
    include_results=True,
    page=0,
    page_size=10,
)
```
* [Enrichment Demo](python/enrichment_demo.py)
```
for url in [
    "https://www.instagram.com/allbirds",
    "https://www.facebook.com/weareallbirds/",
    "https://www.crunchbase.com/organization/amazon",
    "https://pitchbook.com/profiles/company/11919-79",
    "https://angel.co/company/amazon",
    "https://www.linkedin.com/company/amazon/",
]:
    client.enrich_company(url)
```
* [Watchlist Demo](python/watchlist_demo.py) 


