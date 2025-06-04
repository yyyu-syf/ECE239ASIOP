#!/usr/bin/env python3
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib_venn import venn2
from censys.search import CensysHosts
import math

# 1. Load LLM‐generated hosts
llm_df = pd.read_csv('data/raw/llm_hosts.csv', header=None, names=['host'])
llm_hosts = set(llm_df['host'].str.lower())

# 2. Define manual keywords and build a full-text query
noprescriptionlist = [
    "no prescription required",
    "no prescription needed",
    "no rx needed",
    "no rx required",
    "no doctor visit",
]
# Expanded list of controlled substances (generic names and some popular ones)
CONTROLLED_SUBSTANCES = [
    "xanax",
    "valium",
    "tramadol",
    "oxycodone",
    "hydrocodone",
    "percocet",
    "adderall",
    "fentanyl",
    "morphine",
    "codeine",
    "hydromorphone",
    "oxymorphone",
    "dilaudid",
    "suboxone",
    "buprenorphine",
    "oxicontin",
    "vicodin",
    "roxicodone"
]

# Expanded list of brand names for common drugs
BRAND_NAMES = [
    "viagra",
    "cialis",
    "levitra",
    "kamagra",       # often sold illegally online
    "sildenafil",    # generic Viagra
    "tadalafil",     # generic Cialis
    "vardenafil",    # another ED medication
    "stendra"
]

noprescription = " OR ".join([f'"{k}"' for k in noprescriptionlist])
meds = " OR ".join([f'"{k}"' for k in (BRAND_NAMES + CONTROLLED_SUBSTANCES)])
manual_query = f"({noprescription}) OR ({meds})"



# 3. Fetch manual hosts from Censys
api = CensysHosts()
manual_hosts = set()
for page in api.search(manual_query, per_page=100, pages=math.ceil(2000/100)):
    page = page if isinstance(page, list) else [page]
    for hit in page:
        name = hit.get('name')
        if name:
            manual_hosts.add(name.lower())
        else:
            ip = hit.get('ip')
            if ip:
                manual_hosts.add(ip)

# 4. Compute overlap
only_manual = manual_hosts - llm_hosts
only_llm    = llm_hosts - manual_hosts
both        = manual_hosts & llm_hosts

# 5. Venn diagram
plt.figure(figsize=(6,6))
venn2(subsets=(len(only_manual), len(only_llm), len(both)),
      set_labels=('Manual Only', 'LLM Only', 'Both'))
plt.title('Manual vs. LLM Censys Query Overlap')
plt.tight_layout()
plt.show()

# 6. Bar chart
plt.figure(figsize=(8,5))
categories = ['Manual Only', 'Overlap (Both)', 'LLM Only']
values = [len(only_manual), len(both), len(only_llm)]
bars = plt.bar(categories, values)
plt.ylabel('Number of Hosts')
plt.title('Coverage: Manual vs. LLM Queries')
for bar in bars:
    h = bar.get_height()
    plt.text(bar.get_x() + bar.get_width()/2, h + 2, f"{h}", ha='center')
plt.tight_layout()
plt.show()

# 7. Save combined overlap CSV in long format
rows = []
for host in sorted(only_manual):
    rows.append({'host': host, 'category': 'only_manual'})
for host in sorted(only_llm):
    rows.append({'host': host, 'category': 'only_llm'})
for host in sorted(both):
    rows.append({'host': host, 'category': 'both'})

result_df = pd.DataFrame(rows, columns=['host', 'category'])
result_df.to_csv('manual_llm_overlap.csv', index=False)
print(f"Saved {len(result_df)} records to manual_llm_overlap.csv (categories: only_manual, only_llm, both)")