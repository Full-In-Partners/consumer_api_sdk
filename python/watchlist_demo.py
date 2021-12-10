from harmonic.api import HarmonicClient
import argparse


def company_summary(company):
    summary_template = """
    company: {}
        website: {}
        headcount: {}
        funding_stage:{}
        investors: {}
    """
    name = company["name"]
    website = company["website"]["domain"]
    headcount = company["headcount"]
    funding_stage = company["funding"]["funding_stage"]
    investors = [investor["name"] for investor in company["funding"]["investors"]]
    return summary_template.format(name, website, headcount, funding_stage, investors)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--apikey", type=str, required=True, help="HARMONIC API KEY")
    args = parser.parse_args()

    client = HarmonicClient(args.apikey)

    print("----- WATCHLISTS -----")
    watchlists = client.get_watchlists()
    print("all watchlist names")
    print([wl["name"] for wl in watchlists])

    if len(watchlists) > 0:
        watchlist_id = watchlists[-1]["id"]

        keywords = "San Francisco machine learning sequoia"
        print(f"\nsearch new companies with keywords: {keywords}")
        company_ids = client.search(
            keywords,
            include_results=False,
            page=0,
            page_size=10,
        )["results"]
        client.add_company_to_watchlist(watchlist_id, company_ids, isURN=True)
        print("\nupdate watchlist with new search result")
        client.set_watchlist(watchlist_id, name="sdk demo watchlist")
        watchlist = client.get_watchlist_by_id(watchlist_id)
        print(f"\nfirst 10 items in {watchlist['name']}:")
        for company in watchlist["companies"][:10]:
            print(company_summary(company))
