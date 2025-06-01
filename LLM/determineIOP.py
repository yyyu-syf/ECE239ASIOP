#!/usr/bin/env python3
"""
classify_hosts.py

1. Reads 'candidates.csv' with columns: host,category
2. Uses Censys Hosts API to fetch HTTP title and body snippet
3. Uses OpenAI (v1.x) client.chat.completions.create to classify each as
   an illicit pharmacy
4. Saves results to 'classified_hosts.csv'
5. Plots a bar chart of classification counts by original category
"""
from bs4 import BeautifulSoup


import os
import math
import csv
import json
import pandas as pd
import matplotlib.pyplot as plt
from censys.search import CensysHosts
from openai import OpenAI  # new import for v1.x SDK  [oai_citation:0‡Stack Overflow](https://stackoverflow.com/questions/77505030/openai-api-error-you-tried-to-access-openai-chatcompletion-but-this-is-no-lon?utm_source=chatgpt.com)
from matplotlib_venn import venn2

# —––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––—
#  Configuration
# —––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––—
openai_api_key = os.getenv("OPENAI_API_KEY")
CENSYS_API_ID  = os.getenv("CENSYS_API_ID")
CENSYS_API_SECRET = os.getenv("CENSYS_API_SECRET")

# Initialize the new client-based OpenAI SDK  [oai_citation:1‡Stack Overflow](https://stackoverflow.com/questions/77505030/openai-api-error-you-tried-to-access-openai-chatcompletion-but-this-is-no-lon?utm_source=chatgpt.com)
client = OpenAI(api_key=openai_api_key)

# —––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––—
#  1. Load candidate hosts
# —––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––—
df = pd.read_csv("manual_llm_overlap.csv")  # expects columns: host,category
df["html_title"]   = ""
df["body_snippet"] = ""
df["is_pharmacy"]  = False
df["confidence"]   = 0.0
df["reason"]       = ""

# —––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––—
#  2. Initialize Censys client
# —––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––—
api = CensysHosts(api_id=CENSYS_API_ID, api_secret=CENSYS_API_SECRET)
system_msg = {
  "role": "system",
  "content": (
    "You are a JSON‑only API. ALL responses must be a single valid JSON object—"
    "do not wrap it in markdown, code fences, or any additional text."
  )
}
# —––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––—
#  3. Fetch HTTP details and classify with OpenAI
# —––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––—
    # Determine starting position based on host match
start_host = ''
if start_host in df['host'].values:
    start_pos = df.index[df['host'] == start_host][0]
else:
    start_pos = 0
# Iterate from the matching host onward
for idx in df.index[df.index >= start_pos]:
    row = df.loc[idx]
    host = row["host"]
    try:
        rec = api.view(host)
    except Exception as e:
        print(f"[Censys ERROR] {host}: {e}")
        continue

    # Extract HTTP title & snippet
    title = ""
    body  = ""
    for svc in rec.get("services", []):
        http = svc.get("http")
        if http and http.get("response"):
            resp = http["response"]
            title = resp.get("html_title", "") or ""
            body  = resp.get("body", "") or ""
            break

    df.at[idx, "html_title"]   = title
    soup = BeautifulSoup(body, "html.parser")
    text = soup.get_text(separator="\n", strip=True)
    df.at[idx, "body_snippet"] = text[:3000]

    # Build classification prompt
    user_msg = {
      "role": "user",
      "content": (
        "Classify this site as Illicit Online Pharmacy or not using exactly this JSON schema:\n"
        "{\n"
        '  "is_pharmacy": boolean,\n'
        '  "confidence": number,\n'
        '  "reason": string\n'
        "}\n\n"
        f"Host: {host}\nTitle: {title}\nSnippet: {text[:3000]}"
      )
    }
    # Use the new client.chat.completions.create method  [oai_citation:2‡Stack Overflow](https://stackoverflow.com/questions/77505030/openai-api-error-you-tried-to-access-openai-chatcompletion-but-this-is-no-lon?utm_source=chatgpt.com)
    try:
        resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[system_msg, user_msg],
        temperature=0.0,
        max_tokens=150,
        # Optionally enable JSON mode for supported models:
        # response_format={"type":"json_object"},
        logit_bias={123: 10},
        )

        content = resp.choices[0].message.content.strip()
        print(f"[OpenAI RAW] {host}: {repr(content[:200])}")

        try:
            result = json.loads(content)
        except json.JSONDecodeError:
            print(f"[JSON PARSE ERROR] {host}: {repr(content)}")
            result = {"is_pharmacy": False, "confidence": 0.0, "reason": "invalid JSON"}

        df.at[idx, "is_pharmacy"] = result.get("is_pharmacy", False)
        df.at[idx, "confidence"]  = result.get("confidence", 0.0)
        df.at[idx, "reason"]      = result.get("reason", "")
    except Exception as e:
        print(f"[OpenAI ERROR] {host}: {e}")
        # Save intermediate results after classifying this host
        # df.to_csv("classified_hosts.csv", index=False)
    # break
    # Save intermediate results after each host, regardless of success or error
    df.to_csv(
        "classified_hosts2.csv",
        index=False,
        quoting=csv.QUOTE_ALL,
        escapechar="\\"
    )
# —––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––—
#  4. Save results
# —––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––—
# df.to_csv("classified_hosts.csv", index=False)
print("Saved classified_hosts.csv")

# —––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––—
#  5. Plot classification counts
# —––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––—
# Pivot counts by category and boolean classification
pivot = df.pivot_table(
    index="category",
    columns="is_pharmacy",
    aggfunc="size",
    fill_value=0
)

# Rename boolean columns to descriptive names
pivot = pivot.rename(columns={False: "not_pharmacy", True: "pharmacy"})

# Ensure both columns exist
if "not_pharmacy" not in pivot.columns:
    pivot["not_pharmacy"] = 0
if "pharmacy" not in pivot.columns:
    pivot["pharmacy"] = 0

pivot[["not_pharmacy", "pharmacy"]].plot(
    kind="bar",
    stacked=False,
    figsize=(8,5),
)
plt.title("Illicit Pharmacy Classification by Category")
plt.ylabel("Number of Hosts")
plt.xticks(rotation=0)
plt.legend(["Not Pharmacy", "Pharmacy"], title="")
plt.tight_layout()
plt.show()

# Venn diagram: Candidates vs. Real IOP
total = len(df)
real = df['is_pharmacy'].sum()
not_real = total - real


plt.figure(figsize=(6,6))
# subsets: (only candidates, only IOP, intersection)
venn2(subsets=(not_real, 0, real),
      set_labels=('Candidates', 'Real IOP'))
plt.title('Proportion of Candidates Classified as Real IOP')
plt.tight_layout()
plt.show()

# Percentage of real IOP by category
percent_manual = df[df['category'] == 'only_manual']['is_pharmacy'].mean() * 100
percent_llm    = df[df['category'] == 'only_llm']['is_pharmacy'].mean() * 100
percent_both   = df[df['category'] == 'both']['is_pharmacy'].mean() * 100

plt.figure(figsize=(6,4))
categories = ['Manual Only', 'LLM Only', 'Both']
values = [percent_manual, percent_llm, percent_both]
bars = plt.bar(categories, values)
plt.ylabel('Percentage of Real IOP (%)')
plt.title('Real IOP Percentage by Category')
plt.ylim(0, 100)
for bar, v in zip(bars, values):
    plt.text(bar.get_x() + bar.get_width()/2, v + 1, f'{v:.1f}%', ha='center')
plt.tight_layout()
plt.show()