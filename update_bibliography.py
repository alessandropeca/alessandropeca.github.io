#!/usr/bin/env python3
import requests
from urllib.parse import urlencode
from datetime import datetime
import numpy as np
import json
import re
import os

JOURNAL_FILTERS = ['ApJ', 'arXiv', 'Univ', 'A&A', 'Galax']
SITE_URL = "https://alessandropeca.com/"
INDEX_FILE = "index.html"


def fetch_ads(query, token):
    encoded_query = urlencode({"q": query,
                               "fl": "title, author, date, citation_count, bibcode",
                               "rows": 200
                               })
    response = requests.get("https://api.adsabs.harvard.edu/v1/search/query?{}".format(encoded_query),
                            headers={'Authorization': 'Bearer ' + token})
    results = response.json()

    # Filter papers with specific bibcode patterns
    return {
        **results,
        'response': {
            **results['response'],
            'docs': [
                paper for paper in results['response']['docs']
                if any(sub in paper['bibcode'] for sub in JOURNAL_FILTERS)
            ]
        }
    }


def parse_date(datestr):
    return datetime.strptime(datestr, '%Y-%m-%dT%H:%M:%S%z')


def render_publications_html(docs):
    """Render the publication list as static HTML (same layout the old JS produced)."""
    docs = sorted(docs, key=lambda d: parse_date(d['date']), reverse=True)
    items = []
    for doc in docs:
        title = doc['title'][0]  # may contain ADS markup like <SUP>, rendered as HTML
        authors = ', '.join(doc['author'])
        date = parse_date(doc['date']).strftime('%b %Y')
        citations = doc.get('citation_count', 0)
        link = "https://ui.adsabs.harvard.edu/abs/{}".format(doc['bibcode'])
        items.append(
            '<li><strong>{}</strong> by {} ({}) - Citations: {} - '
            '<a href="{}" target="_blank">ADS Link</a></li>'.format(title, authors, date, citations, link)
        )
    return '<ul>\n' + '\n'.join(items) + '\n</ul>'


def render_jsonld(first_docs):
    """Build schema.org JSON-LD (Person + first-author ScholarlyArticles) for LLM/search findability."""
    strip_tags = re.compile(r'<[^>]+>')
    articles = []
    for doc in sorted(first_docs, key=lambda d: parse_date(d['date']), reverse=True):
        articles.append({
            "@type": "ScholarlyArticle",
            "headline": strip_tags.sub('', doc['title'][0]),
            "author": [{"@type": "Person", "name": name} for name in doc['author']],
            "datePublished": parse_date(doc['date']).strftime('%Y-%m-%d'),
            "identifier": doc['bibcode'],
            "url": "https://ui.adsabs.harvard.edu/abs/{}".format(doc['bibcode']),
        })

    data = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "Person",
                "@id": SITE_URL + "#person",
                "name": "Alessandro Peca",
                "jobTitle": "FONDECYT Postdoctoral Fellow",
                "affiliation": {
                    "@type": "Organization",
                    "name": "Universidad Diego Portales",
                    "address": {
                        "@type": "PostalAddress",
                        "addressLocality": "Santiago",
                        "addressCountry": "Chile"
                    }
                },
                "description": "Astrophysicist studying active galactic nuclei (AGN), "
                               "X-ray surveys, obscured AGN, and AGN/galaxy co-evolution.",
                "url": SITE_URL,
                "email": "peca.alessandro@gmail.com",
                "sameAs": [
                    "https://orcid.org/0000-0003-2196-3298",
                    "https://scholar.google.com/citations?user=Dnr-lfUAAAAJ",
                    "https://github.com/alessandropeca",
                    "https://www.linkedin.com/in/alessandro-peca-188949b8/"
                ]
            }
        ] + articles
    }
    return ('<script type="application/ld+json">\n'
            + json.dumps(data, indent=2, ensure_ascii=False)
            + '\n</script>')


def inject_between_markers(html, marker, content):
    """Replace everything between <!-- marker:START --> and <!-- marker:END -->."""
    start = '<!-- {}:START -->'.format(marker)
    end = '<!-- {}:END -->'.format(marker)
    pre, rest = html.split(start, 1)
    _, post = rest.split(end, 1)
    return pre + start + '\n' + content + '\n' + end + post


def update_index(results_first, results_all):
    with open(INDEX_FILE) as f:
        html = f.read()

    html = inject_between_markers(html, 'BIB-FIRST', render_publications_html(results_first['response']['docs']))
    html = inject_between_markers(html, 'BIB-ALL', render_publications_html(results_all['response']['docs']))
    html = inject_between_markers(html, 'JSONLD', render_jsonld(results_first['response']['docs']))

    with open(INDEX_FILE, 'w') as f:
        f.write(html)
    print("index.html updated with static publication lists and JSON-LD.")


def print_stats(results_first, results_all):
    for results in [results_first, results_all]:
        docs = results['response']['docs']
        citation_counts = [paper.get('citation_count', 0) for paper in docs]

        print("Total papers:", len(docs))
        print("Total citations:", np.sum(citation_counts))

        # Compute the H-index
        citation_counts_sorted = sorted(citation_counts, reverse=True)
        h_index = 0
        for i, citations in enumerate(citation_counts_sorted):
            if citations >= i + 1:
                h_index = i + 1
            else:
                break
        print("H-index: {}".format(h_index))


def main():
    token = os.getenv('ADS_API_TOKEN')

    if token:
        results_first = fetch_ads("first_author:peca, alessandro", token)
        with open('data/ads_data_first.json', 'w') as f:
            json.dump(results_first, f, indent=4)

        results_all = fetch_ads("author:peca, alessandro", token)
        with open('data/ads_data_all.json', 'w') as f:
            json.dump(results_all, f, indent=4)
    else:
        # No token (e.g. local run): re-render index.html from the last fetched data
        print("ADS_API_TOKEN not set - rendering from existing data files.")
        with open('data/ads_data_first.json') as f:
            results_first = json.load(f)
        with open('data/ads_data_all.json') as f:
            results_all = json.load(f)

    update_index(results_first, results_all)
    print_stats(results_first, results_all)
    print("Bibliography updated successfully!")


if __name__ == "__main__":
    main()
