from collections import defaultdict, OrderedDict
import xarray as xr

from researcher_impact.pyalex_utils import get_entity_name

def calculate_institution_author_count(institution_author_data):
    institution_author_count = {}
    for institution, author_series in institution_author_data.items():
        author_counts = OrderedDict()
        for year, authors in sorted(author_series.items()):
            author_counts[year] = len(authors)
        author_count_array = xr.DataArray(
            list(author_counts.values()),
            dims=("year",),
            coords={"year": list(author_counts.keys()),},
        )
        institution_author_count[institution] = author_count_array
    return institution_author_count

def name_institution_author_data(institution_author_data):
    named_institution_author_data = defaultdict(lambda: defaultdict(set))
    for ins, author_data in institution_author_data.items():
        ins_name = get_entity_name(ins)
        for year, authors in author_data.items():
            author_names = {get_entity_name(a) for a in authors}
            named_institution_author_data[ins_name][year] = author_names
    return named_institution_author_data

# Test calculate_institution_author_count
def test_calculate_institution_author_count():
    institution_author_data = {
        'Google': OrderedDict([
            (2014, ['Alice',]),
            (2015, ['Alice', 'Bob',]),
            (2016, ['Bob', 'Xin',]),
        ]),
        'OpenAI': OrderedDict([
            (2014, []),
            (2015, ['Lakeith',]),
            (2016, ['Lakeith', 'Anita', 'Wenjie']),
        ]),
    }
    institution_author_count = calculate_institution_author_count(institution_author_data)
    assert institution_author_count["Google"].values.tolist() == [1, 2, 2]
    assert institution_author_count["OpenAI"].values.tolist() == [0, 1, 3]

if __name__ == "__main__":
    test_calculate_institution_author_count()
