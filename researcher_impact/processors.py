from collections import defaultdict
import numpy as np

from researcher_impact.citations import get_citation_count_in_first_years
from researcher_impact.utils import dicts_to_dataarrays


class OpenAlexProcessor:
    def __init__(
        self,
        works,
        selected_institution_ids,
        institution_aliases,
        citation_year_bound=3,
    ):
        self.works = works
        self.selected_institution_ids = selected_institution_ids
        self.institution_aliases = institution_aliases
        self.citation_year_bound = citation_year_bound

        self.data = None
        self.author_counts = None
        self.individual_bounded_citations = None
        self.bounded_citations = None
        self.work_counts = None

    def process_works(self):
        self.data = defaultdict(  # keys: data type
            lambda: defaultdict(  # keys: institution
                lambda: defaultdict(list)  # keys: year
            )
        )
        for work in self.works:
            self.process_authorships(work)

    def process_authorships(self, work):
        pub_year = work["publication_year"]
        bounded_citations = get_citation_count_in_first_years(
            work, years=self.citation_year_bound
        )
        self.data["bounded_citations"][alias][pub_year].append(bounded_citations)
        for authorship in work["authorships"]:
            if len(authorship["institutions"]) == 0:
                continue
            self.process_institutions(authorship, pub_year, bounded_citations)

    def process_institutions(self, authorship, pub_year, bounded_citations):
        author_id = authorship["author"]["id"]
        author_name = authorship["author"]["display_name"]
        for ins in authorship["institutions"]:
            if ins.get("id") is None:
                continue
            if not (
                self.selected_institution_ids is None
                or ins["id"] in self.selected_institution_ids
            ):
                continue
            alias = self.institution_aliases[ins["id"]]
            self.data["authors"][alias][pub_year].append(author_id)
            self.data["author_names"][alias][pub_year].append(author_name)

    def get_author_data(self):
        return self.data["authors"]

    def get_author_name_data(self):
        return self.data["author_names"]
    
    def get_author_counts(self):
        self.author_counts = dicts_to_dataarrays(
            self.data["authors"], 'year', val_fn=len
        )
        return self.author_counts

    def get_individual_bounded_citations(self):
        merged_bounded_citations = defaultdict(list)
        for alias, year_data in self.data["bounded_citations"].items():
            for bounded_citations in year_data.values():
                merged_bounded_citations[alias].extend(bounded_citations)
        self.individual_bounded_citations = {
            k: np.array(v) for k, v in merged_bounded_citations.items()
        }
        return self.individual_bounded_citations

    def get_bounded_citations(self):
        self.bounded_citations = dicts_to_dataarrays(
            self.data["bounded_citations"], "year", val_fn=sum,
        )
        return self.bounded_citations

    def get_work_counts(self):
        self.work_counts = dicts_to_dataarrays(
            self.data["bounded_citations"], "year", val_fn=len,
        )
        return self.work_counts


class TestProcessor:
    def __init__(self):
        pass

    @classmethod
    def get_concepts(cls, work):
        return [
            {
                "display_name": "Concept 1",
                "counts_by_year": [
                    {"year": 2009, "works_count": 7829.60, "cited_by_count": 141665.20},
                ],
            },
        ]
