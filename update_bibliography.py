#!/usr/bin/env python3
import requests
from urllib.parse import urlencode
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np
import json
import os

def main():
    # Get API token from environment variable
    token = os.getenv('ADS_API_TOKEN')
    if not token:
        raise ValueError("ADS_API_TOKEN environment variable not set")
    
    # First author papers
    encoded_query_first = urlencode({"q": "first_author:peca, alessandro",
                               "fl": "title, author, date, citation_count, bibcode",
                               "rows": 200
                              })

    response_first = requests.get("https://api.adsabs.harvard.edu/v1/search/query?{}".format(encoded_query_first), 
                           headers={'Authorization': 'Bearer ' + token})

    # Format the response in a nicely readable format
    results_first = response_first.json()

    # Filter papers with specific bibcode patterns
    filtered_results_first = {
        **results_first,
        'response': {
            **results_first['response'],
            'docs': [
                paper for paper in results_first['response']['docs']
                if any(sub in paper['bibcode'] for sub in ['ApJ', 'arXiv', 'Univ', 'A&A', 'Galax'])
            ]
        }
    }

    # Save filtered results
    with open('data/ads_data_first.json', 'w') as f:
        json.dump(filtered_results_first, f, indent=4)

    # All papers
    encoded_query_all = urlencode({"q": "author:peca, alessandro",
                               "fl": "title, author, date, citation_count, bibcode",
                               "rows": 200
                              })

    response_all = requests.get("https://api.adsabs.harvard.edu/v1/search/query?{}".format(encoded_query_all), 
                           headers={'Authorization': 'Bearer ' + token})

    # Format the response in a nicely readable format
    results_all = response_all.json()

    # Filter papers with specific bibcode patterns
    filtered_results_all = {
        **results_all,
        'response': {
            **results_all['response'],
            'docs': [
                paper for paper in results_all['response']['docs']
                if any(sub in paper['bibcode'] for sub in ['ApJ', 'arXiv', 'Univ', 'A&A', 'Galax'])
            ]
        }
    }

    # Save filtered results
    with open('data/ads_data_all.json', 'w') as f:
        json.dump(filtered_results_all, f, indent=4)

    # Generate statistics
    data_per_year = {}
    citation_counts_all = []

    for j, results in enumerate([results_first, results_all]):
        filtered_papers = [
            paper for paper in results['response']['docs']
            if any(sub in paper['bibcode'] for sub in ['ApJ', 'arXiv', 'Univ', 'A&A', 'Galax'])
        ]

        papers = filtered_papers
        titles = [paper['title'][0] for paper in filtered_papers]
        authors = [paper['author'] for paper in filtered_papers]
        dates = [datetime.strptime(paper['date'], '%Y-%m-%dT%H:%M:%S%z').date() for paper in filtered_papers]
        citation_counts = [paper.get('citation_count', 0) for paper in filtered_papers]

        # Number of papers per year
        years = [date.year for date in dates]
        unique_years = sorted(set(years))

        for year in unique_years:
            if year not in data_per_year:
                data_per_year[year] = [0, 0]
            data_per_year[year][j] = years.count(year)
        citation_counts_all.append(citation_counts)

        print("Total papers:", len(papers))
        print("Total citations:", np.sum(citation_counts))

        # Compute the H-index
        citation_counts_sorted = sorted(citation_counts, reverse=True)
        h_index = 0
        for i, citations in enumerate(citation_counts_sorted):
            if citations >= i + 1:
                h_index = i + 1
            else:
                break

        print(f"H-index: {h_index}")

    print("Bibliography updated successfully!")

if __name__ == "__main__":
    main()