from harmonic.api import HarmonicClient
import argparse

from harmonic.api import (
    COMPANY_CANONICAL_URL_TYPE,
    HarmonicCompanyEnrichmentRequest,
)


def company_summary(company, client):
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

    # search companies with keywords
    print("----- SEND ENRICHMENT REQUEST -----")
    # option 1
    print("\nrequest with company website URL")
    website = "https://www.harmonic.ai"
    print(f"{website}")
    company = client.enrich_company(
        HarmonicCompanyEnrichmentRequest(
            COMPANY_CANONICAL_URL_TYPE.WebsiteCompanyCanonical,
            website,
        )
    )
    print(company_summary(company, client))
    # option 2
    print("\nrequest with company social URLs")
    for url in [
        "https://www.instagram.com/allbirds",
        "https://www.facebook.com/weareallbirds/",
        "https://www.crunchbase.com/organization/amazon",
        "https://pitchbook.com/profiles/company/11919-79",
        "https://angel.co/company/amazon",
        "https://www.linkedin.com/company/amazon/",
    ]:
        print(f"{url}")
        company = client.enrich_company(url)
        print(company_summary(company, client))
