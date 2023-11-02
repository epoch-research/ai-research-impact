import numpy as np
from pyalex import Authors, Institutions
from tqdm import tqdm, trange

TYPE_TO_PYALEX_CLASS = {
  'A': Authors,
  'I': Institutions,
}

def get_id_from_url(id_url):
    return id_url.rsplit('/', 1)[-1]

def get_entity_name(url):
    entity_id = get_id_from_url(url)
    openalex_class = TYPE_TO_PYALEX_CLASS[entity_id[0]]
    return openalex_class()[entity_id]['display_name']

def merge_pages(pager):
    """
    I'm not sure how to get more than 200 items at once other than to create
    a pager and then merge the pages.
    """
    items = []
    for page in tqdm(pager, unit="page"):
        items.extend(page)
    return items

def merge_sample(query, sample_size=1000, seed=None):
    sampler = query.sample(sample_size, seed=seed)
    items = []
    for i in trange(int(np.ceil(sample_size / 200)) + 1):  # 200 is the max page size
        page = sampler.get(per_page=200, page=i+1)
        items.extend(page)
    return items
