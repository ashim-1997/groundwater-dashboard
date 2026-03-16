import streamlit as st
import pandas as pd
import plotly.express as px

# ---------------- Page Configuration ----------------
st.set_page_config(
    page_title="Groundwater Dashboard",
    layout="wide"
)

st.title("💧 Groundwater Dashboard")
st.markdown("Web-based dashboard for groundwater monitoring and analysis")

# ---------------- Load CSV Data ----------------
@st.cache_data
def load_data():
    # Load Excel file
    # file_path = r"D:\python_udemy_haris\PROJECTS\GW_Dashboard\data\GW_levels_new.xlsx"
    file_path = "data/GW_levels_new.xlsx"
    if file_path.endswith(".csv"):
        df = pd.read_csv(file_path)
    else:
        df = pd.read_excel(file_path)
    # Remove completely empty rows
    df = df.dropna(how="all")

    # Separate inactive wells
    inactive_wells = df[df["Well_Status"] == "Inactive"]

    # Keep only active wells for analysis
    df = df[df["Well_Status"] != "Inactive"]

    
    # Metadata columns (fixed information)
    meta_cols = [
        "District",
        "Block",
        "Village/Town",
        "Place",
        "Well_Type",
        "Well_ID",
        "Latitude",
        "Longitude"
    ]

    # Year_Season columns follow YYYY_season pattern
    value_cols = [col for col in df.columns if col not in meta_cols]

    # Convert WIDE → LONG format
    df_long = df.melt(
        id_vars=meta_cols,
        value_vars=value_cols,
        var_name="Year_Season",
        value_name="GWL"
    )
    # It converts GW values into numeric
    df_long["GWL"] = pd.to_numeric(df_long["GWL"], errors="coerce")
   
    # Remove empty groundwater values
    df_long = df_long.dropna(subset=["GWL"])

    # ---------------- Year & Season Extraction ----------------
    # Extract 4-digit year
    df_long["Year"] = df_long["Year_Season"].str.extract(r"(\d{4})")

    # Extract season text AFTER year and underscore
    df_long["Season"] = df_long["Year_Season"].str.extract(r"\d{4}_(.*)")

    # Drop rows where year could not be extracted
    df_long = df_long.dropna(subset=["Year"])

    # Convert Year to integer
    df_long["Year"] = df_long["Year"].astype(int)

    # Clean season names
    df_long["Season"] = df_long["Season"].str.strip()

    # return df_long---I have replaced the earlier return df_long command
    return df_long, inactive_wells

# --------call the function-------
# df=load_data()-- I also changed the call function accordingly
df, inactive_wells = load_data()

# -------------sidebar filters------------------
st.sidebar.header("🔎 Filters")

# ---------------- District Filter (with All option) ----------------
district_options = ["All Districts"] + sorted(df["District"].dropna().unique().tolist())

district = st.sidebar.selectbox(
    "Select District",
    district_options
)

# ---------------- Block Filter (MULTI BLOCK) ----------------

if district == "All Districts":
    block_options = sorted(df["Block"].dropna().unique())
else:
    block_options = sorted(
        df[df["District"] == district]["Block"]
        .dropna()
        .unique()
    )

selected_blocks = st.sidebar.multiselect(
    "Select Block(s)",
    block_options,
    default=block_options
)

# ---------------- Season Filter ----------------
season_filter_df = df.copy()

if district != "All Districts":
    season_filter_df = season_filter_df[season_filter_df["District"] == district]

# multi select in season filter
if selected_blocks:
    season_filter_df = season_filter_df[
        season_filter_df["Block"].isin(selected_blocks)
    ]

season_options = ["All Seasons"] + sorted(
    season_filter_df["Season"].dropna().unique().tolist()
)

season = st.sidebar.selectbox(
    "Select Season",
    season_options
)

# ---------------- Year Filter (MULTI YEAR) ----------------

year_options = sorted(df["Year"].dropna().unique())

year = st.sidebar.multiselect(
    "Select Year(s)",
    year_options,
    default=year_options
)

# ---------------- Well Type Filter ----------------
well_type_options = ["All Well Types"] + sorted(
    df["Well_Type"].dropna().unique().tolist()
)

well_type = st.sidebar.selectbox(
    "Select Well Type",
    well_type_options
)

# ---------------- Well Filter (DEPENDENT ON DISTRICT & BLOCK) ----------------

# Create a temporary dataframe for well filtering
well_filter_df = df.copy()

# Apply district condition
if district != "All Districts":
    well_filter_df = well_filter_df[
        well_filter_df["District"] == district
    ]

# Apply block condition
if selected_blocks:
    well_filter_df = well_filter_df[
        well_filter_df["Block"].isin(selected_blocks)
    ]

# Extract wells only from selected district/block
well_options = sorted(
    well_filter_df["Well_ID"].dropna().unique().tolist()
)

select_all_wells = st.sidebar.checkbox("Select All Wells", value=True)

if select_all_wells:
    selected_wells = well_options
else:
    selected_wells = st.sidebar.multiselect(
        "Select Wells",
        well_options
    )


filtered_df = df.copy()

