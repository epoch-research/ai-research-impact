from collections import defaultdict
from pyalex import Works
from researcher_impact.pyalex_utils import merge_pages, merge_sample

class OpenAlexProcessor:
    def __init__(self):
        pass
    
    @classmethod
    def get_institution_author_data(cls, works):
        institution_author_data = defaultdict(lambda: defaultdict(set))
        named_institution_author_data = defaultdict(lambda: defaultdict(set))
        for work in works:
            pub_year = work['publication_year']
            for authorship in work['authorships']:
                if len(authorship['institutions']) > 0:
                    author_id = authorship['author']['id']
                    author_name = authorship['author']['display_name']
                    for ins in authorship['institutions']:
                        if ins.get('id') is None:
                            continue
                        institution_author_data[ins['id']][pub_year].add(author_id)

                        ins_name = ins['display_name']
                        named_institution_author_data[ins_name][pub_year].add(author_name)
        return institution_author_data, named_institution_author_data

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
