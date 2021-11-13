# Harmonic Consumer API SDK

## python
currently python SDK is only python3 compatible

See [README](python/README.md) for installation details

### Quick Start
```
from harmonic.api import HarmonicClient
client = HarmonicClient('YOUR_API_KEY')
companies = client.get_companies_by_ids([1, 4])
print(companies)
```

Checkout below demos for advanced usage
* [Search Demo](python/search_demo.py) 
* [Enrichment Demo](python/enrichment_demo.py)
* [Watchlist Demo](python/watchlist_demo.py) 


