#Copyright (c) Dmitry Moskalev
import streamlit as st
from google.oauth2 import service_account
from google.cloud import bigquery
import pandas as pd
import seaborn as sns
from PIL import Image

st.set_page_config(page_title="Master project",
                   page_icon='⚙',
                   layout="wide",
                   initial_sidebar_state="collapsed",
                   menu_items=None)

st.title("Master thesis project")
st.markdown("Developing program system for analyzing digital student's footprint")

st.image("Streamlit.gif")

with st.expander("About"):
    st.text("""
        Project of developing program system for analyzing digital student's footprint.

        FAQ:
        1. Select item from list of available groups
        2. The website will show values that chosen group contains
        3. After that results will be printed as visualization
        4. Left row indicates about students activity, right row about attendance per subjects
        5. For better efficiency between BigQuery and StreamLit current query saved in cache for 1 hour
        
        Developer:
        Moskalev Dmitry
        
    """)

# Create API client.
credentials = service_account.Credentials.from_service_account_info(
    st.secrets.gcp_service_account
)
client = bigquery.Client(credentials=credentials)

# Uses st.cache to only rerun when the query changes or after 60 min.
@st.cache(ttl=3600, suppress_st_warning=True, allow_output_mutation=True)
def df():
    query_df_students = client.query(f"SELECT lectures_all, `group`, week_n FROM `{st.secrets.table_id_1.table_1}`")
    rows_raw_students = query_df_students.result()
    table_df_students = [dict(row) for row in rows_raw_students]
    df_students = pd.DataFrame()
    df_students = df_students.append(table_df_students)

    query_job_subjects = client.query(f"SELECT subject, `group`, week_n, total FROM `{st.secrets.table_id_2.table_2}`")
    rows_raw_subjects = query_job_subjects.result()
    table_df_subjects = [dict(row) for row in rows_raw_subjects]
    df_subjects = pd.DataFrame()
    df_subjects = df_subjects.append(table_df_subjects)
    return df_students, df_subjects

df_students, df_subjects = df()

group = st.selectbox('Select group', set(df_subjects['group']))
st.write(f"Values for {group}: {sorted(set(df_students[df_students['group'] == group]['week_n']))}")

df_students_stripplot = sns.stripplot(x=df_students[df_students['group'] == group]["week_n"],
                                      y=df_students[df_students['group'] == group]["lectures_all"],
                                      data=df_students[df_students['group'] == group])
df_subjects_stripplot = sns.stripplot(x=df_subjects[df_subjects['group'] == group]["week_n"],
                                      y=df_subjects[df_subjects['group'] == group]["total"],
                                      data=df_subjects[df_subjects['group'] == group])

df_students_pairplot = sns.pairplot(df_students[df_students['group'] == group],
                                    hue="lectures_all")
df_subjects_pairplot = sns.pairplot(df_subjects[df_subjects['group'] == group],
                                    hue="total")

df_students_graphic = df_students[df_students['group'] == group].plot.hexbin(x='lectures_all',
                                                                             y='week_n',
                                                                             gridsize=20,
                                                                             cmap="viridis")
df_subjects_graphic = df_subjects[df_subjects['group'] == group].plot.hexbin(x='total',
                                                                             y='week_n',
                                                                             gridsize=20,
                                                                             cmap="viridis")

df_students_stats = df_students[df_students['group'] == group].plot.hist(x='lectures_all',
                                                                         y='week_n',
                                                                         bins=max(df_students[df_students['group'] == group]['week_n']), alpha=0.5)
df_subjects_stats = df_subjects[df_subjects['group'] == group].plot.hist(x='total',
                                                                         y='week_n',
                                                                         bins=max(df_subjects[df_subjects['group'] == group]['week_n']), alpha=0.5)

graphic1 = df_students[df_students['group'] == group].plot.scatter(x='week_n',
                                                                   y='group',
                                                                   c='lectures_all',
                                                                   colormap='viridis')
graphic2 = df_subjects[df_subjects['group'] == group].plot.scatter(x='week_n',
                                                                   y='group',
                                                                   c='total',
                                                                   colormap='viridis')


col1, col2 = st.columns([1.0, 1.0])

try:
    with col1:
        st.header("Students")
        st.pyplot(df_students_stripplot.figure)
        st.pyplot(df_students_pairplot.figure)
        st.pyplot(df_students_stats.figure)
        st.pyplot(df_students_graphic.figure)
        st.pyplot(graphic1.figure)

    with col2:
        st.header("Subjects")
        st.pyplot(df_subjects_stripplot.figure)
        st.pyplot(df_subjects_pairplot.figure)
        st.pyplot(df_subjects_stats.figure)
        st.pyplot(df_subjects_graphic.figure)
        st.pyplot(graphic2.figure)

except ValueError:
    st.info("Error")