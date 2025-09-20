import streamlit as st
import pandas as pd
import psycopg2
import plotly.express as px
import os

# --- 1. Database Connection & Caching ---
# IMPORTANT: Replace with your actual PostgreSQL connection details.
# It is recommended to use environment variables for production.
@st.cache_data
def load_data():
    """Connects to the PostgreSQL database, queries the nonfarm_payrolls table, and caches the data."""
    try:
        conn = psycopg2.connect(
            dbname=os.environ.get("DB_NAME", "FREDAPI"),
            user=os.environ.get("DB_USER", "postgres"),
            password=os.environ.get("DB_PASSWORD", "suhani.."),
            host=os.environ.get("DB_HOST", "localhost")
        )
        query = "SELECT * FROM nonfarm_payrolls;"
        df = pd.read_sql(query, conn)
        conn.close()
        
        # Ensure the date column is in datetime format
        df['date'] = pd.to_datetime(df['date'])
        
        st.success("Data loaded and cached successfully!")
        return df
    except Exception as e:
        st.error(f"Error connecting to the database or loading data: {e}")
        return None

# --- 2. Custom Styling ---
def add_custom_css():
    """Injects custom CSS for styling the app."""
    st.markdown("""
        <style>
        .main {
            background-color: #f5f5f5;
        }
        .css-1av0vzn { /* Streamlit's main header container */
            display: flex;
            justify-content: center;
        }
        h1 {
            color: #333;
            text-align: center;
        }
        .st-emotion-cache-1q1n1p { /* CSS for the main content container */
            border-radius: 10px;
            box-shadow: 0 4px 8px 0 rgba(0,0,0,0.1), 0 6px 20px 0 rgba(0,0,0,0.1);
            padding: 20px;
            margin-bottom: 20px;
            background-color: white;
        }
        .css-1f7l053 { /* Plotly chart container */
            border-radius: 10px;
            box-shadow: 0 4px 8px 0 rgba(0,0,0,0.05), 0 6px 20px 0 rgba(0,0,0,0.05);
            padding: 10px;
            background-color: white;
        }
        table {
            border-collapse: collapse;
            width: 100%;
            margin-top: 20px;
        }
        th, td {
            text-align: left;
            padding: 8px;
        }
        tr:nth-child(even) {
            background-color: #f2f2f2;
        }
        </style>
    """, unsafe_allow_html=True)

# --- 3. OLAP Analyses & Visualizations ---
def create_slicing_charts(df):
    """Performs and visualizes Slicing analyses."""
    st.header("Slicing Analysis")



    # Slicing 2: Monthly employment comparison for Mar-Dec 2020 vs. 2019
    st.subheader("Monthly Employment Comparison (Mar-Dec 2020 vs. 2019)")
    df['year'] = df['date'].dt.year
    df['month'] = df['date'].dt.month
    df_slice2 = df[((df['year'] == 2019) | (df['year'] == 2020)) & 
                   (df['month'].between(3, 12))].copy()
    df_slice2['Month'] = df_slice2['date'].dt.strftime('%b')

    # Create a line chart with clear markers, larger font, and legend
    fig2 = px.line(
        df_slice2, 
        x='Month', 
        y='total_nonfarm', 
        color='year',
        title="Monthly Employment: March-December 2020 vs. 2019",
        labels={'total_nonfarm': 'Total Employment (in thousands)', 'Month': 'Month', 'year': 'Year'},
        markers=True,
        line_dash='year',
        color_discrete_map={2019: '#636EFA', 2020: '#EF553B'}
    )
    fig2.update_layout(
        legend_title_text='Year',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        font=dict(size=14),
        plot_bgcolor='#f5f5f5',
        paper_bgcolor='#f5f5f5',
        title_font=dict(size=20, family='Arial'),
        xaxis=dict(title='Month', tickmode='array', tickvals=df_slice2['Month'].unique()),
        yaxis=dict(title='Total Employment (in thousands)', gridcolor='lightgrey')
    )
    fig2.update_traces(marker=dict(size=10), line=dict(width=4))
    st.plotly_chart(fig2, use_container_width=True)