# District filter
if district != "All Districts":
    filtered_df = filtered_df[
        filtered_df["District"] == district
    ]

# Block filter (MULTI BLOCK)
if selected_blocks:
    filtered_df = filtered_df[
        filtered_df["Block"].isin(selected_blocks)
    ]

# Apply season filter
if season != "All Seasons":
    filtered_df = filtered_df[filtered_df["Season"] == season]

# Apply year filter (MULTI YEAR)
if year:
    filtered_df = filtered_df[
        filtered_df["Year"].isin(year)
    ]

# WELL TYPE FILTER
if well_type != "All Well Types":
    filtered_df = filtered_df[
        filtered_df["Well_Type"] == well_type
    ]

# WELL FILTER
filtered_df = filtered_df[
    filtered_df["Well_ID"].isin(selected_wells)
]

# ---------------- Menu Navigation ----------------
menu = st.sidebar.radio(
    "Select Dashboard View",
    [
        "Overview",
        "Seasonal Trends",
        "Well Trends",
        "Season Comparison",
        "Block Ranking",
        "Map View",
        "Inactive Wells",
        "Download Data"
    ]
)

# -----------KPI section---------
if menu == "Overview":

    st.subheader("📊 Key Groundwater Indicators")

    if filtered_df.empty:
        st.warning("No data available for selected filters.")
    else:

        col1, col2, col3, col4, col5 = st.columns(5)

        avg_level = filtered_df["GWL"].mean()
        max_level = filtered_df["GWL"].max()
        min_level = filtered_df["GWL"].min()

        active_wells = df["Well_ID"].nunique()
        inactive_count = inactive_wells["Well_ID"].nunique()

        total_wells = active_wells + inactive_count

        col1.metric("Average Water Level (m bgl)", round(avg_level,2))
        col2.metric("Maximum Depth (m bgl)", round(max_level,2))
        col3.metric("Minimum Depth (m bgl)", round(min_level,2))
        col4.metric("Active Wells", active_wells)
        col5.metric("Inactive Wells", inactive_count)

        st.metric("Total Wells in Monitoring Network", total_wells)
        # ---------------- Annual Groundwater Trend ----------------
        st.subheader("📈 Annual Groundwater Level Trend")

        if filtered_df.empty:
            st.warning("No data available for annual trend.")
        else:

            annual_trend = (
                filtered_df
                .groupby("Year", as_index=False)["GWL"]
                .mean()
            )

            fig_annual = px.line(
                annual_trend,
                x="Year",
                y="GWL",
                markers=True,
                title="Average Annual Groundwater Level",
            )

            fig_annual.update_layout(
                xaxis_title="Year",
                yaxis_title="Average Groundwater Level (m bgl)",
                height=450
            )

            st.plotly_chart(fig_annual, width="stretch")
    st.subheader("⚠️ District-wise Well Status")

    if inactive_wells.empty:
        st.info("No inactive wells found in the dataset.")
    else:

        # Total wells per district
        total_district = (
            pd.concat([df, inactive_wells])
            .groupby("District", as_index=False)["Well_ID"]
            .nunique()
        )

        total_district.rename(
            columns={"Well_ID": "Total Wells"},
            inplace=True
        )

        # Inactive wells per district
        inactive_district = (
            inactive_wells
            .groupby("District", as_index=False)["Well_ID"]
            .nunique()
        )

        inactive_district.rename(
            columns={"Well_ID": "Inactive Wells"},
            inplace=True
        )

        # Merge tables
        district_status = pd.merge(
            total_district,
            inactive_district,
            on="District",
            how="left"
        )

        district_status["Inactive Wells"] = district_status["Inactive Wells"].fillna(0).astype(int)

        district_status = district_status.sort_values(
            "Inactive Wells",
            ascending=False
        )

        st.dataframe(district_status, width="stretch")  



# ---------------- Trend Chart Section ----------------
if menu == "Seasonal Trends":
    st.subheader("📈 Groundwater Level Trend by Season")

    if filtered_df.empty:
        st.warning("No data available for trend analysis.")
    else:
        # Group data by Year & Season (average across wells)
        trend_df = (
            filtered_df
            .groupby(["Year", "Season"], as_index=False)["GWL"]
            .mean()
        )

        fig_trend = px.line(
            trend_df,
            x="Year",
            y="GWL",
            color="Season",
            markers=True,
            title="Season-wise Groundwater Level Trend",
        )

        fig_trend.update_layout(
            xaxis_title="Year",
            yaxis_title="Groundwater Level (m bgl)",
            legend_title="Season",
            height=500
        )

        st.plotly_chart(fig_trend, width="stretch")


# ---------------- Well-wise Trend Chart ----------------
if menu == "Well Trends":
    st.subheader("📈 Well-wise Groundwater Level Trend")

    if filtered_df.empty:
     st.warning("No data available for well-wise trend.")
    else:

     # Ensure numeric groundwater values
        well_trend_df = filtered_df.copy()
        well_trend_df["GWL"] = pd.to_numeric(well_trend_df["GWL"], errors="coerce")

        # Create line chart
        fig_well_trend = px.line(
            well_trend_df,
            x="Year",
            y="GWL",
            color="Well_ID",
            markers=True,
            title="Groundwater Level Trend by Observation Well"
        )

        fig_well_trend.update_layout(
            xaxis_title="Year",
            yaxis_title="Groundwater Level (m bgl)",
            legend_title="Well ID",
            height=500
        )

        st.plotly_chart(fig_well_trend, width="stretch")

    # ---------------- Season Comparison Chart ----------------
