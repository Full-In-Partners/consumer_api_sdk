from enum import Enum
from urllib.parse import urlparse

import requests

HARMONIC_CONSUMER_API_ENDPOINT = "https://api.harmonic.ai"
HARMONIC_CONSUMER_API_ERROR_MSG = "error out unexpectedly. Please check your rate limit, timeout setting or contact us support@harmonic.ai"


class COMPANY_CANONICAL_URL_TYPE(str, Enum):
    LinkedinCompanyCanonical = "linkedin_url"
    WebsiteCompanyCanonical = "website_url"
    TwitterCompanyCanonical = "twitter_url"
    CrunchbaseCompanyCanonical = "crunchbase_url"
    PitchbookCompanyCanonical = "pitchbook_url"
    InstagramCompanyCanonical = "instagram_url"
    FacebookCompanyCanonical = "facebook_url"
    AngellistCompanyCanonical = "angellist_url"
    MonsterCompanyCanonical = "monster_url"
    IndeedCompanyCanonical = "indeed_url"
    StackoverflowCompanyCanonical = "stackoverflow_url"
    GlassdoorCompanyCanonical = "glassdoor_url"
    DomainCompanyCanonical = "website_domain"

    @classmethod
    def from_domain(cls, root_domain):
        domain_map = {
            "linkedin.com": COMPANY_CANONICAL_URL_TYPE.LinkedinCompanyCanonical,
            "twitter.com": COMPANY_CANONICAL_URL_TYPE.TwitterCompanyCanonical,
            "crunchbase.com": COMPANY_CANONICAL_URL_TYPE.CrunchbaseCompanyCanonical,
            "pitchbook.com": COMPANY_CANONICAL_URL_TYPE.PitchbookCompanyCanonical,
            "instagram.com": COMPANY_CANONICAL_URL_TYPE.InstagramCompanyCanonical,
            "facebook.com": COMPANY_CANONICAL_URL_TYPE.FacebookCompanyCanonical,
            "angel.co": COMPANY_CANONICAL_URL_TYPE.AngellistCompanyCanonical,
            "monster.com": COMPANY_CANONICAL_URL_TYPE.MonsterCompanyCanonical,
            "indeed.com": COMPANY_CANONICAL_URL_TYPE.IndeedCompanyCanonical,
            "stackoverflow.com": COMPANY_CANONICAL_URL_TYPE.StackoverflowCompanyCanonical,
            "glassdoor.com": COMPANY_CANONICAL_URL_TYPE.GlassdoorCompanyCanonical,
        }
        return domain_map.get(root_domain)


class PERSON_CANONICAL_URL_TYPE(str, Enum):
    LinkedinPersonCanonical = "linkedin_url"
    TwitterPersonCanonical = "twitter_profile_url"
    CrunchbasePersonCanonical = "crunchbase_profile_url"


class HarmonicCompanyEnrichmentRequest:
    def __init__(self, canonical_url_type, url):
        self.canonical_url_type = canonical_url_type
        self.url = url

    @classmethod
    def infer_from_url(cls, url):
        parsed_uri = urlparse(url)
        domain = "{uri.netloc}/".format(uri=parsed_uri)
        root_domain = domain.replace("www.", "").rstrip("/")
        url_type = COMPANY_CANONICAL_URL_TYPE.from_domain(root_domain)
        return HarmonicCompanyEnrichmentRequest(url_type, url) if url_type else None

    def to_dict(self):
        return {self.canonical_url_type.value: self.url}


