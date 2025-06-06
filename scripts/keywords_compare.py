# Your Censys API credentials
API_ID = "YOUR_CENSYS_API_ID"
API_SECRET = "YOUR_CENSYS_API_SECRET"

import os
import time
from collections import defaultdict
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import seaborn as sns
import pandas as pd
from censys.search import CensysHosts
from censys.common.exceptions import CensysException

# Init Censys API
hosts = CensysHosts(api_id=API_ID, api_secret=API_SECRET)

openai_keywords = [
  "viagra",
  "v1agra",
  "xanax",
  "x@nax",
  "tramadol",
  "tr@m@dol",
  "valium",
  "adderall",
  "ambien",
  "oxycontin",
  "oxycodone",
  "percocet",
  "hydrocodone",
  "soma",
  "phentermine",
  "clonazepam",
  "cheap meds",
  "cheap pills",
  "buy without prescription",
  "no prescription",
  "rx online",
  "online rx",
  "fastmeds",
  "medstore",
  "onlinedrugs",
  "generic pharmacy",
  "canada pharmacy",
  "canadian meds",
  "intl pharmacy",
  "international pharmacy",
  "pharma express",
  "pharma ship",
  "overnight delivery",
  "discreet shipping",
  "bulk discount",
  "bitcoin accepted",
  "pay with crypto",
  "cash only",
  "free pills",
  "bonus pills",
  "fda approved",
  "usa pharmacy",
  "epharmacy",
  "drugstore online",
  "rxdiscount",
  "securemeds",
  "24hr pharmacy",
  "online medz",
  "fast shipping",
  "prescription free",
  "medznow",
  "cheaprx",
  "rxforless",
  "order without script",
  "viagra without rx",
  "controlled meds",
  "legal highs",
  "pain meds online",
  "buy painkillers",
  "order tramadol",
  "overnight xanax",
  "discount drugs",
  "no script",
  "mail order pharmacy",
  "get meds fast",
  "medication no rx",
  "healthpharm",
  "shoprx",
  "yourrxstore",
  "meddelivery",
  "viagra from canada"
]
gemini_keywords= [
  "v1agra",
  "x@nax",
  "tramadol hcl",
  "rx",
  "pharma",
  "drugstore",
  "medsonline",
  "no prescription",
  "cheap pills",
  "fda approved without rx",
  "bitcoin accepted",
  "overnight delivery",
  "bulk discount",
  "canada pharmacy",
  "international meds",
  "generic viagra",
  "buy xanax online",
  "order tramadol",
  "online pharmacy",
  "canadian pharmacy",
  "global pharmacy",
  "discount drugs",
  "free shipping worldwide",
  "secure payment",
  "fast delivery",
  "no prior prescription",
  "offshore pharmacy",
  "mexican pharmacy",
  "indian pharmacy",
  "russian pharmacy",
  "uk meds",
  "europe pharmacy",
  "buy meds online",
  "meds for sale",
  "erectile dysfunction pills",
  "pain relief meds",
  "anxiety meds",
  "sleep aids",
  "weight loss pills",
  "steroids online",
  "injectable meds",
  "c.o.d.",
  "western union",
  "moneygram",
  "e-check",
  "wire transfer",
  "next day delivery",
  "express shipping",
  "worldwide shipping",
  "best prices online",
  "lowest prices",
  "save up to 90%",
  "trusted online pharmacy",
  "reliable meds",
  "quality drugs",
  "fda approved india",
  "made in india",
  "shipped from canada",
  "usa direct",
  "united states pharmacy"
]
claude_keywords = [
  "viagra",
  "v1agra", 
  "vi@gra",
  "xanax",
  "x@nax",
  "xana x",
  "tramadol",
  "tramad0l",
  "codeine",
  "c0deine", 
  "phentermine",
  "phentermin3",
  "ambien",
  "ambi3n",
  "adderall",
  "add3rall",
  "oxycodone",
  "0xycodone",
  "hydrocodone",
  "hydr0codone",
  "valium",
  "v@lium",
  "ativan",
  "klonopin",
  "modafinil",
  "modalert",
  "soma",
  "diazepam",
  "clonazepam",
  "phentermine",
  "rx",
  "rx-meds",
  "meds-rx",
  "pharma",
  "pharmacy",
  "pharm@cy",
  "drugstore",
  "drug-store",
  "medsonline",
  "meds-online",
  "online-meds",
  "onlinepharmacy",
  "online-pharmacy",
  "pill-shop",
  "pill shop",
  "medicine-shop",
  "med-shop",
  "noprescription",
  "no-prescription",
  "no prescription",
  "noprescript",
  "noscript",
  "cheap pills",
  "cheap-pills",
  "cheapmeds",
  "cheap-meds",
  "bestprice",
  "best-price",
  "lowprice",
  "low-price",
  "discount-meds",
  "discount pills",
  "buy-pills",
  "buypills",
  "order-online",
  "order online",
  "fda-approved",
  "fda approved",
  "approved-meds",
  "approved pharmacy",
  "bitcoin",
  "bitcoin-accepted",
  "crypto-accepted",
  "cryptocurrency",
  "overnight delivery",
  "overnight-delivery",
  "fast-delivery",
  "express-delivery",
  "express delivery",
  "bulk-discount",
  "bulk discount",
  "wholesale",
  "bulk-order",
  "bulk order",
  "24/7",
  "24-7",
  "24hour",
  "24-hour",
  "canada pharmacy",
  "canada-pharmacy",
  "canadian-pharmacy",
  "canadian pharmacy",
  "international-meds",
  "international meds",
  "international-pharmacy",
  "world-pharmacy",
  "global-pharmacy",
  "worldwide-shipping",
  "worldwide shipping",
  "usa-ship",
  "us-shipping",
  "us delivery",
  "allday",
  "anytime",
  "instant",
  "fastmeds",
  "quickmeds",
  "rapidmeds",
  "speedy-meds",
  "bestmeds",
  "topmeds",
  "mymeds",
  "yourmeds",
  "easymeds",
  "simplemeds"
]

