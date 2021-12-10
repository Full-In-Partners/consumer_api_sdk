from enum import Enum
import json
from urllib.parse import urlparse

import requests

HARMONIC_CONSUMER_API_ENDPOINT = "https://api.harmonic.ai"
HARMONIC_CONSUMER_API_ERROR_MSG = "Error out unexpectedly. Please check your rate limit, timeout setting or contact us support@harmonic.ai"
HARMONIC_CONSUMER_API_INTERNAL_ERROR_MSG = "Our service is having some issues"
HARMONIC_CONSUMER_API_RETRYING_MSG = "Something is wrong, retrying..."
HARMONIC_CONSUMER_API_MAX_RETRY_COUNT = 5


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
        self._set_api_endpoint()

    def _set_api_endpoint(self, api_endpoint=None):
        if api_endpoint:
            self.API_ENDPOINT = api_endpoint
        else:
            self.API_ENDPOINT = HARMONIC_CONSUMER_API_ENDPOINT

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
        API_URL = f"{self.API_ENDPOINT}/companies"
        company = requests.post(
            API_URL,
            params=params,
        ).json()
        return company

    # [DISCOVER](https://console.harmonic.ai/docs/api-reference/discover#discover)
    def get_saved_searches(self):
        """[Get saved searches **GET**](https://console.harmonic.ai/docs/api-reference/discover#get-saved-searches)"""
        API_URL = f"{self.API_ENDPOINT}/savedSearches"
        saved_searches = requests.get(
            API_URL,
            params={"apikey": self.API_KEY},
        ).json()
        return saved_searches

    def get_saved_searches_by_owner(self):
        API_URL = f"{self.API_ENDPOINT}/saved_searches"
        saved_searches = requests.get(
            API_URL,
            params={"apikey": self.API_KEY},
        ).json()
        return saved_searches

    def get_saved_search_results(
        self, saved_search_id, record_processor=None, page_size=100
    ):
        """[Get saved search results **GET**](https://console.harmonic.ai/docs/api-reference/discover#get-saved-search-results)"""
        API_URL = f"{self.API_ENDPOINT}/saved_searches:results/{saved_search_id}"
        total_result_count = 0
        page_result_count = 0
        page = 0
        page_error_count = 0
        while (
            page_error_count < HARMONIC_CONSUMER_API_MAX_RETRY_COUNT
        ):  # stop streaming if errors out too many times
            try:
                data = b""
                with requests.get(
                    API_URL,
                    params={"page": page, "size": page_size, "apikey": self.API_KEY},
                    stream=True,
                ) as response:
                    if response.status_code != 200:
                        page_error_count += 1
                        print(f"page {page}: {HARMONIC_CONSUMER_API_RETRYING_MSG}")
                        if response.status_code == 500:
                            print(HARMONIC_CONSUMER_API_INTERNAL_ERROR_MSG)
                        else:
                            print(f"{response.json()}")
                        continue
                    for chunk in response.iter_content(
                        chunk_size=10 * 1024 * 1024
                    ):  # 10MB
                        if chunk:  # filter out keep-alive new chunks
                            data += chunk

                res = json.loads(data)
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
                if page_error_count == HARMONIC_CONSUMER_API_MAX_RETRY_COUNT:
                    print(f"page {page}: {HARMONIC_CONSUMER_API_ERROR_MSG}")
                    break
                else:
                    print(f"page {page}: {HARMONIC_CONSUMER_API_RETRYING_MSG}")
                    continue

            total_result_count += page_result_count
            page += 1

        if page_error_count < HARMONIC_CONSUMER_API_MAX_RETRY_COUNT:
            print(
                f"COMPLETE: search {saved_search_id} generated {total_result_count} results"
            )

    def search(self, keywords_or_query, page=0, page_size=50, include_results=True):
        """[Conduct a search **POST**](https://console.harmonic.ai/docs/api-reference/discover#conduct-a-search)"""
        # search by keywords or api_query
        SEARCH_BY_QUERY_API_URL = f"{self.API_ENDPOINT}/search/companies"
        SEARCH_BY_KEYWORDS_API_URL = f"{self.API_ENDPOINT}/search/companies_by_keywords"
        API_URL = None
        body = {
            "type": "COMPANIES_LIST",
        }
        if isinstance(keywords_or_query, str):
            API_URL = SEARCH_BY_KEYWORDS_API_URL
            body["keywords"] = keywords_or_query
            body["include_ids_only"] = not include_results
            body["page"] = page
            body["page_size"] = page_size
        elif isinstance(keywords_or_query, dict):
            API_URL = SEARCH_BY_QUERY_API_URL
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
        API_URL = f"{self.API_ENDPOINT}/companies/{id}"
        company = requests.get(API_URL, params={"apikey": self.API_KEY}).json()
        return company

    def get_companies_by_ids(self, ids, isURN=False):
        """[Get companies by ID **GET**](https://console.harmonic.ai/docs/api-reference/fetch#get-companies-by-id)"""
        API_URL = f"{self.API_ENDPOINT}/companies"
        companies = requests.get(
            API_URL, params={("urns" if isURN else "ids"): ids, "apikey": self.API_KEY}
        ).json()
        return companies

    def get_person_by_id(self, id):
        """[Get person by ID **GET**](https://console.harmonic.ai/docs/api-reference/fetch#get-person-by-id)"""
        API_URL = f"{self.API_ENDPOINT}/persons/{id}"
        person = requests.get(API_URL, params={"apikey": self.API_KEY}).json()
        return person

    def get_persons_by_ids(self, ids, isURN=False):
        """[Get persons by ID **GET](https://console.harmonic.ai/docs/api-reference/fetch#get-persons-by-id)"""
        API_URL = f"{self.API_ENDPOINT}/persons"
        persons = requests.get(
            API_URL, params={("urns" if isURN else "ids"): ids, "apikey": self.API_KEY}
        ).json()
        return persons

    # [WATCHLIST](https://console.harmonic.ai/docs/api-reference/watchlist#watchlist)
    def set_watchlist(
        self,
        watchlist_id,
        name=None,
        creator=None,
        shared_with_team=None,
        companies=None,
    ):
        """[Modify a Watchlist **PUT**](https://console.harmonic.ai/docs/api-reference/watchlist#modify-company-watchlist)"""
        API_URL = f"{self.API_ENDPOINT}/watchlists/companies/{watchlist_id}"
        wl = self.get_watchlist_by_id(watchlist_id)
        body = {
            "name": wl["name"],
            "creator": wl["creator"],
            "shared_with_team": wl["shared_with_team"],
            "companies": [c["entity_urn"] for c in wl["companies"]],
        }
        if name is not None and isinstance(name, str):
            body["name"] = name
        if creator is not None and isinstance(creator, str):
            body["creator"] = creator
        if shared_with_team is not None and isinstance(shared_with_team, bool):
            body["shared_with_team"] = shared_with_team
        if companies is not None and isinstance(companies, list):
            body["companies"] = companies
        res = requests.put(
            API_URL,
            params={"apikey": self.API_KEY},
            json=body,
        ).json()
        return res

    def delete_watchlist(self, watchlist_id):
        """[Delete a Watchlist **DELETE**](https://console.harmonic.ai/docs/api-reference/watchlist#delete-company-watchlist)"""
        API_URL = f"{self.API_ENDPOINT}/watchlists/companies/{watchlist_id}"
        res = requests.delete(
            API_URL,
            params={"apikey": self.API_KEY},
        ).json()
        return res

    def get_watchlists(self):
        API_URL = f"{self.API_ENDPOINT}/watchlists/companies"
        print(API_URL)
        watchlists = requests.get(API_URL, params={"apikey": self.API_KEY}).json()
        return watchlists

    def get_watchlist_by_id(self, watchlist_id):
        """[Get Company Watchlist **GET**](https://console.harmonic.ai/docs/api-reference/watchlist#get-company-watchlist)"""
        API_URL = f"{self.API_ENDPOINT}/watchlists/companies/{watchlist_id}"
        watchlist = requests.get(API_URL, params={"apikey": self.API_KEY}).json()
        return watchlist

    def add_company_to_watchlist(self, watchlist_id, company_ids, isURN=False):
        """[Add Companies to Watchlist **POST**](https://console.harmonic.ai/docs/api-reference/watchlist#add-companies-to-watchlist)"""
        API_URL = (
            f"{self.API_ENDPOINT}/watchlists/companies/{watchlist_id}:addCompanies"
        )
        res = requests.post(
            API_URL,
            params={"apikey": self.API_KEY},
            json={("urns" if isURN else "ids"): company_ids},
        ).json()
        return res

    def remove_company_from_watchlist(self, watchlist_id, company_ids, isURN=False):
        """[Remove Companies from Watchlist **POST**](https://console.harmonic.ai/docs/api-reference/watchlist#remove-companies-from-watchlist)"""
        API_URL = (
            f"{self.API_ENDPOINT}/watchlists/companies/{watchlist_id}:removeCompanies"
        )
        res = requests.post(
            API_URL,
            params={"apikey": self.API_KEY},
            json={("urns" if isURN else "ids"): company_ids},
        ).json()
        return res