def create_dicing_charts(df):
    """Performs and visualizes Dicing analyses."""
    st.header("Dicing Analysis")

    # Dicing 1: Months with > 2% month-over-month employment drop
    st.subheader("Months with > 2% Month-over-Month Employment Drop")
    df['mom_growth'] = df['total_nonfarm'].pct_change() * 100
    df['month_year'] = df['date'].dt.strftime('%b-%Y')
    
    significant_drops = df[df['mom_growth'] < -2].copy()
    if not significant_drops.empty:
        st.write("Months with a greater than 2% month-over-month employment drop:")
        st.dataframe(significant_drops[['month_year', 'mom_growth']].round(2).rename(columns={'mom_growth': 'MoM Growth (%)'}))
        
        # Calculate recovery time
        recovery_data = []
        for index, row in significant_drops.iterrows():
            drop_date = row['date']
            drop_employment = row['total_nonfarm']
            
            # Find the peak before the drop
            pre_drop_data = df[df['date'] < drop_date]
            if not pre_drop_data.empty:
                prior_peak_employment = pre_drop_data['total_nonfarm'].max()
                
                # Find the first month where employment recovers to or exceeds the prior peak
                post_drop_data = df[df['date'] > drop_date]
                recovery_month = post_drop_data[post_drop_data['total_nonfarm'] >= prior_peak_employment].first_valid_index()
                
                if recovery_month:
                    months_to_recover = (df.loc[recovery_month]['date'].year - drop_date.year) * 12 + (df.loc[recovery_month]['date'].month - drop_date.month)
                    recovery_data.append({
                        'Drop Month': row['month_year'],
                        'Prior Peak Date': df.loc[pre_drop_data['total_nonfarm'].idxmax()]['date'].strftime('%b-%Y'),
                        'Months to Recover': months_to_recover
                    })
                else:
                    recovery_data.append({'Drop Month': row['month_year'], 'Prior Peak Date': 'N/A', 'Months to Recover': 'Not recovered yet'})
        
        if recovery_data:
            st.write("Time taken to recover to the prior peak:")
            st.dataframe(pd.DataFrame(recovery_data))
    else:
        st.info("No months found with a month-over-month employment drop greater than 2%.")

    # Dicing 2: Q4 month with highest payroll growth
    st.subheader("Highest Q4 Payroll Growth by Month")
    # Calculate month-over-month percentage change for all months
    df_all = df.copy()
    df_all['year'] = df_all['date'].dt.year
    df_all['month'] = df_all['date'].dt.strftime('%b')
    df_all['pct_change_mom'] = df_all['total_nonfarm'].pct_change() * 100

    # Filter for Q4 months only
    df_q4 = df_all[df_all['date'].dt.month.isin([10, 11, 12])].copy()

    # For each year, select the Q4 month with the highest MoM % change
    idx = df_q4.groupby('year')['pct_change_mom'].idxmax()
    df_q4_highest = df_q4.loc[idx]

    # Custom color mapping for months
    color_map = {'Oct': 'red', 'Nov': 'blue', 'Dec': 'green'}

    fig3 = px.bar(df_q4_highest, x='year', y='pct_change_mom', color='month',
                  labels={'year': 'Year', 'pct_change_mom': 'MoM % Change', 'month': 'Month'},
                  barmode='group',
                  color_discrete_map=color_map)

    # Increase bar width
    fig3.update_traces(width=0.8)

    st.plotly_chart(fig3, use_container_width=True)

