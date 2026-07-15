
import streamlit as st
import pandas as pd
import plotly.express as px
st.set_page_config(page_title="Carbon Emission Tracker",layout="wide")
st.title("Carbon Emission Tracker") 
st.write("Global North VS Global South: Carbon Emission Tracker")

@st.cache_data
def load_data():
    url = "https://raw.githubusercontent.com/owid/co2-data/master/owid-co2-data.csv"
    columns = ["country", "year", "iso_code", "co2", "consumption_co2", "cumulative_co2", "population", "gdp"]
    df = pd.read_csv(url, usecols=columns)
    df = df.sort_values(['country', 'year'])
    df['gdp'] = df.groupby('country')['gdp'].ffill()
    df['population'] = df.groupby('country')['population'].ffill()
    return df

df= load_data()
#control the sidebar
st.sidebar.header("Control Panel")
countries= sorted(df['country'].unique())

target_country=st.sidebar.selectbox("Select Country",countries,index=countries.index("World"))
tarrif_price=st.sidebar.slider(
    "CBAM Carbon Tariff Price (euros/tonne)",min_value=50.0,max_value=150.0,value=79.20,step=0.10
)

st.sidebar.caption("Default Value: 79.20 euros/tonne (July 2026 market average)")

eu_export_share=st.sidebar.slider(
    "EU Export Share (%)",min_value=1.0,max_value=100.0,step=1.0)

#data processing

st.write(f"### Carbon Emission Data for {target_country}")
df_filtered=df[(df['country']==target_country) & (df['year']>=2000)].copy()
df_filtered['net_co2']= df_filtered['consumption_co2'] - df_filtered['co2']
df_filtered['emissions_per_capita']=(df_filtered['co2']*1_000_000)/df_filtered['population']
df_filtered['gdp_per_capita']=df_filtered['gdp']/df_filtered['population']
df_filtered['consumption_co2'] = df_filtered['consumption_co2'].fillna(df_filtered['co2'])


st.dataframe(
    df_filtered.tail(10),
    hide_index=True,  
    use_container_width=True,
    column_config={
        "year": st.column_config.TextColumn("Year"),  
        "country": st.column_config.TextColumn("Country"),
        "iso_code": st.column_config.TextColumn("ISO Code"),
        "co2": st.column_config.NumberColumn("Production CO₂ (Mt)", format="%,.2f"),
        "consumption_co2": st.column_config.NumberColumn("Consumption CO₂ (Mt)", format="%,.2f"),
        "cumulative_co2": st.column_config.NumberColumn("Cumulative CO₂ (Mt)", format="%,.2f"),
        "net_co2": st.column_config.NumberColumn("Net CO₂ (Mt)", format="%,.2f"),
        "population": st.column_config.NumberColumn("Population", format="%,d"),  
        "gdp": st.column_config.NumberColumn("GDP", format="$%,d"),  
        "emissions_per_capita": st.column_config.NumberColumn("Emissions Per Capita (t)", format="%,.2f"),
        "gdp_per_capita": st.column_config.NumberColumn("GDP Per Capita", format="$%,.2f")
    }
)

#tarrif impact

st.write("---")
st.write("Impact of CBAM Carbon Tariff on Selected Country")
df_with_consumption = df_filtered[df_filtered['consumption_co2'].notna()]
if not df_with_consumption.empty:
    latest_row = df_with_consumption.iloc[-1]
    net_carbons = latest_row['net_co2']
    latest_year_num = int(latest_row['year'])

    if net_carbons < -0.1 and target_country != "World":
        net_exported_carbon = abs(net_carbons)
        eu_multiplier = eu_export_share / 100
        total_tariff = net_exported_carbon * eu_multiplier * tarrif_price * 1_000_000
        
        st.metric(
            label=f"Estimated CBAM Tariff for {target_country} (Based on {latest_year_num} Trade Data)",
            value=f"€{total_tariff:,.2f}",
            delta="Exposed Net Exporter of Carbon Emissions",
            delta_color="inverse"
        )
    else:
        st.metric(  
            label=f"Estimated CBAM Tariff for {target_country} (Based on {latest_year_num} Trade Data)",
            value="€0.00",
            delta="Protected / Neutral Balance",
            delta_color="normal"
        )
