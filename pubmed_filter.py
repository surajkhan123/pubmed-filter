import requests
import csv
import argparse
from typing import List, Dict, Optional

PUBMED_API_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
PUBMED_SUMMARY_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"


def fetch_pubmed_papers(query: str) -> List[Dict]:
    """Fetch paper IDs from PubMed based on a query."""
    params = {
        "db": "pubmed",
        "term": query,
        "retmode": "json",
        "retmax": 10  # Adjust as needed
    }
    response = requests.get(PUBMED_API_URL, params=params)
    response.raise_for_status()
    data = response.json()
    return data.get("esearchresult", {}).get("idlist", [])


def fetch_paper_details(paper_ids: List[str]) -> List[Dict]:
    """Fetch detailed information about papers given their IDs."""
    if not paper_ids:
        return []
    
    params = {
        "db": "pubmed",
        "id": ",".join(paper_ids),
        "retmode": "json"
    }
    response = requests.get(PUBMED_SUMMARY_URL, params=params)
    response.raise_for_status()
    data = response.json()
    return data.get("result", {}).values()


def filter_non_academic_authors(papers: List[Dict]) -> List[Dict]:
    """Identify non-academic authors and their company affiliations."""
    results = []
    for paper in papers:
        authors = paper.get("authors", [])
        non_academic_authors = []
        company_affiliations = []
        corresponding_email = None
        
        for author in authors:
            affiliation = author.get("affiliation", "")
            email = author.get("email", "")
            
            if affiliation and not any(keyword in affiliation.lower() for keyword in ["university", "college", "institute", "lab", "hospital"]):
                non_academic_authors.append(author.get("name", "Unknown"))
                company_affiliations.append(affiliation)
            
            if email:
                corresponding_email = email
        
        if non_academic_authors:
            results.append({
                "PubmedID": paper.get("uid", "Unknown"),
                "Title": paper.get("title", "No title"),
                "Publication Date": paper.get("pubdate", "Unknown"),
                "Non-academic Author(s)": ", ".join(non_academic_authors),
                "Company Affiliation(s)": ", ".join(company_affiliations),
                "Corresponding Author Email": corresponding_email or "N/A"
            })
    return results


def save_to_csv(papers: List[Dict], filename: str) -> None:
    """Save filtered papers to a CSV file."""
    if not papers:
        print("No results to save.")
        return
    
    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=papers[0].keys())
        writer.writeheader()
        writer.writerows(papers)
    print(f"Results saved to {filename}")


def main():
    parser = argparse.ArgumentParser(description="Fetch PubMed papers with non-academic authors.")
    parser.add_argument("query", type=str, help="PubMed search query.")
    parser.add_argument("-d", "--debug", action="store_true", help="Enable debug mode.")
    parser.add_argument("-f", "--file", type=str, help="Filename to save results as CSV.")
    
    args = parser.parse_args()
    
    if args.debug:
        print(f"Searching PubMed for: {args.query}")
    
    paper_ids = fetch_pubmed_papers(args.query)
    papers = fetch_paper_details(paper_ids)
    filtered_papers = filter_non_academic_authors(papers)
    
    if args.file:
        save_to_csv(filtered_papers, args.file)
    else:
        print(filtered_papers)

if __name__ == "__main__":
    main()
