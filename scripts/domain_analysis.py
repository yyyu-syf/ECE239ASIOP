from censys.search import CensysHosts
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import json
from collections import Counter
import os
from datetime import datetime
from collections import defaultdict
from wordcloud import WordCloud

# Your Censys API credentials
API_ID = "xxxxx"
API_SECRET = "xxxx"

def search_illicit_pharmacies():
    """
    Use Censys Hosts API to identify potential illicit online pharmacies
    """
    try:
        # Initialize Censys Hosts client with API credentials
        h = CensysHosts()
        
        # Search queries for identifying potential illicit pharmacies
        search_queries = [
            "services.http.response.body: prescription OR services.http.response.body: medication",
            "(services.http.response.html_title: medication OR services.http.response.html_title: medicine) AND (services.http.response.body: buy OR services.http.response.body: order OR services.http.response.body: online)",
            'services.http.response.body: "no prescription required" AND (services.http.response.body: "pharmacy" OR services.http.response.body: "medication")',
            "services.http.response.body: \"buy medication online\" ",
            # "services.http.response.body: (viagra OR cialis OR tramadol) AND services.http.response.body: (buy OR order)"
        ]
        
        all_results = []
        
        # Execute each search query
        for idx, query in enumerate(search_queries):
            print(f"Executing search query: {query}")
            try:
                # Get search results (paginated)
                search_results = h.search(query, per_page=100, pages=1)
                
                # print(json.dumps(search_results))
                # with open(f'query_{idx}.json', 'w') as f:
                #     json.dump(list(search_results), f, ensure_ascii=False, indent=2)
                    # json.dump(search_results, f)
                # exit()
                # Extract results
                for page in search_results:
                    # print(page)
                    with open('data.json', 'w') as f:
                       json.dump(page,f) 
                    all_results.extend(page)
                
                print(f"Found {len(all_results)} potential results")
            
            except Exception as e:
                print(f"Error executing query '{query}': {e}")
        
        # Deduplicate results based on IP
        unique_ips = {}
        for result in all_results:
            ip = result.get("ip")
            if ip and ip not in unique_ips:
                unique_ips[ip] = result
        
        print(f"Found {len(unique_ips)} unique hosts")
        return list(unique_ips.values())
    
    except Exception as e:
        print(f"Error initializing Censys client: {e}")
        return []

def analyze_search_results(results):
    """
    Analyze Censys search results to identify patterns in illicit online pharmacies
    """
    if not results:
        print("No results to analyze.")
        return
    
    # Extract relevant fields for analysis
    ip_addresses = []
    domains = []
    countries = []
    asn_names = []
    http_titles = []
    http_bodies = []
    
    # Pharmacy-related keywords to look for
    medications = [
        "viagra", "cialis", "levitra", "xanax", "valium", "ambien", "tramadol", 
        "adderall", "oxycontin", "vicodin", "percocet", "hydrocodone", "fentanyl"
    ]
    
    for result in results:
        # Basic host information
        ip_addresses.append(result.get("ip", ""))
        countries.append(result.get("location", {}).get("country", "unknown"))
        
        # AS information
        if "autonomous_system" in result:
            asn_names.append(result["autonomous_system"].get("name", "unknown"))
        else:
            asn_names.append("unknown")
        
        # Extract domains if available
        if "dns" in result and "names" in result["dns"]:
            domains.extend(result["dns"]["names"])
        
        # Extract HTTP title and body content if available
        http_services = result.get("services", [])
        for service in http_services:
            if service.get("service_name") == "HTTP":
                if "http" in service and "response" in service["http"]:
                    response = service["http"]["response"]
                    if "html_title" in response:
                        http_titles.append(response["html_title"].lower())
                    if "body" in response:
                        http_bodies.append(response["body"].lower())
    
    # Count medication mentions in HTTP bodies
    medication_mentions = Counter()
    no_prescription_count = 0
    
    for body in http_bodies:
        # Check medication mentions
        for med in medications:
            if med in body:
                medication_mentions[med] += 1
        
        # Check for no prescription mentions
        if any(phrase in body for phrase in ["no prescription", "without prescription", "no rx"]):
            no_prescription_count += 1
    
    # Create a DataFrame for further analysis
    host_data = pd.DataFrame({
        "ip": ip_addresses,
        "country": countries,
        "asn": asn_names
    })
    
    # Geographic distribution
    country_counts = Counter(countries)
    print("\nTop countries hosting potential illicit pharmacies:")
    for country, count in country_counts.most_common(10):
        print(f"  {country}: {count}")
    
    # ASN distribution
    asn_counts = Counter(asn_names)
    print("\nTop ASNs hosting potential illicit pharmacies:")
    for asn, count in asn_counts.most_common(10):
        print(f"  {asn}: {count}")
    
    # Medication analysis
    print("\nMost commonly mentioned medications:")
    for med, count in medication_mentions.most_common():
        print(f"  {med}: {count}")
    
    # No prescription mentions
    print(f"\nHosts explicitly mentioning 'no prescription required': {no_prescription_count}")
    if http_bodies:
        print(f"Percentage: {no_prescription_count/len(http_bodies)*100:.1f}%")
    
    # Create output directory
    output_dir = "illicit_pharmacy_analysis"
    os.makedirs(output_dir, exist_ok=True)
    
    # Create visualizations
    
    # Visualization 1: Country distribution
    plt.figure(figsize=(12, 8))
    country_df = pd.DataFrame(country_counts.most_common(10), columns=["Country", "Count"])
    sns.barplot(x="Count", y="Country", data=country_df)
    plt.title("Top 10 Countries Hosting Potential Illicit Pharmacies")
    plt.tight_layout()
    plt.savefig(f"{output_dir}/top_countries.png")
    
    # Visualization 2: ASN distribution
    plt.figure(figsize=(12, 8))
    asn_df = pd.DataFrame(asn_counts.most_common(10), columns=["ASN", "Count"])
    sns.barplot(x="Count", y="ASN", data=asn_df)
    plt.title("Top 10 ASNs Hosting Potential Illicit Pharmacies")
    plt.tight_layout()
    plt.savefig(f"{output_dir}/top_asns.png")
    
    # Visualization 3: Medication mentions
    if medication_mentions:
        plt.figure(figsize=(12, 8))
        med_df = pd.DataFrame(medication_mentions.most_common(), columns=["Medication", "Mentions"])
        sns.barplot(x="Mentions", y="Medication", data=med_df)
        plt.title("Medications Mentioned on Potential Illicit Pharmacy Sites")
        plt.tight_layout()
        plt.savefig(f"{output_dir}/medication_mentions.png")
    
    # Save data for further analysis
    host_data.to_csv(f"{output_dir}/illicit_pharmacy_hosts.csv", index=False)
    
    # Generate summary report
    report = {
        "analysis_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_hosts_analyzed": len(results),
        "unique_domains": len(set(domains)),
        "top_countries": dict(country_counts.most_common(10)),
        "top_asns": dict(asn_counts.most_common(10)),
        "medication_mentions": dict(medication_mentions.most_common()),
        "no_prescription_mentions": {
            "count": no_prescription_count,
            "percentage": f"{no_prescription_count/len(http_bodies)*100:.1f}%" if http_bodies else "N/A"
        }
    }
    
    with open(f"{output_dir}/summary_report.json", "w") as f:
        json.dump(report, f, indent=4)
    
    print(f"\nAnalysis complete. Results saved to '{output_dir}' directory.")
    return report


