def get_citation_count_in_first_years(work, years=3):
    pub_year = work['publication_year']
    counts_by_year = work['counts_by_year']
    total_count = 0
    for year_count in counts_by_year:
        if year_count['year'] >= pub_year and year_count['year'] <= pub_year + years:
            total_count += year_count['cited_by_count']
    return total_count
