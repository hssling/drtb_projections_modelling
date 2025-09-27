import pandas as pd
from pathlib import Path

def extract_who_tb(output_file="tb_amr_project/data/tb_raw/who_tb_india.csv"):
    """
    Extract TB-AMR data (MDR/RR-TB) for India from WHO TB Data Portal.
    Saves CSV to data/tb_raw/.
    """
    Path("tb_amr_project/data/tb_raw").mkdir(parents=True, exist_ok=True)

    # WHO TB Data Portal - MDR/RR-TB estimates
    url = "https://extranet.who.int/tme/generateCSV.asp?ds=dr_surveillance"

    try:
        df = pd.read_csv(url)
        print(f"✅ Downloaded WHO TB dataset: {df.shape}")

        # Filter for India
        india = df[df["country"] == "India"]

        # Select relevant columns
        cols = [
            "year", "country", "iso2", "iso3",
            "mdr_new", "mdr_ret",  # MDR cases
            "rr_new", "rr_ret",  # RR-TB cases
            "dst_rlt_new", "dst_rlt_ret",  # DST tested for resistance
            "xdr"  # XDR cases
        ]
        india = india[cols]

        india.to_csv(output_file, index=False)
        print(f"📄 Saved India TB-AMR data → {output_file}")
        return india

    except Exception as e:
        print(f"❌ WHO TB extraction failed: {e}")
        return pd.DataFrame()

def unify_tb_data():
    """
    Combine WHO + local ICMR data into unified schema for forecasting.
    """
    # WHO data
    who_file = "tb_amr_project/data/tb_raw/who_tb_india.csv"
    if not Path(who_file).exists():
        print("⚠️ WHO TB file missing. Run extract_who_tb() first.")
        return pd.DataFrame()

    who = pd.read_csv(who_file)

    # Unified schema: date, country, state, drug, percent_resistant, n_tested, type, source
    records = []

    for _, row in who.iterrows():
        year = int(row["year"])
        # New cases - MDR/RR %
        if pd.notnull(row["mdr_new"]) and pd.notnull(row["dst_rlt_new"]) and row["dst_rlt_new"] > 0:
            percent = (row["mdr_new"] / row["dst_rlt_new"]) * 100
            records.append({
                "date": f"{year}-01-01",
                "country": "India",
                "state": "National",
                "drug": "Rifampicin (proxy MDR)",
                "percent_resistant": percent,
                "n_tested": row["dst_rlt_new"],
                "type": "new",
                "source": "WHO"
            })
        # Retreated cases - MDR/RR %
        if pd.notnull(row["mdr_ret"]) and pd.notnull(row["dst_rlt_ret"]) and row["dst_rlt_ret"] > 0:
            percent = (row["mdr_ret"] / row["dst_rlt_ret"]) * 100
            records.append({
                "date": f"{year}-01-01",
                "country": "India",
                "state": "National",
                "drug": "Rifampicin (proxy MDR)",
                "percent_resistant": percent,
                "n_tested": row["dst_rlt_ret"],
                "type": "retreated",
                "source": "WHO"
            })

    merged = pd.DataFrame(records)
    out_file = "tb_amr_project/data/tb_merged.csv"
    merged.to_csv(out_file, index=False)
    print(f"📊 Unified TB-AMR dataset saved → {out_file} ({len(merged)} rows)")

    return merged

if __name__ == "__main__":
    extract_who_tb()
    unify_tb_data()
