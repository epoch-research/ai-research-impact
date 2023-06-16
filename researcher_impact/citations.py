import numpy as np

def get_citation_count_in_first_years(work, years=3):
    pub_year = work['publication_year']
    counts_by_year = work['counts_by_year']
    total_count = 0
    for year_count in counts_by_year:
        if year_count['year'] >= pub_year and year_count['year'] <= pub_year + years:
            total_count += year_count['cited_by_count']
    return total_count

def get_expected_citation_count(work, processor, seed):
    # Get concepts of the work
    # TODO consider using concept levels to narrow down the number of concepts
    concepts = [concept for concept in work['concepts'] if concept['level'] == 1]
    pub_year = work['publication_year']
    pub_type = work['type']
    expected_citations = np.zeros(len(concepts))
    for i, concept in enumerate(concepts):
        print(f"Concept: {concept['display_name']} ({i+1} of {len(concepts)})")
        # Works in database published in same year, of same type, and with the same concept as given work
        # TODO use downloaded data instead of querying?
        concept_works = processor.get_concept_works(concept, pub_year, pub_type, seed)
        # Total citations received in pub year plus 3 years by all works in the database published
        # in same year, of same type, and with the same concept
        total_citations = sum(get_citation_count_in_first_years(work) for work in concept_works)
        expected_citations[i] = total_citations / len(concept_works)
        print(f"Expected citations from {len(concept_works)} works: {expected_citations[i]}")
    # 3. For publications indexed in multiple categories, use harmonic mean to compute expected
    # number of citations
    if np.prod(expected_citations) > 0:
        expected_citation_count = len(expected_citations) / np.sum(1 / expected_citations)
    else:
        expected_citation_count = 1  # avoid division by zero
    print(f"Overall expected citation count: {expected_citation_count}")
    return expected_citation_count

def fwci(works, processor, seed=0):
    # Get all publications for entity
    work_citation_ratios = np.zeros(len(works))
    for i, work in enumerate(works):
        print(f"Work: {work['display_name']} ({i+1} of {len(works)})")
        # 1. Compute number of citations received by publications in entity.
        citation_count = get_citation_count_in_first_years(work)
        print(f"Citation count: {citation_count}")
        # Compute expected number of citations received by similar publications.
        expected_citation_count = get_expected_citation_count(work, processor, seed)
        # Compute ratio of actual to expected citations for each publication
        work_citation_ratios[i] = citation_count / expected_citation_count
    # Take arithmetic mean of the ratios to calculate Field-Weighted Citation Impact for this entity
    fwci_entity = np.mean(work_citation_ratios)
    return fwci_entity