else:
    st.warning(f"No complete consumption/trade data available for {target_country} to calculate tariffs.")
st.write("### Recent Historical data(last 10 years)")

display_columns = ['year', 'co2', 'consumption_co2', 'net_co2', 'population', 'gdp']
st.dataframe(
    df_filtered[display_columns].tail(10),
    hide_index=True,
    use_container_width=True,
    column_config={
        "year": st.column_config.TextColumn("Year"),
        "co2": st.column_config.NumberColumn("Production CO₂ (Mt)", format="%,.2f"),
        "consumption_co2": st.column_config.NumberColumn("Consumption CO₂ (Mt)", format="%,.2f"),
        "net_co2": st.column_config.NumberColumn("Net CO₂ (Mt)", format="%,.2f"),
        "population": st.column_config.NumberColumn("Population", format="%,d"),
        "gdp": st.column_config.NumberColumn("GDP", format="$%,d")
    }
)
#map
st.write("---")
st.write("Global Carbon Heatmap")
latest_year=df['year'].max()
map_data=df[df['year']==latest_year].copy()
map_data['gdp_per_capita']=map_data['gdp']/map_data['population']

figure=px.choropleth(
    map_data,
    locations="iso_code",
    locationmode="ISO-3",
    color="co2",
    hover_name="country",
    hover_data={"country":False,"co2":":,.0f","gdp_per_capita":":,.0f"},
    color_continuous_scale="Greens",
    title=f"Global Carbon Emissions in {latest_year}"
)

figure.update_layout(
    margin=dict(r=10, t=30, l=10, b=10),
    geo=dict(showframe=False, showcoastlines=False, projection_type="equirectangular")
)

st.plotly_chart(figure,use_container_width=True)


#comparison

st.write("---")
st.write("Comparison of Carbon Emissions production VS consumption")
if not df_filtered.empty:
    fig_line=px.line(
        df_filtered,
        x="year",
        y=["co2","consumption_co2"],
        labels={"value":"CO2 Emissions (million tonnes)","year":"Year","variable":"Emission Type"},
        title=f"Carbon Emissions Production VS Consumption for {target_country}",
        color_discrete_map={"co2":"blue","consumption_co2":"red"}
    )
    new_names={"co2":"Production Emissions","consumption_co2":"Consumption Emissions"}
    fig_line.for_each_trace(lambda trace: trace.update(name=new_names.get(trace.name, trace.name)))

    fig_line.update_layout(
        legend_title_text="Emission Type",
        hovermode="x unified",
        margin=dict(r=10, t=30, l=10, b=10),
        legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1)
    )
    st.plotly_chart(fig_line,use_container_width=True)
else:
    st.warning(f"No data available for {target_country} from 2000 onwards.")
st.caption("Data Source: Our World in Data (OWID) - CO2 and Greenhouse Gas Emissions Dataset")

#Global North VS Global South Analysis
st.write("---")
st.write("Global North VS Global South: Carbon Emission Analysis")
north_regions=["Europe","North America","Oceania"]
south_regions=["Africa","Asia","South America"]
df_regions = df[df['country'].isin(north_regions + south_regions)].copy()
df_regions['bloc']=df_regions['country'].apply(lambda x: "Global North" if x in north_regions else "Global South")
bloc_data=df_regions.groupby(['year','bloc'])['co2'].sum().reset_index()
bloc_data=bloc_data[bloc_data['year']>=1920]

fig_bloc=px.area(
    bloc_data,
    x="year",
    y="co2",
    color="bloc",
    color_discrete_map={"Global North":"Orange","Global South":"green"},
    labels={"co2":"CO2 Emissions (million tonnes)","year":"Year","bloc":"Region"},
    title="Global North VS Global South: Carbon Emissions Over Time",
)

fig_bloc.update_layout(
    hovermode="x unified",
    margin=dict(r=10, t=30, l=10, b=10),
    legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1)
)

st.plotly_chart(fig_bloc,use_container_width=True)