class HarmonicClient:
    def __init__(self, API_KEY):
        self.API_KEY = API_KEY

    # [ENRICH](https://console.harmonic.ai/docs/api-reference/enrich)
    def enrich_company(self, url_or_enrichment_request):
        """[Enrich a company **POST**](https://console.harmonic.ai/docs/api-reference/enrich#enrich-a-company)"""
        params = {"apikey": self.API_KEY}
        if isinstance(url_or_enrichment_request, str):
            enrichment_request = HarmonicCompanyEnrichmentRequest.infer_from_url(
                url_or_enrichment_request
            )
            if not enrichment_request:
                raise ValueError(
                    "Not able to infer valid domain type from URL, try using HarmonicCompanyEnrichmentRequest(COMPANY_CANONICAL_URL_TYPE.WebsiteCompanyCanonical, YOUR_URL) as parameter"
                )
            params = {
                **params,
                **enrichment_request.to_dict(),
            }
        elif isinstance(url_or_enrichment_request, HarmonicCompanyEnrichmentRequest):
            params = {**params, **url_or_enrichment_request.to_dict()}
        else:
            raise ValueError(
                "Enrichment input has to be either url(str) or HarmonicCompanyEnrichmentRequest"
            )
        API_URL = f"{HARMONIC_CONSUMER_API_ENDPOINT}/companies"
        company = requests.post(
            API_URL,
            params=params,
        ).json()
        return company

    # [DISCOVER](https://console.harmonic.ai/docs/api-reference/discover#discover)
    def get_saved_searches(self):
        """[Get saved searches **GET**](https://console.harmonic.ai/docs/api-reference/discover#get-saved-searches)"""
        API_URL = f"{HARMONIC_CONSUMER_API_ENDPOINT}/savedSearches"
        saved_searches = requests.get(
            API_URL,
            params={"apikey": self.API_KEY},
        ).json()
        return saved_searches

    def get_saved_searches_by_owner(self):
        API_URL = f"{HARMONIC_CONSUMER_API_ENDPOINT}/saved_searches"
        saved_searches = requests.get(
            API_URL,
            params={"apikey": self.API_KEY},
        ).json()
        return saved_searches

    def get_saved_search_results(
        self, saved_search_id, record_processor=None, page_size=100
    ):
        """[Get saved search results **GET**](https://console.harmonic.ai/docs/api-reference/discover#get-saved-search-results)"""
        API_URL = (
            f"{HARMONIC_CONSUMER_API_ENDPOINT}/saved_searches:results/{saved_search_id}"
        )

        total_result_count = 0
        page_result_count = 0
        page = 0
        page_error_count = 0
        while page_error_count < 5:  # stop streaming if errors out too many times
            try:
                res = requests.get(
                    API_URL,
                    params={"page": page, "size": page_size, "apikey": self.API_KEY},
                ).json()
                page_result_count = len(res["results"])

                PAGE_INFO = f"page {page}: {page_result_count} results {'(some results might get merged or deleted)' if page_result_count < page_size else ''}"
                print(PAGE_INFO if page_result_count > 0 else "END")
                if page_result_count == 0:
                    break

                for record in res["results"]:
                    if record_processor and callable(record_processor):
                        record_processor(record)
            except requests.exceptions.RequestException:
                page_error_count += 1
                print(f"page {page}: {HARMONIC_CONSUMER_API_ERROR_MSG}")
            total_result_count += page_result_count
            page += 1

        print(
            f"COMPLETE: search {saved_search_id} generated {total_result_count} results"
        )

    def search(self, keywords_or_query, include_results=True, page=0, page_size=50):
        """[Conduct a search **POST**](https://console.harmonic.ai/docs/api-reference/discover#conduct-a-search)"""
        # search by keywords or api_query
        API_URL = f"{HARMONIC_CONSUMER_API_ENDPOINT}/search/companies"
        body = {
            "type": "COMPANIES_LIST",
            "include_count": True,
            "include_results": include_results,
            "page": page,
            "page_size": page_size,
        }
        if isinstance(keywords_or_query, str):
            body["keywords"] = keywords_or_query
        elif isinstance(keywords_or_query, dict):
            if not keywords_or_query.get("pagination"):
                keywords_or_query["pagination"] = {}
            keywords_or_query["pagination"]["start"] = page * page_size
            keywords_or_query["pagination"]["page_size"] = page_size
            body["query"] = keywords_or_query
        else:
            raise ValueError("Search input has to be keywords(str) or query(dict)")

        company = requests.post(
            API_URL,
            params={"apikey": self.API_KEY},
            json=body,
        ).json()
        return company

    # [FETCH](https://console.harmonic.ai/docs/api-reference/fetch#fetch)
    def get_company_by_id(self, id):
        """[Get company by ID **GET**](https://console.harmonic.ai/docs/api-reference/fetch#get-company-by-id)"""
        API_URL = f"{HARMONIC_CONSUMER_API_ENDPOINT}/companies/{id}"
        company = requests.get(API_URL, params={"apikey": self.API_KEY}).json()
        return company

    def get_companies_by_ids(self, ids, isURN=False):
        """[Get companies by ID **GET**](https://console.harmonic.ai/docs/api-reference/fetch#get-companies-by-id)"""
        API_URL = f"{HARMONIC_CONSUMER_API_ENDPOINT}/companies"
        companies = requests.get(
            API_URL, params={("urns" if isURN else "ids"): ids, "apikey": self.API_KEY}
        ).json()
        return companies

    def get_person_by_id(self, id):
        """[Get person by ID **GET**](https://console.harmonic.ai/docs/api-reference/fetch#get-person-by-id)"""
        API_URL = f"{HARMONIC_CONSUMER_API_ENDPOINT}/persons/{id}"
        person = requests.get(API_URL, params={"apikey": self.API_KEY}).json()
        return person

    def get_persons_by_id(self, ids, isURN=False):
        """[Get persons by ID **GET](https://console.harmonic.ai/docs/api-reference/fetch#get-persons-by-id)"""
        API_URL = f"{HARMONIC_CONSUMER_API_ENDPOINT}/persons"
        persons = requests.get(
            API_URL, params={("urns" if isURN else "ids"): ids, "apikey": self.API_KEY}
        ).json()
        return persons

    # [WATCHLIST](https://console.harmonic.ai/docs/api-reference/watchlist#watchlist)
    def set_watchlist(self, name, companies, shared_with_team):
        """[Modify a Watchlist **PUT**](https://console.harmonic.ai/docs/api-reference/watchlist#modify-company-watchlist)"""
        raise NotImplementedError

    def delete_watchlist(self):
        """[Delete a Watchlist **DELETE**](https://console.harmonic.ai/docs/api-reference/watchlist#delete-company-watchlist)"""
        raise NotImplementedError

    def get_watchlist(self):
        """[Get Company Watchlist **GET**](https://console.harmonic.ai/docs/api-reference/watchlist#get-company-watchlist)"""
        raise NotImplementedError

    def add_company_to_watchlist(self):
        """[Add Companies to Watchlist **POST**](https://console.harmonic.ai/docs/api-reference/watchlist#add-companies-to-watchlist)"""
        raise NotImplementedError

    def remove_company_from_watchlist(self):
        """[Remove Companies from Watchlist **POST**](https://console.harmonic.ai/docs/api-reference/watchlist#remove-companies-from-watchlist)"""
        raise NotImplementedError
