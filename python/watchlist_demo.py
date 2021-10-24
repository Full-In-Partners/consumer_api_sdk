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
        print("\nadd company to watchlist")
        companies = client.search(
            "San Francisco machine learning sequoia",
            include_results=True,
            page=0,
            page_size=10,
        )["results"]
        client.add_company_to_watchlist(watchlist_id, companies, isURN=True)
        print("\nupdate watchlist")
        client.set_watchlist(watchlist_id, name="sdk demo watchlist")
        watchlist = client.get_watchlist_by_id(watchlist_id)
        print(f"\n{watchlist['name']}:")
        for company in watchlist["companies"]:
            print(company_summary(company))