def create_roll_up_charts(df):
    """Performs and visualizes Roll-up analyses."""
    st.header("Roll-up Analysis")

    # Roll-up 1: Quarter-over-quarter and Year-over-year growth rates
    st.subheader("Quarter-over-Quarter and Year-over-Year Growth Rates")
    
    # Quarterly aggregation
    df_quarterly = df.set_index('date').resample('QS').mean()
    df_quarterly['qoq_growth'] = df_quarterly['total_nonfarm'].pct_change() * 100
    fig_qoq = px.line(df_quarterly.reset_index(), x='date', y='qoq_growth', 
                      title="Quarter-over-Quarter Employment Growth Rate",
                      labels={'qoq_growth': 'QoQ Growth (%)', 'date': 'Date'})
    st.plotly_chart(fig_qoq)

    # Yearly aggregation
    df_yearly = df.set_index('date').resample('A').mean()
    df_yearly['yoy_growth'] = df_yearly['total_nonfarm'].pct_change() * 100
    fig_yoy = px.line(df_yearly.reset_index(), x='date', y='yoy_growth', 
                      title="Year-over-Year Employment Growth Rate",
                      labels={'yoy_growth': 'YoY Growth (%)', 'date': 'Date'})
    st.plotly_chart(fig_yoy)
    
    # Roll-up 2: Compare average employment in 2010s vs. 2000s
    st.subheader("Average Employment in the 2010s vs. the 2000s")
    df['year'] = df['date'].dt.year
    decade_2000s = df[(df['year'] >= 2000) & (df['year'] <= 2009)]
    decade_2010s = df[(df['year'] >= 2010) & (df['year'] <= 2019)]
    
    avg_2000s = decade_2000s['total_nonfarm'].mean()
    avg_2010s = decade_2010s['total_nonfarm'].mean()
    
    comparison_df = pd.DataFrame({
        'Decade': ['2000s', '2010s'],
        'Average Employment': [avg_2000s, avg_2010s]
    })
    
    fig_decades = px.bar(comparison_df, x='Decade', y='Average Employment', 
                         title="Average Employment: 2000s vs. 2010s",
                         labels={'Average Employment': 'Average Employment (in thousands)'})
    st.plotly_chart(fig_decades)

def create_drill_down_charts(df):
    """Performs and visualizes Drill-down analyses."""
    st.header("Drill-down Analysis")
    
    # Drill-down 1: Year with highest annual employment gain
    st.subheader("Breakdown of Highest Annual Employment Gain")
    df_annual = df.groupby(df['date'].dt.year)['total_nonfarm'].sum().reset_index()
    df_annual['annual_gain'] = df_annual['total_nonfarm'].diff()
    df_annual.columns = ['year', 'total_employment', 'annual_gain']
    highest_gain_year = df_annual.loc[df_annual['annual_gain'].idxmax()]['year']
    
    st.write(f"The year with the highest annual employment gain was **{int(highest_gain_year)}**.")
    
    # Drill-down into that year's monthly contributions
    highest_gain_df = df[df['date'].dt.year == highest_gain_year].copy()
    highest_gain_df['month'] = highest_gain_df['date'].dt.strftime('%b')
    fig_drill = px.bar(highest_gain_df, x='month', y='total_nonfarm',
                       title=f"Monthly Employment Contributions in {int(highest_gain_year)}",
                       labels={'total_nonfarm': 'Total Employment (in thousands)', 'month': 'Month'},
                       color='total_nonfarm')
    st.plotly_chart(fig_drill)
    
    # Drill-down 2: Sharpest monthly drop
    st.subheader("Sharpest Monthly Employment Drop")
    df['mom_drop'] = df['total_nonfarm'].diff()
    sharpest_drop_month = df.loc[df['mom_drop'].idxmin()]
    
    st.write(f"The sharpest drop in employment occurred in **{sharpest_drop_month['date'].strftime('%B %Y')}**.")
    st.write(f"The total payroll employment decreased by approximately **{sharpest_drop_month['mom_drop']:.2f} thousand** that month.")
    
    st.info("The available data is monthly. A weekly breakdown of this event is not possible with this dataset.")


# --- 4. Main App Structure ---
def main():
    add_custom_css()
    st.title("U.S. Non-Farm Payrolls OLAP Analysis")

    # Sidebar navigation
    st.sidebar.title("Navigation")
    menu_selection = st.sidebar.radio(
        "Select an analysis type:",
        ["Slicing", "Dicing", "Roll-up", "Drill-Down"]
    )

    data = load_data()

    if data is not None:
        if menu_selection == "Slicing":
            create_slicing_charts(data.copy())
        elif menu_selection == "Dicing":
            create_dicing_charts(data.copy())
        elif menu_selection == "Roll-up":
            create_roll_up_charts(data.copy())
        elif menu_selection == "Drill-Down":
            create_drill_down_charts(data.copy())

if __name__ == "__main__":
    main()