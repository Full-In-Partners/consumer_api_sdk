from harmonic.api import HarmonicClient
import argparse


def company_summary(company, client):
    summary_template = """
    company: {}
        website: {}
        headcount: {}
        funding_stage:{}
        investors: {}
        people: {}
    """
    name = company["name"]
    website = company["website"]["domain"]
    headcount = company["headcount"]
    funding_stage = company["funding"]["funding_stage"]
    investors = [investor["name"] for investor in company["funding"]["investors"]]
    people_full = client.get_persons_by_id(
        [bio["person"] for bio in company["people"]], isURN=True
    )
    people = [
        (person["full_name"], person["socials"]["LINKEDIN"]["url"])
        for person in people_full
    ]
    return summary_template.format(
        name, website, headcount, funding_stage, investors, people
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--apikey", type=str, required=True, help="HARMONIC API KEY")
    args = parser.parse_args()

    client = HarmonicClient(args.apikey)

    # search companies with keywords
    print("----- KEWORDS SEARCH -----")
    keywords = "San Francisco machine learning sequoia"
    keyword_serach_res = client.search(
        keywords,
        include_results=False,  # only get companies ids and fetch company data later
        page=0,
        page_size=10,
    )
    print(f"keywords: {keywords}")
    print(f"total: {keyword_serach_res['count']}")
    companies = client.get_companies_by_ids(keyword_serach_res["results"], isURN=True)
    print("first page matched company summaries")
    for company in companies:
        print(company_summary(company, client))

    # show my saved searches
    print("----- SAVED SEARCHES -----")
    saved_searches = client.get_saved_searches_by_owner()
    print("search names")
    print([ss["name"] for ss in saved_searches])

    # search companies with saved search
    if len(saved_searches) > 0:
        first_saved_search = saved_searches[0]
        # option 1:
        print("\n--- search with saved search query (only first page demo below) ---")
        saved_searches_res1 = client.search(
            first_saved_search["query"], include_results=True, page=0, page_size=50
        )
        companies = saved_searches_res1["results"]
        print(f"{first_saved_search['name']}: first page matched company domains")
        print(f"{[company['website']['domain'] for company in companies]}")
        # option 2:
        print("\n--- search with saved search id (streaming all) ---")
        companies = []
        saved_searches_res2 = client.get_saved_search_results(
            save_search_id=first_saved_search["entity_urn"],
            record_processor=(lambda c: companies.append(c)),
        )
        print(f"{first_saved_search['name']}: all matched company domains")
        print(f"{[company['website']['domain'] for company in companies]}")
