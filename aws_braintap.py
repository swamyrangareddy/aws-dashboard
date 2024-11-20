import streamlit as st
import pandas as pd
import numpy as np
from streamlit_option_menu import option_menu
import plotly.express as px
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import altair as alt
from io import StringIO
import boto3

class BraninTapApp:
    def __init__(self):
        self.s3_client = boto3.client('s3')
        self.s3_config = {
            "bucket_name": "my-s3-dashboard",
            "files": {
                "summary": "summary.csv",
                "users": "users.csv",
                "goals": "goals.csv",
                "authors": "authors.csv"
            }
        }

    def load_data_from_s3(self, file_key):
        """Load CSV data from an S3 bucket using a file key."""
        bucket_name = self.s3_config["bucket_name"]
        response = self.s3_client.get_object(Bucket=bucket_name, Key=self.s3_config["files"][file_key])
        content = response['Body'].read().decode('utf-8')
        return pd.read_csv(StringIO(content))

    def page_summary(self):
        summary = self.load_data_from_s3('summary')

        summary['tap_session_started_at'] = pd.to_datetime(summary['tap_session_started_at'], errors='coerce')

        total1, total2, total3,total4 = st.columns(4)

        with total1:
            #Total no users - 22952
            st.info("Total Users") 
            st.metric(label="Total Users", value="22952")

        with total2:
            #Total no partners - 5555
            st.info("Total Partners") 
            st.metric(label="Total Partners", value="570")

        with total3:
            #Total no sessions - 100000
            st.info("Total BT Paid Users")
            st.metric(label="Total BT Paid Users", value='22041')
        
        with total4:
            st.info("Awakend Active")
            st.metric(label="Awakend Active", value="304")
            
        # Filter data for "Paid Partner (Unlimited)" title and NULL completed_minutes
        filtered_df = summary[(summary['title'] == 'Paid Partner (Unlimited)') & (summary['completed_minutes'].isnull())]
        # Count unique user IDs
        partners_no_sessions = filtered_df['userid'].nunique()
        
        # Filter data for "User (Limited)" title and NULL completed_minutes
        filtered_df = summary[(summary['title'] == 'BT Paid Customer (Limited)') & (summary['completed_minutes'].isnull())]
        
        # Count unique user IDs
        users_no_sessions = filtered_df['userid'].nunique()
                    
        # Count occurrences of each session ID
        session_counts = summary['tap_session_id'].value_counts()
        
        # Get the most played session and least played session details
        most_played_session_id = session_counts.idxmax()   # Session ID with the highest count
        most_played_session_count = session_counts.max()    # Count of the most played session
        
        least_played_session_id = session_counts.idxmin()   # Session ID with the lowest count
        least_played_session_count = session_counts.min()   # Count of the least played session
        
        # Display in Streamlit
        total1, total2, total3, total4 = st.columns(4, gap='small')
        
        with total1:
            st.info('Partners - Played Sessions = 0')
            st.metric(label='Number of Partners', value=f"{partners_no_sessions}")
        
        with total2:
            st.info('Users - Played Sessions = 0')
            st.metric(label="Number of Users", value=f"{users_no_sessions}")
        
        with total3:
            st.info('Most Played Session')
            # Displaying both count and session ID for most played session
            st.metric(label="Most Played Session", value=f"{most_played_session_count}", delta=f"Session ID: {most_played_session_id}")
        
        with total4:
            st.info('Least Played Session')
            # Displaying both count and session ID for least played session
            st.metric(label="Least Played Session", value=f"{least_played_session_count}", delta=f"Session ID: {least_played_session_id}")


        def get_session_counts(df, days):
            filtered_df = df[df['tap_session_started_at'] >= pd.Timestamp.now() - pd.Timedelta(days=days)]
            if filtered_df.empty:
                return None
            session_count = filtered_df['tap_session_id'].count()
            return {'days': days, 'session_count': session_count}
        
        # Assuming your DataFrame is already loaded as df
        top_sessions = {
            'Last Week': get_session_counts(summary, 7),
            'Last 15 Days': get_session_counts(summary, 15),
            'Last Month': get_session_counts(summary, 30),
            'Last 2 Months': get_session_counts(summary, 60),
        }
        
        # Display the session counts
        st.subheader("Session Counts Over Different Periods")
        
        # Define the color and icon for all boxes
        icons = ["📅", "📆", "🗓️", "🗓️"]
        
        # Display each period in a column layout with fixed styling
        columns = st.columns(4)
        for i, (period, session) in enumerate(top_sessions.items()):
            with columns[i]:
                # Display session count in a metric
                st.info(f"{icons[i]} {period}" )
                st.metric(label="Session Count", value=session['session_count'] if session else 'N/A')
        st.write(" ")
        
        st.sidebar.header("Select Date Range:")
        start_date = st.sidebar.date_input("Start date", summary['tap_session_started_at'].min().date())
        end_date = st.sidebar.date_input("End date", summary['tap_session_started_at'].max().date())
        filtered_df = summary[(summary['tap_session_started_at'] >= pd.to_datetime(start_date)) & (summary['tap_session_started_at'] <= pd.to_datetime(end_date))]

        with st.expander("VIEW DATA"):
                showData = st.multiselect('Filter: ',  filtered_df.columns, default=[
                    'tap_session_started_at', 'tap_session_id',	'completed_minutes', 'title', 'userid',
                    'user_notifications_enabled',	'preferred_time',	'email'])
                st.dataframe( filtered_df[showData], use_container_width=True)

        # Group by 'tap_session_id' and calculate total completed minutes
        session_time_spent = filtered_df.groupby('tap_session_id')['completed_minutes'].sum().reset_index()
        # Sort by total completed minutes in descending order and get the top 10
        session_time_spent = session_time_spent.sort_values(by='completed_minutes', ascending=False).head(10).reset_index()
        
        st.subheader("Most Frequently Played Sessions")
        
        # Creating an interactive bar chart with Altair
        chart = alt.Chart(session_time_spent).mark_bar().encode(
            x=alt.X('tap_session_id:N', sort='-y', title='Session ID'),
            y=alt.Y('completed_minutes:Q', title='Completed Minutes'),
            tooltip=['tap_session_id', 'completed_minutes']
        ).properties(
            width=600,
            height=400
        ).configure_axis(
            labelAngle=0
        )
        
        st.altair_chart(chart, use_container_width=True)
        
        # Optional: Display the data in a table for reference
        with st.expander("View Data"):
            st.dataframe(session_time_spent, use_container_width=True)

        
        # Convert 'tap_session_started_at' to datetime, handling errors by coercing invalid dates to NaT
        summary['tap_session_started_at'] = pd.to_datetime(summary['tap_session_started_at'], errors='coerce')

        

        total1, total2= st.columns(2, gap='small')
        with total1 :
            filtered_df['title'].value_counts()
            st.subheader("User Group Title")
            user_group_title = filtered_df.groupby(['title'])['userid'].count().reset_index()
            user_group_title = user_group_title.sort_values(by='userid', ascending=False)
            fig = px.pie(user_group_title, names='title', values='userid')
            st.plotly_chart(fig, use_container_width=True)

        with total2:
            st.subheader("User Notifications Enabled")
            user_notifications_enabled = filtered_df.groupby(['user_notifications_enabled'])['userid'].count().reset_index()
            user_notifications_enabled = user_notifications_enabled.sort_values(by='userid', ascending=False)
            fig = px.pie(user_notifications_enabled, names='user_notifications_enabled', values='userid')
            st.plotly_chart(fig, use_container_width=True)


        # no_of_times_comple_per = filtered_df.groupby(['tap_session_id'])['twenty_five_percent_completed_at'].count().reset_index()
        # # Sort by total completed minutes in descending order
        # no_of_times_comple_per = no_of_times_comple_per.sort_values(by='twenty_five_percent_completed_at', ascending=False).head(10)
        # # Display a bar chart for a visual representation
        # st.subheader("Total Time Spent per Session (Top 10)")
        # st.bar_chart(no_of_times_comple_per.set_index('tap_session_id').head(10)['twenty_five_percent_completed_at'])
        # # Show the sorted data in a table
        # with st.expander("VIEW DATA"):
        #     st.dataframe(no_of_times_comple_per )


        # Get unique value counts of preferred_time
        preferred_time = filtered_df['preferred_time'].value_counts().reset_index()
        preferred_time.columns = ['preferred_time', 'count']  # Rename columns for clarity
        preferred_time = preferred_time.sort_values(by='count', ascending=False)
        
        # Display a bar chart for a visual representation
        st.subheader("Preferred Time")
        
        # Create an interactive bar chart with Altair with horizontal labels
        chart = alt.Chart(preferred_time).mark_bar().encode(
            x=alt.X('count:Q', title='Count'),
            y=alt.Y('preferred_time:N', title='Preferred Time', sort='-x'),
            tooltip=['preferred_time', 'count']
        ).properties(
            width=600,
            height=400
        ).configure_axis(
            labelAngle=0  # Set the label angle to 0 to make them horizontal
        )
        
        st.altair_chart(chart, use_container_width=True)
        
        # Optional: Display the data in a table for reference
        with st.expander("View Data"):
            st.dataframe(preferred_time, use_container_width=True)




    def page_users(self):
        users = self.load_data_from_s3('users')

        users['tap_session_started_at'] = pd.to_datetime(users['tap_session_started_at'], errors='coerce')
        st.sidebar.header("Select Date Range:")
        start_date = st.sidebar.date_input("Start date", users['tap_session_started_at'].min().date())
        end_date = st.sidebar.date_input("End date", users['tap_session_started_at'].max().date())
        filtered_df = users[(users['tap_session_started_at'] >= pd.to_datetime(start_date)) & (users['tap_session_started_at'] <= pd.to_datetime(end_date))]

        titles = filtered_df['title'].unique()
        titles = np.insert(titles, 0, 'All')
        st.sidebar.header("Select User Group:")
        title = st.sidebar.selectbox("User Group", titles, index=0)
        if title != 'All':
            filtered_df = filtered_df[filtered_df['title'] == title]

        total1, total2, total3, = st.columns(3)

        with total1:
            #Total no users - 22952
            st.info("Total Users") 
            st.metric(label="Total Users", value="22952")

        with total2:
            #Total no partners - 5555
            st.info("Total Partners") 
            st.metric(label="Total Partners", value="570")

        with total3:
            #Total no sessions - 100000
            st.info("Total BT Paid Users")
            st.metric(label="Total BT Paid Users", value='22041')

        total1, total2,total3 = st.columns(3, gap='small')
        with total1 :
            st.info('Total Active Users')
            st.metric(label="Total Active Users", value=filtered_df['userid'].nunique())
        with total2:
            st.info('Total Completed Minutes')
            st.metric(label="Total Completed Minutes", value=filtered_df['completed_minutes'].sum())
        with total3:
            st.info('Total Unique Sessions')
            st.metric(label="Total Unique Sessions", value=filtered_df['tap_session_id'].nunique())

        total1, total2,total3 = st.columns(3, gap='small')
        with total1 :
            st.info('Number of Sessions Played')
            st.metric(label="Number of Sessions Played", value=filtered_df['tap_session_id'].count())
        with total2:
            st.info("User Notifications Enabled")
            st.metric(label="User Notifications Enabled", value=filtered_df[filtered_df['user_notifications_enabled'] == True]['userid'].count())
        with total3:
            st.info("User Notifications Disabled")
            st.metric(label="User Notifications Disabled", value=filtered_df[filtered_df['user_notifications_enabled'] == False]['userid'].count())



        total1, total2 = st.columns(2, gap='small')
        with total1:
            # Most Performing Users
            most_performing_users = filtered_df.groupby('userid')['completed_minutes'].sum().reset_index()
            most_performing_users_df = most_performing_users.sort_values(by='completed_minutes', ascending=False).reset_index(drop=True).head(10)
            # Creating an interactive bar chart with Altair
            st.subheader("Users with Most Session Activity")
            chart = alt.Chart(most_performing_users_df).mark_bar().encode(
                x=alt.X('userid:N', sort='-y', title='User ID'),
                y=alt.Y('completed_minutes:Q', title='Completed Minutes'),
                tooltip=['userid', 'completed_minutes']).properties(width=600,height=400,).configure_axis(labelAngle=0)
            st.altair_chart(chart, use_container_width=True)
            with st.expander("VIEW DATA"):
                st.dataframe(most_performing_users_df)
        
        with total2:
            # Group by user ID and calculate total completed minutes, sorted ascending
            least_performing_users = filtered_df.groupby('userid')['completed_minutes'].sum().reset_index()
            least_performing_users = least_performing_users[least_performing_users['completed_minutes'] > 0]
            least_performing_users = least_performing_users.sort_values(by='completed_minutes', ascending=True).reset_index(drop=True).head(10)
            st.subheader("Users with Minimal Session Activity")
            chart = alt.Chart(least_performing_users).mark_bar().encode(
                x=alt.X('userid:N', sort='-y', title='User ID'),
                y=alt.Y('completed_minutes:Q', title='Completed Minutes'),
                tooltip=['userid', 'completed_minutes']).properties(width=600,height=400,).configure_axis(labelAngle=0)
            st.altair_chart(chart, use_container_width=True)
            with st.expander("VIEW DATA"):
                st.dataframe(least_performing_users)

        # Convert 'tap_session_started_at' to datetime if not already
        filtered_df['tap_session_started_at'] = pd.to_datetime(filtered_df['tap_session_started_at'], errors='coerce')

        #Calculate session frequency for each user
        filtered_df_user = filtered_df[filtered_df['title'].str.contains('BT Paid', case=False)]
        user_session_counts = filtered_df_user.groupby('userid')['tap_session_id'].count().reset_index()
        user_session_counts = user_session_counts.rename(columns={'tap_session_id': 'session_count'})
        top_10_users = user_session_counts.sort_values(by='session_count', ascending=False).head(10)
        if title in ['All', 'BT Paid Customer (Limited)']:
            # Display top 10 users and visualize
            st.subheader("Key Users with Highest Session Engagement")
            
            # Create an interactive bar chart with Altair
            chart = alt.Chart(top_10_users).mark_bar().encode(
                x=alt.X('userid:N', sort='-y', title='User ID'),
                y=alt.Y('session_count:Q', title='Session Count'),
                tooltip=['userid', 'session_count']
            ).properties(
                width=600,
                height=400
            ).configure_axis(
                labelAngle=0
            )
            
            st.altair_chart(chart, use_container_width=True)
            with st.expander("VIEW DATA"):
                st.dataframe(top_10_users)

        # Most performing Partners title contains parter
        filtered_df_partner = filtered_df[filtered_df['title'].str.contains('Partner', case=False)]
        most_performing_partners = filtered_df_partner.groupby('userid')['completed_minutes'].sum().reset_index()
        most_performing_partners = most_performing_partners.sort_values(by='completed_minutes', ascending=False).head(10)
        if title in ['All', 'Paid Partner (Unlimited)']:
            st.subheader("Key Partners with Highest Session Engagement")
            chart = alt.Chart(most_performing_partners).mark_bar().encode(
                x=alt.X('userid:N', sort='-y', title='User ID'),
                y=alt.Y('completed_minutes:Q', title='Completed Minutes'),
                tooltip=['userid', 'completed_minutes']
            ).properties(
                width=600,
                height=400,
            ).configure_axis(
                labelAngle=0
            )
            st.altair_chart(chart, use_container_width=True)
            
            with st.expander("VIEW DATA"):
                st.dataframe(most_performing_partners)

        # Group by user ID and calculate total completed minutes, sorted ascending
        if title in ['All', 'Paid Partner (Unlimited)']:
            if title == 'All':
                filtered_partners = filtered_df[filtered_df['title'] == 'Paid Partner (Unlimited)']
            else:
                filtered_partners = filtered_df
            st.subheader("Partners with Minimal Session Activity")
            least_performing_partners = filtered_partners.groupby('userid')['completed_minutes'].sum().reset_index()
            least_performing_partners = least_performing_partners.sort_values(by='completed_minutes', ascending=True).head(10)
            # Pie chart
            fig = px.pie(least_performing_partners, names='userid', values='completed_minutes')
            st.plotly_chart(fig, use_container_width=True)
            # Display in Streamlit
            with st.expander("VIEW DATA"):
                st.dataframe(least_performing_partners)

            

        
    def page_goals(self):
        goals = self.load_data_from_s3('goals')
        
        goals['tap_session_started_at'] = pd.to_datetime(goals['tap_session_started_at'], errors='coerce')

        st.sidebar.header("Select Date Range:")
        start_date = st.sidebar.date_input("Start date", goals['tap_session_started_at'].min().date())
        end_date = st.sidebar.date_input("End date", goals['tap_session_started_at'].max().date())
        filtered_df = goals[(goals['tap_session_started_at'] >= pd.to_datetime(start_date)) & (goals['tap_session_started_at'] <= pd.to_datetime(end_date))]

        total1, total2 = st.columns(2, gap='small')
        
        with total1:
            st.info('Users With Goals')
            st.metric(label="Users With Goals", value="22948")
        
        with total2:
            st.info("Users Without Goals")
            st.metric(label="Users Without Goals", value="57818")
            
        total1, total2, total3 = st.columns(3, gap='small')
        
        with total1:
            st.info('Goal - 1 Count')
            st.metric(label="Goal - 1 Count", value="364")
        
        with total2:
            st.info("Goal - 2 Count")
            st.metric(label="Goal - 2 Count", value="22026")

        with total3:    
            st.info('Goal - 3 Count') 
            st.metric(label="Goal - 3 Count", value="558")
            

                    
        # Show how many goals are completed in each session
        completed_goals_per_session = filtered_df.groupby('userid')['user_session_goals'].count().reset_index()
        top_10_sessions = completed_goals_per_session.sort_values(by='user_session_goals', ascending=False).head(10)
        
        # Display top 10 completed goals per session
        st.subheader("Leading Users by Completed Goals")
        
        # Create an interactive bar chart with Altair
        chart = alt.Chart(top_10_sessions).mark_bar().encode(
            x=alt.X('userid:N', sort='-y', title='User ID'),
            y=alt.Y('user_session_goals:Q', title='Completed Goals'),
            tooltip=['userid', 'user_session_goals']
        ).properties(
            width=600,
            height=400
        ).configure_axis(
            labelAngle=0
        )
        
        st.altair_chart(chart, use_container_width=True)
        
        # Optional: Display the data in a table for reference
        with st.expander("VIEW DATA"):
            st.dataframe(top_10_sessions)
        
        # Show how many goals are completed in each session
        completed_goals_per_session = filtered_df.groupby('tap_session_id')['user_session_goals'].count().reset_index()
        top_10_sessions = completed_goals_per_session.sort_values(by='user_session_goals', ascending=False).head(10)
        
        # Display top 10 completed goals per session
        st.subheader("Leading Sessions by Completed Goals")
        
        # Create an interactive bar chart with Altair
        chart = alt.Chart(top_10_sessions).mark_bar().encode(
            x=alt.X('tap_session_id:N', sort='-y', title='Tap Session ID'),
            y=alt.Y('user_session_goals:Q', title='Completed Goals'),
            tooltip=['tap_session_id', 'user_session_goals']
        ).properties(
            width=600,
            height=400
        ).configure_axis(
            labelAngle=0
        )
        
        st.altair_chart(chart, use_container_width=True)
        
        # Optional: Display the data in a table for reference
        with st.expander("VIEW DATA"):
            st.dataframe(top_10_sessions)
        
        # Show how many twenty_five_percent_completed_at are completed in each session
        twenty_five_percent_completed_at = filtered_df.groupby('userid')['twenty_five_percent_completed_at'].count().reset_index()
        top_10_sessions = twenty_five_percent_completed_at.sort_values(by='twenty_five_percent_completed_at', ascending=False).head(10)
        
        # Display top 10 twenty-five percent completed sessions
        st.subheader("Users with 25% of Sessions Completed")
        
        # Create an interactive bar chart with Altair
        chart = alt.Chart(top_10_sessions).mark_bar().encode(
            x=alt.X('userid:N', sort='-y', title='User ID'),
            y=alt.Y('twenty_five_percent_completed_at:Q', title='Completed Events'),
            tooltip=['userid', 'twenty_five_percent_completed_at']
        ).properties(
            width=600,
            height=400
        ).configure_axis(
            labelAngle=0
        )
        
        st.altair_chart(chart, use_container_width=True)
        
        # Optional: Display the data in a table for reference
        with st.expander("VIEW DATA"):
            st.dataframe(top_10_sessions)


        # Filtered data for user session goals
        user_goals = filtered_df['user_session_goals'].dropna().value_counts().reset_index()
        user_goals.columns = ['session_goal', 'count']  # Rename columns for clarity       
        # Display users with their session goal values
        st.subheader("Users with Their Session Goals")        
        # Create an interactive bar chart with Altair with horizontal labels
        chart = alt.Chart(user_goals).mark_bar().encode(
            x=alt.X('count:Q', title='Count of Users'),
            y=alt.Y('session_goal:N', title='Session Goal', sort='-x'),
            tooltip=['session_goal', 'count']
        ).properties(
            width=600,
            height=400
        ).configure_axis(
            labelAngle=0  # Set the label angle to 0 to make them horizontal
        )
        
        st.altair_chart(chart, use_container_width=True)
        
        # Optional: Display the data in a table for reference
        with st.expander("View Data"):
            st.dataframe(user_goals, use_container_width=True)


        # # Calculate the value counts, convert nulls to 0, and reset the index
        # st.subheader("Twenty-Five Percent Completed Sessions")
        # filtered_df['twenty_five_percent_completed_at'] = filtered_df['twenty_five_percent_completed_at'].fillna(0)
        # twenty_five_percent_completed_at = filtered_df['twenty_five_percent_completed_at'].replace(1, 1).value_counts()
        # goal_distribution = twenty_five_percent_completed_at.reset_index()
        # goal_distribution.columns = ['Completion Status', 'Count of Users']  # Rename columns
        # # Create a bar chart using the updated DataFrame
        # fig = px.bar(goal_distribution, x='Completion Status', y='Count of Users',
        #             labels={'Completion Status': 'Completed (0 = No, 1 = Yes)', 'Count of Users': 'Count of Users'},
        #             title="Distribution of Twenty-Five Percent Completed Sessions")
        # # Display the bar chart in Streamlit
        # st.plotly_chart(fig)
        # # Display the subheader and data table
        # with st.expander("VIEW DATA"):
        #     st.dataframe(goal_distribution)  # Display the modified DataFrame

    def page_authors(self):
        authors = self.load_data_from_s3('authors')

        authors['tap_session_started_at'] = pd.to_datetime(authors['tap_session_started_at'], errors='coerce')

        st.sidebar.header("Select Date Range:")
        start_date = st.sidebar.date_input("Start date", authors['tap_session_started_at'].min().date())
        end_date = st.sidebar.date_input("End date", authors['tap_session_started_at'].max().date())
        filtered_df = authors[(authors['tap_session_started_at'] >= pd.to_datetime(start_date)) & (authors['tap_session_started_at'] <= pd.to_datetime(end_date))]
        
        # Count unique authors and narrators
        total_authors = authors['author'].nunique()
        total_narrators = authors['narrator'].nunique()
        
        # Display in Streamlit
        total1, total2 = st.columns(2, gap='small')
        
        with total1:
            st.info('Total Authors')
            st.metric(label="Number of Authors", value=f"{total_authors}")
        
        with total2:
            st.info('Total Narrators')
            st.metric(label="Number of Narrators", value=f"{total_narrators}")


        # Group by 'author' and count unique 'tap_session_id'
        top_authors = (
            filtered_df.groupby('author')['tap_session_id']
            .nunique()
            .sort_values(ascending=False)
            .head(10))
        top_authors_df = top_authors.reset_index(name='session_count')
        
        # Display the subheader
        st.subheader("Top Performing Authors by Session Counts")
        
        # Creating an interactive bar chart with Altair
        chart = alt.Chart(top_authors_df).mark_bar().encode(
            x=alt.X('author:N', sort='-y', title='Author'),
            y=alt.Y('session_count:Q', title='Session Count'),
            tooltip=['author', 'session_count']
        ).properties(
            width=600,
            height=400
        ).configure_axis(
            labelAngle=0
        )
        
        st.altair_chart(chart, use_container_width=True)
        
        # Optional: Display the data in a table for reference
        with st.expander("View Data"):
            st.dataframe(top_authors_df, use_container_width=True)
            
        
            
            
        # Group by 'author' and count unique 'tap_session_id'
        top_narrators = (
            filtered_df.groupby('narrator')['tap_session_id']
            .nunique()
            .sort_values(ascending=False)
            .head(10)
        )
        top_narrators_df = top_narrators.reset_index(name='session_count')
        
        # Display the subheader
        st.subheader("Top Performing Narrators by Session Counts")
        
        # Creating an interactive bar chart with Altair
        chart = alt.Chart(top_narrators_df).mark_bar().encode(
            x=alt.X('narrator:N', sort='-y', title='Narrator'),
            y=alt.Y('session_count:Q', title='Session Count'),
            tooltip=['narrator', 'session_count']
        ).properties(
            width=600,
            height=400
        ).configure_axis(
            labelAngle=0
        )
        
        st.altair_chart(chart, use_container_width=True)
        
        # Optional: Display the data in a table for reference
        with st.expander("View Data"):
            st.dataframe(top_narrators_df, use_container_width=True)

        total1, total2= st.columns(2, gap='small')
        with total1:
            # Least Performing Authors by Session Counts
            least_authors = (
                filtered_df.groupby('author')['tap_session_id']
                .nunique()
                .sort_values(ascending=True)
                .head(10)
            )
            least_authors_df = least_authors.reset_index(name='session_count')
            
            # Display the subheader for least performing authors
            st.subheader("Least Performing Authors by Session Counts")
            
            # Creating an interactive bar chart with Altair for least performing authors
            least_chart = alt.Chart(least_authors_df).mark_bar().encode(
                x=alt.X('author:N', sort='y', title='Author'),
                y=alt.Y('session_count:Q', title='Session Count'),
                tooltip=['author', 'session_count']
            ).properties(
                width=600,
                height=400
            ).configure_axis(
                labelAngle=0
            )
            
            st.altair_chart(least_chart, use_container_width=True)
            
            with st.expander("VIEW DATA"):
                st.dataframe(least_authors_df, use_container_width=True)
            
        with total2:
            # Least Performing Authors by Session Counts
            least_narrators = (
                filtered_df.groupby('narrator')['tap_session_id']
                .nunique()
                .sort_values(ascending=True)
                .head(10)
            )
            least_narrators_df = least_narrators.reset_index(name='session_count')
            
            # Display the subheader for least performing authors
            st.subheader("Least Performing Narrators by Session Counts")
            
            # Creating an interactive bar chart with Altair for least performing authors
            least_chart = alt.Chart(least_narrators_df).mark_bar().encode(
                x=alt.X('narrator:N', sort='y', title='Narrator'),
                y=alt.Y('session_count:Q', title='Session Count'),
                tooltip=['narrator', 'session_count']
            ).properties(
                width=600,
                height=400
            ).configure_axis(
                labelAngle=0
            )
            
            st.altair_chart(least_chart, use_container_width=True)
            
            # Optional: Display the data in a table for reference
            with st.expander("View Data"):
                st.dataframe(least_narrators_df, use_container_width=True)

    def main(self):
        with st.sidebar:
            selected = option_menu(
                menu_title="Select a Page",
                options=["Summary", "Users", "Goals", "Authors"],
                icons=["house", "people", "trophy", "book"],
                menu_icon="cast",
                default_index=0
            )
        
        if selected == "Summary":
            self.page_summary()
        elif selected == "Users":
            self.page_users()
        elif selected == "Goals":
            self.page_goals()
        elif selected == "Authors":
            self.page_authors()

if __name__ == "__main__":

    app = BraninTapApp()
    app.main()