llm_keywords = openai_keywords + gemini_keywords + claude_keywords
llm_keywords = list(set(openai_keywords))
# # LLM-suggested keywords
# llm_keywords = [
#     # 购买药品相关（模糊表达）
#     "no prescription needed",
#     "cheap meds online",
#     "buy meds direct",
#     "refill meds online",
#     "get meds delivered",
#     "online health store",
#     "order medication safely",
#     "purchase health products",
#     "pharma site online",
#     "shop drugs anonymously",

#     # 药房话术/营销用语
#     "trusted online pharmacy",
#     "secure checkout pharmacy",
#     "affordable health pills",
#     "fast delivery pharmacy",
#     "discreet medical shipping",
#     "global drug shipping",
#     "pharmacy discounts",
#     "save on prescriptions",
#     "express pharmacy deal",
#     "low price prescriptions",

#     # 模糊药品指代（不出现具体药名）
#     "performance enhancers online",
#     "mental focus pills",
#     "sleep aid without script",
#     "pain relief pills online",
#     "weight loss supplement pharmacy",
#     "anti-anxiety tablets online",
#     "stress relief medication no script",

#     # 用户行为类表达
#     "how to buy meds online",
#     "best online medicine website",
#     "can i order drugs online",
#     "where to get meds shipped"
# ]

# # Baseline keyword set
baseline_keywords = [
    "online pharmacy", "buy medicine online", "order drugs", "cheap meds", "no prescription required", "no prescription needed", "without prescription", "no rx needed", "no rx required", "no doctor visit"
]

