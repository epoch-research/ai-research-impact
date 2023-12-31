from collections import defaultdict
import numpy as np
import unittest

from research_impact.citations import get_bounded_citations
from research_impact.utils import dicts_to_dataarrays
from research_impact.test_works import TEST_WORKS


class OpenAlexProcessor:
    def __init__(
        self,
        works,
        selected_institution_ids=None,
        institution_aliases=None,
        citation_year_bound=3,
        deduplicate_authors_flag=True,
    ):
        self.works = works
        self.selected_institution_ids = selected_institution_ids
        self.institution_aliases = institution_aliases
        self.citation_year_bound = citation_year_bound
        self.deduplicate_authors_flag = deduplicate_authors_flag

        self.data = {}
        self.avg_coauthor_counts = None
        self.author_counts = None
        self.individual_bounded_citations = None
        self.bounded_citations = None
        self.work_counts = None
        self.author_id_to_name = defaultdict(  # keys: institution
            lambda: defaultdict(dict)  # keys: year
        )
        self.institution_id_to_name = {}

    def process_works(self):
        self.data["bounded_citations"] = defaultdict(  # keys: institution
            lambda: defaultdict(list)  # keys: year
        )
        self.data["coauthor_counts"] = defaultdict(  # keys: institution
            lambda: defaultdict(list)  # keys: year
        )
        self.data["authors_by_work"] = defaultdict(  # keys: institution
            lambda: defaultdict(list)  # keys: work ID
        )
        for work in self.works:
            self.process_authorships(work)
        self.deduplicate_authors()
        self.run_checks()

    def run_checks(self):
        for alias, year_data in self.data["authors"].items():
            for year, author_ids in year_data.items():
                assert len(author_ids) == len(self.data["author_names"][alias][year])

    def process_authorships(self, work):
        pub_year = work["publication_year"]
        bounded_citations = get_bounded_citations(
            work, year_bound=self.citation_year_bound
        )
        coauthor_count = len(work["authorships"])
        # For each work we'll need to check if citations are already added to a given
        # institution's list, because multiple authors may have the same affiliation
        bounded_citations_added = defaultdict(bool)
        for authorship in work["authorships"]:
            if len(authorship["institutions"]) == 0:
                continue
            self.process_institutions(
                work, authorship, pub_year, bounded_citations, bounded_citations_added, coauthor_count
            )

    def process_institutions(
        self, work, authorship, pub_year, bounded_citations, bounded_citations_added, coauthor_count
    ):
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
            if self.institution_aliases is None:
                alias = ins["id"]
            else:
                alias = self.institution_aliases.get(ins["id"], ins["id"])
            if not bounded_citations_added[alias]:
                self.data["bounded_citations"][alias][pub_year].append(
                    bounded_citations
                )
                self.institution_id_to_name[ins["id"]] = ins["display_name"]
                self.data["coauthor_counts"][alias][pub_year].append(coauthor_count)
                bounded_citations_added[alias] = True

            self.data["authors_by_work"][alias][work["id"]].append(author_id)
        
            # The below condition means we use the first id encountered for each author each year
            if self.author_id_to_name[alias][pub_year].get(author_id) is None:
                self.author_id_to_name[alias][pub_year][author_id] = author_name

    def deduplicate_authors(self):
        self.data["authors"] = defaultdict(  # keys: institution
            lambda: defaultdict(set)  # keys: year
        )
        self.data["author_names"] = defaultdict(  # keys: institution
            lambda: defaultdict(list)  # keys: year
        )
        for alias, year_data in self.author_id_to_name.items():
            for pub_year, author_id_to_name in year_data.items():
                unique_ids = set()
                unique_ids_list = []
                encountered_names_set = set()
                encountered_names_list = []
                for id_, name in author_id_to_name.items():
                    unique_ids_list.append(id_)
                    encountered_names_list.append(name)
                    if name not in encountered_names_set:
                        unique_ids.add(id_)
                        encountered_names_set.add(name)
                if self.deduplicate_authors_flag:
                    self.data["authors"][alias][pub_year] = unique_ids
                    self.data["author_names"][alias][pub_year] = list(encountered_names_set)
                else:
                    self.data["authors"][alias][pub_year] = unique_ids_list
                    self.data["author_names"][alias][pub_year] = encountered_names_list

    def get_author_data(self):
        return self.data["authors"]
    
    def get_authors_by_work(self):
        return self.data["authors_by_work"]

    def get_author_name_data(self):
        return self.data["author_names"]

    def get_author_counts(self):
        for ins in set(self.institution_aliases.values()):
            if ins not in self.data["authors"].keys():
                self.data["authors"][ins][2010] = set()  # placeholder
        
        self.author_counts = dicts_to_dataarrays(
            self.data["authors"], "year", val_fn=len
        )
        return self.author_counts
    
    def get_coauthor_counts(self):
        return self.data["coauthor_counts"]
    
    def get_avg_coauthor_counts(self):
        self.avg_coauthor_counts = dicts_to_dataarrays(
            self.data["coauthor_counts"], "year", val_fn=np.mean
        )
        return self.avg_coauthor_counts

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
        for ins in set(self.institution_aliases.values()):
            if ins not in self.data["bounded_citations"].keys():
                self.data["bounded_citations"][ins][2010] = []  # placeholder

        self.bounded_citations = dicts_to_dataarrays(
            self.data["bounded_citations"],
            "year",
            val_fn=sum,
        )
        return self.bounded_citations

    def get_work_counts(self):
        self.work_counts = dicts_to_dataarrays(
            self.data["bounded_citations"],
            "year",
            val_fn=len,
        )
        return self.work_counts