if menu == "Season Comparison":
    st.subheader("📊 Seasonal Groundwater Level Comparison")

    if filtered_df.empty:
        st.warning("No data available for seasonal comparison.")
    else:
        # Calculate average GWL for each season
        season_avg = (
            filtered_df
            .groupby("Season", as_index=False)["GWL"]
            .mean()
        )

        # Create bar chart
        fig_season = px.bar(
            season_avg,
            x="Season",
            y="GWL",
            color="Season",
            text_auto=".2f",
            title="Average Groundwater Level by Season"
        )

        fig_season.update_layout(
            xaxis_title="Season",
            yaxis_title="Average Groundwater Level (m bgl)",
            showlegend=False,
            height=450
        )

        st.plotly_chart(fig_season, width="stretch")


# ---------------- Year-wise Block Extremes ----------------
st.subheader("📅 Year-wise Highest and Lowest Groundwater Levels by Block")

if filtered_df.empty:
    st.warning("No data available for analysis.")
else:

    # Average GWL by Year and Block
    year_block_stats = (
        filtered_df
        .groupby(["Year", "Block"], as_index=False)["GWL"]
        .mean()
    )

    results = []

    for year in year_block_stats["Year"].unique():

        temp = year_block_stats[year_block_stats["Year"] == year]

        highest = temp.loc[temp["GWL"].idxmax()]
        lowest = temp.loc[temp["GWL"].idxmin()]

        results.append({
            "Year": year,
            "Highest GWL Block": highest["Block"],
            "Highest GWL (m bgl)": round(highest["GWL"], 2),
            "Lowest GWL Block": lowest["Block"],
            "Lowest GWL (m bgl)": round(lowest["GWL"], 2)
        })

    extremes_df = pd.DataFrame(results)

    st.dataframe(extremes_df, width="stretch")


# ---------------- Block Ranking Table ----------------
if menu == "Block Ranking":
    st.subheader("🏆 Block Ranking Based on Average Groundwater Level")

    if filtered_df.empty:
        st.warning("No data available for ranking.")
    else:

        block_rank = (
            filtered_df
            .groupby("Block", as_index=False)["GWL"]
            .mean()
        )

        # Rank blocks
        block_rank["Rank (Deepest First)"] = block_rank["GWL"].rank(
            ascending=False,
            method="dense"
        ).astype(int)

        block_rank = block_rank.sort_values("Rank (Deepest First)")

        block_rank.rename(
            columns={"GWL": "Average GWL (m bgl)"},
            inplace=True
        )

        st.dataframe(block_rank, width="stretch")

# -------display data table----------
st.subheader("📋 Filtered Groundwater Data")
st.dataframe(filtered_df, width="stretch")


# ---------------- Dynamic Map Section ----------------
if menu == "Map View":
    st.subheader("🗺️ Groundwater Observation Wells Map")

    if filtered_df.empty:
        st.warning("No wells to display on map.")
    else:
        map_df = filtered_df.copy()

        # Convert to numeric (CRITICAL FIX)
        map_df["Latitude"] = pd.to_numeric(map_df["Latitude"], errors="coerce")
        map_df["Longitude"] = pd.to_numeric(map_df["Longitude"], errors="coerce")
        map_df["GWL"] = pd.to_numeric(map_df["GWL"], errors="coerce")

        # Remove invalid rows
        map_df = map_df.dropna(subset=["Latitude", "Longitude", "GWL"])

        if map_df.empty:
            st.warning("No valid coordinates or GWL values available.")
        else:
            fig = px.scatter_mapbox(
                map_df,
                lat="Latitude",
                lon="Longitude",
                color="GWL",
                size="GWL",
                hover_data={
                    "District": True,
                    "Block": True,
                    "Season": True,
                    "Year": True,
                    "GWL": True
                },
                color_continuous_scale="Viridis",
                zoom=6,
                height=500
            )

            fig.update_layout(
                mapbox_style="open-street-map",
                margin={"r":0,"t":0,"l":0,"b":0}
            )

            st.plotly_chart(fig, width="stretch")


# ---------------- Inactive Wells Table ----------------
if menu == "Inactive Wells":

    st.subheader("⚠️ Inactive Observation Wells")

    if inactive_wells.empty:
        st.info("No inactive wells found in the dataset.")
    else:
        st.dataframe(
            inactive_wells[
                ["District","Block","Place","Well_ID","Latitude","Longitude"]
            ],
            width="stretch"
        )
# -----Download Button------
if menu == "Download Data":
    st.download_button(
        label="⬇️ Download Filtered Data (CSV)",
        data=filtered_df.to_csv(index=False),
        file_name="filtered_groundwater_data.csv",
        mime="text/csv"
    )