# === Step 3: Crawl and Store Content ===
keyword_to_sites = defaultdict(dict)
def _handle_single_result(keyword, result):
    ip = result.get("ip")
    if not ip:
        return
    for service in result.get("services", []):
        if service.get("service_name") == "HTTP":
            title = service.get("http", {}).get("response", {}).get("html_title", "")
            body = service.get("http", {}).get("response", {}).get("body", "")
            keyword_to_sites[keyword][ip] = {"title": title, "body": body}
def run_query_with_content(keyword, max_results=100):
    query = f'services.http.response.body: "{keyword}"'
    try:
        search_results = hosts.search(query=query, per_page=100, max_records=max_results)

        for result in search_results:
            # 如果 result 是列表（某些版本 SDK 有这种行为）
            if isinstance(result, list):
                for item in result:
                    _handle_single_result(keyword, item)
            elif isinstance(result, dict):
                _handle_single_result(keyword, result)

        time.sleep(1)

    except CensysException as e:
        print(f"[Error] {keyword}: {e}")


# === Step 4: Run Search ===
print("Collecting baseline...")
baseline_set = set()
for kw in baseline_keywords:
    run_query_with_content(kw)
    baseline_set |= set(keyword_to_sites[kw].keys())

print("Collecting LLM keywords...")
llm_unique_counts = {}
for kw in llm_keywords:
    run_query_with_content(kw)
    llm_sites = set(keyword_to_sites[kw].keys())
    unique_sites = llm_sites - baseline_set
    llm_unique_counts[kw] = len(unique_sites)
    print(f"[LLM Keyword] {kw} → {len(unique_sites)} unique sites")

# Calculate total keywords and those with zero unique sites
total_keywords = len(llm_unique_counts)
zero_unique_keywords = sum(1 for count in llm_unique_counts.values() if count == 0)

print(f"Total LLM Keywords: {total_keywords}")
print(f"Keywords with Zero Unique Sites: {zero_unique_keywords}")

# Filter out keywords with zero unique sites
filtered_llm_unique_counts = {k: v for k, v in llm_unique_counts.items() if v > 0}

plt.figure(figsize=(12, 6))
plt.barh(list(filtered_llm_unique_counts.keys()), list(filtered_llm_unique_counts.values()))
plt.xlabel("Unique Sites Not Found by Baseline")
plt.title("LLM Keyword Effectiveness: Unique Illicit Pharmacy Sites")
plt.tight_layout()
plt.gca().invert_yaxis()
plt.savefig("llm_keyword_effectiveness2.pdf")
plt.show()

# === Step 6: Word Cloud from HTML Content ===
def generate_wordcloud():
    all_text = ""
    for site_dict in keyword_to_sites.values():
        for meta in site_dict.values():
            all_text += " " + (meta.get("title") or "") + " " + (meta.get("body") or "")

    if not all_text.strip():
        print("[Warning] No website content available to generate word cloud.")
        return

    wordcloud = WordCloud(width=1600, height=800, background_color='white').generate(all_text)
    plt.figure(figsize=(15, 7))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis("off")
    plt.title("Word Cloud from Website Titles and Body Content")
    plt.savefig("website_wordcloud2.pdf")
    # plt.show()


generate_wordcloud()

# === Step 7: Keyword Overlap Matrix ===
def plot_keyword_overlap():
    all_keywords = baseline_keywords + llm_keywords
    keyword_ip_sets = {k: set(keyword_to_sites[k].keys()) for k in all_keywords}
    matrix = []
    for k1 in all_keywords:
        row = []
        for k2 in all_keywords:
            overlap = len(keyword_ip_sets[k1] & keyword_ip_sets[k2])
            row.append(overlap)
        matrix.append(row)
    df = pd.DataFrame(matrix, index=all_keywords, columns=all_keywords)
    plt.figure(figsize=(14, 12))
    sns.heatmap(df, annot=True, fmt="d", cmap="YlGnBu")
    plt.title("Keyword Overlap: Shared IPs Across Keywords")
    plt.tight_layout()
    plt.savefig("keyword_overlap_matrix2.png")
    plt.show()

plot_keyword_overlap()