class TestOpenAlexProcessor(unittest.TestCase):

    def get_processor(self):
        processor = OpenAlexProcessor(TEST_WORKS)
        processor.process_works()
        return processor

    def test_get_author_data(self):
        processor = self.get_processor()
        author_data = processor.get_author_data()
        self.assertEqual(
            author_data["https://openalex.org/I4210164937"][2016], 
            {
                "https://openalex.org/A4344207660",
                "https://openalex.org/A4358260579",
                "https://openalex.org/A2119543935",
                "https://openalex.org/A4358569165",
            }
        )
        self.assertEqual(
            author_data["https://openalex.org/I16733864"][2011],
            {
                "https://openalex.org/A4334906277",
                "https://openalex.org/A4349829430",
            }
        )
        self.assertEqual(len(author_data["https://openalex.org/I4210164937"].keys()), 1)

    def test_get_author_counts(self):
        processor = self.get_processor()
        author_counts = processor.get_author_counts() 
        self.assertEqual(author_counts["https://openalex.org/I4210164937"].loc[2016], 4)

    def test_get_individual_bounded_citations(self):
        processor = self.get_processor()
        self.assertEqual(
            processor.get_individual_bounded_citations(),
            {
                "https://openalex.org/I4210164937": np.array([
                    732 + 3131 + 7952 + 15243,
                ]),
                "https://openalex.org/I16733864": np.array([
                    1599 + 2320 + 2695,
                ]),
            },
        )

    def test_get_bounded_citations(self):
        processor = self.get_processor()
        bounded_citations = processor.get_bounded_citations()
        self.assertEqual(
            bounded_citations["https://openalex.org/I4210164937"].loc[2016],
            732 + 3131 + 7952 + 15243,
        )

    def test_get_avg_coauthor_counts(self):
        processor = self.get_processor()
        avg_coauthor_counts = processor.get_avg_coauthor_counts()
        self.assertEqual(avg_coauthor_counts["https://openalex.org/I4210164937"].loc[2016], 4)

    def test_get_work_counts(self):
        processor = self.get_processor()
        work_counts = processor.get_work_counts()
        self.assertEqual(work_counts["https://openalex.org/I4210164937"].loc[2016], 1)
        self.assertEqual(work_counts["https://openalex.org/I16733864"].loc[2011], 1)

    def test_selected_institution_ids(self):
        selected_institution_ids = [
            "https://openalex.org/I4210164937",
        ]
        processor = OpenAlexProcessor(TEST_WORKS, selected_institution_ids=selected_institution_ids)
        processor.process_works()
        author_data = processor.get_author_data()
        self.assertIn("https://openalex.org/I4210164937", author_data.keys())
        self.assertEqual(len(author_data), 1)

    def test_institution_aliases(self):
        institution_aliases = {"https://openalex.org/I4210164937": "Microsoft"}
        processor = OpenAlexProcessor(TEST_WORKS, institution_aliases=institution_aliases)
        processor.process_works()
        author_data = processor.get_author_data()
        self.assertIn("Microsoft", author_data.keys())
        assert "https://openalex.org/I16733864" in author_data.keys()


if __name__ == "__main__":
    unittest.main()
