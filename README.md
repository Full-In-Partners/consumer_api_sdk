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
# search by keywords, group keywords with ','
keywords = "San Francisco, machine learning, sequoia"
serach_res = client.search(
    keywords,
    include_results=True,
    page=0,
    page_size=10,
)
```
```
# search by saved search (saved from https://console.harmonic.ai)
first_saved_search = client.get_saved_searches_by_owner()[0]
serach_res = client.search(
    first_saved_search["query"],
    include_results=True,
    page=0,
    page_size=10,
)
```
```
# stream companies in my first saved search
first_saved_search = client.get_saved_searches_by_owner()[0]
companies = []
client.get_saved_search_results(
    first_saved_search["entity_urn"],
    record_processor=(lambda c: companies.append(c)),
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
for url in [
    "https://twitter.com/elonmusk",
    "https://www.linkedin.com/in/williamhgates/",
    "https://www.crunchbase.com/person/jeff-bezos",
]:
    client.enrich_person(url)
```
* [Watchlist Demo](python/watchlist_demo.py) 
```
# add companies with id 1 and 4 to my first watchlist
first_watchlist_id = client.get_watchlists()[0]['id']
client.add_company_to_watchlist(first_watchlist_id, [1, 4])
client.add_company_to_watchlist_by_urls(first_watchlist_id, ["microsoft.com","https://www.linkedin.com/company/meta"])
```