def analyze_search_results2(results):
    if not results:
        print("No results to analyze.")
        return

    # Data collections
    ip_addresses = []
    countries = []
    asn_names = []
    domains = []
    tlds = []
    reg_years = []
    http_titles = []
    http_bodies = []
    port_usage = defaultdict(int)

    medications = [
        "viagra", "cialis", "levitra", "xanax", "valium", "ambien", "tramadol",
        "adderall", "oxycontin", "vicodin", "percocet", "hydrocodone", "fentanyl"
    ]
    medication_mentions = Counter()
    no_prescription_count = 0

    for result in results:
        ip_addresses.append(result.get("ip", ""))
        countries.append(result.get("location", {}).get("country", "unknown"))

        asn_names.append(result.get("autonomous_system", {}).get("name", "unknown"))

        for service in result.get("services", []):
            port_usage[service.get("port", -1)] += 1

            if service.get("service_name") == "HTTP" and "http" in service:
                http = service["http"]
                response = http.get("response", {})
                title = response.get("html_title", "").lower()
                body = response.get("body", "").lower()
                http_titles.append(title)
                http_bodies.append(body)

                for med in medications:
                    if med in body:
                        medication_mentions[med] += 1

                if any(phrase in body for phrase in ["no prescription", "without prescription", "no rx"]):
                    no_prescription_count += 1

        if "dns" in result:
            names = result["dns"].get("names", [])
            domains.extend(names)
            for name in names:
                if "." in name:
                    tld = name.split(".")[-1]
                    tlds.append(f".{tld}")

        if "certificate" in result:
            reg_date = result["certificate"].get("registered")
            if reg_date and len(reg_date) >= 4:
                reg_years.append(reg_date[:4])

    # Output directory
    output_dir = "illicit_pharmacy_analysis"
    os.makedirs(output_dir, exist_ok=True)

    # Save CSV of domains
    domain_df = pd.DataFrame({"domain": list(set(domains)), "tld": tlds})
    domain_df.to_csv(f"{output_dir}/domain_data.csv", index=False)

    # Figures

    # 1. Country Distribution
    plt.figure(figsize=(10, 6))
    pd.Series(countries).value_counts().head(10).plot(kind='barh')
    plt.title("Top Hosting Countries")
    plt.tight_layout()
    plt.savefig(f"{output_dir}/top_countries.png")

    # 2. ASN Distribution
    plt.figure(figsize=(10, 6))
    pd.Series(asn_names).value_counts().head(10).plot(kind='barh')
    plt.title("Top ASNs Hosting Illicit Pharmacies")
    plt.tight_layout()
    plt.savefig(f"{output_dir}/top_asns.png")

    # 3. TLD Distribution
    if tlds:
        plt.figure(figsize=(10, 6))
        pd.Series(tlds).value_counts().head(10).plot(kind='barh')
        plt.title("Top-level Domains (TLDs) Used")
        plt.tight_layout()
        plt.savefig(f"{output_dir}/top_tlds.png")

    # 4. Registration Year Histogram
    if reg_years:
        plt.figure(figsize=(10, 6))
        pd.Series(reg_years).value_counts().sort_index().plot(kind='bar')
        plt.title("Domain Certificate Registration Years")
        plt.xlabel("Year")
        plt.tight_layout()
        plt.savefig(f"{output_dir}/reg_years.png")

    # 5. Medication Mentions
    if medication_mentions:
        plt.figure(figsize=(10, 6))
        pd.Series(medication_mentions).sort_values().plot(kind='barh')
        plt.title("Medication Mentions")
        plt.tight_layout()
        plt.savefig(f"{output_dir}/med_mentions.png")

    # 6. Port Distribution (Top 15 Ports)
    # 6. Port Distribution (Top 15 Ports)
    if port_usage:
        # Top 15 ports
        port_series = pd.Series(port_usage).sort_values(ascending=False).head(15)

        # 映射常见端口到服务名（你可以补充更多）
        port_map = {
            21: "FTP",
            22: "SSH",
            25: "SMTP",
            53: "DNS",
            80: "HTTP",
            110: "POP3",
            143: "IMAP",
            443: "HTTPS",
            587: "SMTP (submission)",
            993: "IMAPS",
            995: "POP3S",
            3306: "MySQL",
            3389: "RDP",
            8080: "HTTP-alt",
            8443: "HTTPS-alt",
            8888: "Web UI"
        }

        # 构造 DataFrame 并加上服务名标签
        port_df = pd.DataFrame({
            "Port": port_series.index,
            "Count": port_series.values
        })
        port_df["Service"] = port_df["Port"].map(port_map).fillna("Unknown")
        port_df["Label"] = port_df.apply(lambda row: f"{row['Port']} ({row['Service']})", axis=1)

        # 绘图
        plt.figure(figsize=(10, 6))
        sns.barplot(x="Count", y="Label", data=port_df, palette="viridis")
        plt.xlabel("Host Count")
        plt.ylabel("Port (Service)")
        plt.title("Top 15 Service Ports Used by Illicit Pharmacies")
        plt.tight_layout()
        plt.savefig(f"{output_dir}/top_ports_bar_labeled.png")
    else:
        print("[Info] No port usage data found.")


    # 7. Word Cloud from bodies
    if http_bodies:
        wc_text = " ".join(http_bodies)
        wc = WordCloud(width=800, height=400, background_color="white").generate(wc_text)
        plt.figure(figsize=(12, 6))
        plt.imshow(wc, interpolation="bilinear")
        plt.axis("off")
        plt.title("Common Terms in HTTP Body")
        plt.tight_layout()
        plt.savefig(f"{output_dir}/http_wordcloud.png")

    # Summary
    report = {
        "total_hosts": len(results),
        "unique_domains": len(set(domains)),
        "top_countries": dict(Counter(countries).most_common(10)),
        "top_asns": dict(Counter(asn_names).most_common(10)),
        "tlds": dict(Counter(tlds).most_common(10)),
        "medications": dict(medication_mentions),
        # "no_prescription": {
        #     "count": no_prescription_count,
        #     "percentage": f"{no_prescription_count / len(http_bodies) * 100:.2f}%"
        # }
    }

    with open(f"{output_dir}/summary_report.json", "w") as f:
        json.dump(report, f, indent=2)

    print("\n✅ Analysis complete. Figures and data saved to:", output_dir)
    return report

def main():
    print("Researching potential illicit online pharmacies using Censys Hosts API...")
    search_results = search_illicit_pharmacies()
    
    if search_results:
        print(f"\nAnalyzing {len(search_results)} potential illicit pharmacy websites...")
        analysis_report = analyze_search_results2(search_results)
        
        print("\nResearch Question Analysis:")
        print("What is the technical infrastructure footprint of illicit online pharmacies, including hosting locations, network providers, and medication offerings?")
        
        if analysis_report:
            print("\nKey Findings:")
            print(f"1. Geographic Distribution: Most common in {list(analysis_report['top_countries'].keys())[0]}")
            print(f"2. Network Providers: Most common ASN is {list(analysis_report['top_asns'].keys())[0]}")
            
            # if analysis_report['medication_mentions']:
            #     print(f"3. Most Commonly Offered Medication: {list(analysis_report['medication_mentions'].keys())[0]}")
            
            # print(f"4. No Prescription Required: {analysis_report['no_prescription_mentions']['percentage']} of sites explicitly advertise this")
    else:
        print("No potential illicit pharmacies identified. Please check API connection or try different search parameters.")

if __name__ == "__main__":
    main()