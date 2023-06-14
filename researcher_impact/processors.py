from collections import defaultdict
import numpy as np
from pyalex import Concepts, Works
from researcher_impact.pyalex_utils import merge_pages, merge_sample
from researcher_impact.citations import get_citation_count_in_first_years
from researcher_impact.utils import dict_to_dataarray

class OpenAlexProcessor:
    def __init__(self):
        pass
    
    @classmethod
    def get_institution_author_data(cls, works, selected_institution_ids=None):
        institution_author_data = defaultdict(lambda: defaultdict(set))
        named_institution_author_data = defaultdict(lambda: defaultdict(set))
        for work in works:
            pub_year = work['publication_year']
            for authorship in work['authorships']:
                if authorship['author'].get('id') is None:
                    continue
                if len(authorship['institutions']) == 0:
                    continue
                author_id = authorship['author']['id']
                author_name = authorship['author']['display_name']
                for ins in authorship['institutions']:
                    if ins.get('id') is None:
                        continue
                    if selected_institution_ids is not None and ins['id'] not in selected_institution_ids:
                        continue
                    institution_author_data[ins['id']][pub_year].add(author_id)

                    ins_name = ins['display_name']
                    named_institution_author_data[ins_name][pub_year].add(author_name)
        return institution_author_data, named_institution_author_data
    
    @classmethod
    def get_institution_citation_distribution(cls, works, selected_institution_ids=None, citation_window_size=3):
        institution_cited_by_count = defaultdict(list)
        for work in works:
            citation_count = get_citation_count_in_first_years(work, years=citation_window_size)
            for authorship in work['authorships']:
                if len(authorship['institutions']) == 0:
                    continue
                for ins in authorship['institutions']:
                    if ins.get('id') is None:
                        continue
                    if selected_institution_ids is not None and ins['id'] not in selected_institution_ids:
                        continue
                    institution_cited_by_count[ins['id']].append(citation_count)

        for ins, cited_by_count in institution_cited_by_count.items():
            institution_cited_by_count[ins] = np.array(cited_by_count)
        
        return institution_cited_by_count
    
    @classmethod
    def get_institution_counts(cls, works, selected_institution_ids=None, citation_window_size=3):
        """
        For each year, count the citations for each work published in that year, within some window 
        of subsequent years. Also count the number of works published in each year.
        """
        institution_work_count = defaultdict(lambda: defaultdict(int))
        institution_cited_by_count = defaultdict(lambda: defaultdict(int))
        for work in works:
            pub_year = work['publication_year']
            citation_count = get_citation_count_in_first_years(work, years=citation_window_size)
            for authorship in work['authorships']:
                if len(authorship['institutions']) == 0:
                    continue
                for ins in authorship['institutions']:
                    if ins.get('id') is None:
                        continue
                    if selected_institution_ids is not None and ins['id'] not in selected_institution_ids:
                        continue
                    institution_cited_by_count[ins['id']][pub_year] += citation_count
                    institution_work_count[ins['id']][pub_year] += 1

        for ins, cited_by_count in institution_cited_by_count.items():
            institution_cited_by_count[ins] = dict_to_dataarray(cited_by_count, 'year')

        for ins, work_count in institution_work_count.items():
            institution_work_count[ins] = dict_to_dataarray(work_count, 'year')

        return institution_cited_by_count, institution_work_count
    
    @classmethod
    def get_institution_new_citations(cls, works, selected_institution_ids=None):
        """
        For each year, count the new citations (of works from any year).
        """
        # institution -> (year -> count)
        institution_cited_by_count = defaultdict(lambda: defaultdict(int))
        for work in works:
            counts_by_year = work['counts_by_year']
            for authorship in work['authorships']:
                if len(authorship['institutions']) == 0:
                    continue
                for ins in authorship['institutions']:
                    if ins.get('id') is None:
                        continue
                    if selected_institution_ids is not None and ins['id'] not in selected_institution_ids:
                        continue
                    for year_count in counts_by_year:
                        year = year_count['year']
                        cited_by_count = year_count['cited_by_count']
                        institution_cited_by_count[ins['id']][year] += cited_by_count

        for ins, cited_by_count in institution_cited_by_count.items():
            institution_cited_by_count[ins] = dict_to_dataarray(cited_by_count, 'year')

        return institution_cited_by_count

    @classmethod
    def get_institution_works(cls, institution_id, concept_ids=None):
        if concept_ids is None:
            works = merge_pages(
                Works() \
                    .filter(authorships={"institutions": {"id": institution_id}}) \
                    .paginate(n_max=100000)
            )
        else:
            works = merge_pages(
                Works() \
                    .filter(authorships={"institutions": {"id": institution_id}}) \
                    .filter(concepts={"id": concept_ids}) \
                    .paginate(n_max=100000)
            )
        return works

    @classmethod
    def get_concept_works(cls, concept, pub_year, pub_type, seed):           
        works = merge_sample(
            Works() \
                .filter(concepts={"id": concept['id']}) \
                .filter(publication_year=pub_year) \
                .filter(type=pub_type),
            sample_size=1000,
            seed=seed,
        )
        return works

    @classmethod
    def get_concepts(cls, work):
        return [Concepts()[c['id']] for c in work['concepts']]


class TestProcessor:
    def __init__(self):
        pass

    @classmethod
    def get_concepts(cls, work):
        return [
            {
                'display_name': 'Concept 1',
                'counts_by_year': [
                    {'year': 2009, 'works_count': 7829.60, 'cited_by_count': 141665.20},
                    
                ]
            },
        ]
