import requests
import threading

HARMONIC_CONSUMER_API_ENDPOINT = "https://api.harmonic.ai"
HARMONIC_CONSUMER_API_ERROR_MSG = "error out unexpectedly. Please check your rate limit, timeout setting or contact us support@harmonic.ai"


class HarmonicClient:
    def __init__(self, API_KEY):
        self.API_KEY = API_KEY

    # [ENRICH](https://console.harmonic.ai/docs/api-reference/enrich)
    def enrich_company(self):
        """[Enrich a company **POST**](https://console.harmonic.ai/docs/api-reference/enrich#enrich-a-company)"""
        raise NotImplementedError

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

    def search(self, keywordsOrQuery, include_results=True, page=0, page_size=50):
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
        if isinstance(keywordsOrQuery, str):
            body["keywords"] = keywordsOrQuery
        elif isinstance(keywordsOrQuery, dict):
            if not keywordsOrQuery.get("pagination"):
                keywordsOrQuery["pagination"] = {}
            keywordsOrQuery["pagination"]["start"] = page * page_size
            keywordsOrQuery["pagination"]["page_size"] = page_size
            body["query"] = keywordsOrQuery
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
