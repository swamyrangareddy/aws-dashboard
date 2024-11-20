# Import the necessary libraries
import streamlit as st
import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt
from streamlit_option_menu import option_menu
import warnings
from io import StringIO
import boto3
import datetime
import seaborn as sns
import numpy as np
import altair as alt

# Disable all warnings, including deprecation warnings
warnings.filterwarnings('ignore') 

class Dashboard:
    def __init__(self):
        self.s3_client = boto3.client('s3')
        self.s3_config = {
            "bucket_name": "my-s3-dashboard",
            "files": {
                "revenue": "KPI_Revenue_total_counts.csv", 
                "customers": "customers_6months.csv", 
                "subscriptions": "subscriptions_6months.csv", 
                "payment": "payments_outcome_data.csv",
                "financial": "financial.csv", 
                "customer_metadata": "customers_metadata.csv",
                "charges" : "charges_data.csv"
            }}
    
    def load_data_from_s3(self, file_key):
        """Load CSV data from an S3 bucket using a file key."""
        bucket_name = self.s3_config["bucket_name"]
        response = self.s3_client.get_object(Bucket=bucket_name, Key=self.s3_config["files"][file_key])
        content = response['Body'].read().decode('utf-8')
        return pd.read_csv(StringIO(content))
    
    def Summary(self):
        # Assuming `Revenue_df` is your DataFrame with a 'created' column
        revenue_df = self.load_data_from_s3('revenue')
        customers_df = self.load_data_from_s3('customers')
        subscriptions_df = self.load_data_from_s3('subscriptions')# Convert 'trial_end' and 'created' to datetime
        payment_df = self.load_data_from_s3('payment')

        revenue_df = revenue_df[~revenue_df['created'].isnull()]
        revenue_df = revenue_df[revenue_df['created'] != 'NaT'] 

        

        revenue_df['created'] = pd.to_datetime(revenue_df['created'], format='%d-%m-%Y', errors='coerce')
        # New users     - current day and last 7 days
        
        today = revenue_df['created'].dt.date.max()
        last7days = today - datetime.timedelta(days=7)
        last30days = today - datetime.timedelta(days=30)
        new_users_today = revenue_df[revenue_df['created'].dt.date == today]['customer_id'].nunique()
        new_users_last7days = revenue_df[(revenue_df['created'].dt.date >= last7days) & (revenue_df['created'].dt.date < today)]['customer_id'].nunique()
        new_users_last30days = revenue_df[(revenue_df['created'].dt.date >= last30days) & (revenue_df['created'].dt.date < today)]['customer_id'].nunique()
        st.subheader(today)

        # New subscriptions - current day and last 7 days
        last7days = today - datetime.timedelta(days=7)
        last30days = today - datetime.timedelta(days=30)
        new_sub_today = revenue_df[revenue_df['created'].dt.date == today]['subscription'].nunique()
        new_sub_last7days = revenue_df[(revenue_df['created'].dt.date >= last7days) & (revenue_df['created'].dt.date < today)]['subscription'].nunique()
        new_sub_last30days = revenue_df[(revenue_df['created'].dt.date >= last30days) & (revenue_df['created'].dt.date < today)]['subscription'].nunique()

        # merge the two dataframes
        merged_df = pd.merge(revenue_df, payment_df, on='customer_id', how='left').merge(subscriptions_df, on='customer_id', how='left')
        total_users = merged_df['customer_id'].nunique()
        total_trial_subscriptions = merged_df[merged_df['status_x'] == 'trialing']['customer_id'].nunique()
        total_paid_subscriptions = merged_df[merged_df['status_x'] == 'active']['customer_id'].nunique()
        

        total1, total2, total3 = st.columns(3, gap='small')
        with total1:
            st.info('Total Users')
            st.metric(label="", value=f'{total_users}')
        with total2:   
            st.info('Total Trial Subscriptions')
            st.metric(label="", value=f'{total_trial_subscriptions}')
        with total3:
            st.info('Total Paid Subscriptions')
            st.metric(label="", value=f'{total_paid_subscriptions}')
##############################################################################################################
        customer_df_temp = customers_df[["id","name","email"]]
        customer_df_temp.rename({"id":"cust_id"},axis=1, inplace=True)
        merged_df = pd.merge(customer_df_temp, subscriptions_df, left_on='cust_id', right_on='customer_id', how='inner')

        merged_df["description"] =merged_df["description"].fillna("No sub")
        total_no_of_sub = merged_df[merged_df["description"]!='No sub'].shape[0]
        total_monthly_sub = merged_df[merged_df["description"].str.contains('Monthly|month|Month')].shape[0]
        total_yearly_sub = merged_df[merged_df["description"].str.contains('Yearly|year|Year')].shape[0]
        total_promo_sub = merged_df[merged_df["description"].str.contains('Promo|promo')].shape[0]
        
        total_Legacy_Monthly_Sub = merged_df[(merged_df["description"].str.contains('Legacy')) & merged_df["description"].str.contains('Monthly')].shape[0]
        total_Legacy_Yearly_Sub = merged_df[(merged_df["description"].str.contains('Legacy')) & merged_df["description"].str.contains('Yearly')].shape[0]
        total_partners_monthly = merged_df[(merged_df["description"].str.contains('Professional')) & merged_df["description"].str.contains('Monthly')].shape[0]
        total_partners_yearly = merged_df[(merged_df["description"].str.contains('Professional')) & merged_df["description"].str.contains('Yearly')].shape[0]

        total1, total2,total3, total4 = st.columns(4,gap ='small')
        with total1:
            st.info('Total Subscriptions')
            st.metric("",total_no_of_sub)
        with total2:
            st.info("Total Montly Subscriptions")
            st.metric("", total_monthly_sub)
        with total3:
            st.info("Total Yearly Subscriptions")
            st.metric("", total_yearly_sub)
        with total4:
            st.info("Total Promo Subscriptions")
            st.metric("", total_promo_sub)
        
        total1, total2, total3, total4 = st.columns(4, gap ='small')
        with total1:
            st.info("Total Legacy Monthly Subscriptions")
            st.metric("", total_Legacy_Monthly_Sub)
        with total2:
            st.info("Total Legacy Yearly Subscriptions")
            st.metric("", total_Legacy_Yearly_Sub)
        with total3:
            st.info("Total Partners Monthly")
            st.metric("", total_partners_monthly)
        with total4:
            st.info("Total Partners Yearly")
            st.metric("", total_partners_yearly)
##############################################################################################################
        total_products = merged_df['description'].str.contains('Headphones').count()
        total_accessories = merged_df['description'].str.contains('Charging Cable|Replacement Battery|Accessory Shipping').sum()
        total_payments_failed = payment_df[payment_df['status'] == 'failed']['id'].nunique()
        
        total1, total2, total3 = st.columns(3, gap='small')
        with total1:
            st.info('Total Products sold')
            st.metric(label="", value=f'{total_products}')
        with total2:
            st.info('Total Accessories sold')
            st.metric(label="", value=f'{total_accessories}')
        with total3:
            st.info('Payments Failed')
            st.metric(label="", value=f'{total_payments_failed}')

        # Ensure the 'created' column is in datetime format
        revenue_df['created'] = pd.to_datetime(revenue_df['created'], errors='coerce')

        # Check if there are any invalid dates
        if revenue_df['created'].isna().any():
            print("Warning: Some dates could not be parsed and are set to NaT.")

        # Get the maximum date
        today = revenue_df['created'].dt.date.max()

        # Calculate date ranges
        last7days = today - datetime.timedelta(days=7)
        last30days = today - datetime.timedelta(days=30)
        last1year = today - datetime.timedelta(days=365)

        # Filter and count unique customers for the specified periods
        new_users_last7days = revenue_df[(revenue_df['created'].dt.date >= last7days) & (revenue_df['created'].dt.date < today)]['customer_id'].nunique()
        new_users_last30days = revenue_df[(revenue_df['created'].dt.date >= last30days) & (revenue_df['created'].dt.date < today)]['customer_id'].nunique()
        new_users_1_year = revenue_df[(revenue_df['created'].dt.date >= last1year) & (revenue_df['created'].dt.date < today)]['customer_id'].nunique()

                
        st.subheader("New Users")
        total1, total2, total3 = st.columns(3, gap='small')
        with total1:
            st.info('Last 7 Days')
            st.metric(label="", value=f'{new_users_last7days}')
        with total2:   
            st.info('Last 30 Days')
            st.metric(label="", value=f'{new_users_last30days}')
        with total3:
            st.info('Last 1 Year')
            st.metric(label="", value=f'{new_users_1_year}')

        last_7_days = today - datetime.timedelta(days=7)
        last_15_days = today - datetime.timedelta(days=15)
        last_30_days = today - datetime.timedelta(days=30)
        last_1_year = today - datetime.timedelta(days=365)
        new_sub_last7days = revenue_df[(revenue_df['created'].dt.date >= last_7_days) & (revenue_df['created'].dt.date < today)]['subscription'].nunique()
        new_sub_last15days = revenue_df[(revenue_df['created'].dt.date >= last_15_days) & (revenue_df['created'].dt.date < today)]['subscription'].nunique()
        new_sub_last30days = revenue_df[(revenue_df['created'].dt.date >= last_30_days) & (revenue_df['created'].dt.date < today)]['subscription'].nunique()   
        new_sub_1_year = revenue_df[(revenue_df['created'].dt.date >= last_1_year) & (revenue_df['created'].dt.date < today)]['subscription'].nunique()

        st.subheader("Subscriptions Sold")
        total1, total2, total3, total4 = st.columns(4, gap='small')
        with total1:
            st.info('Last 7 Days')
            st.metric(label="", value=f'{new_sub_last7days}')
        with total2:   
            st.info('Last 15 Days')
            st.metric(label="", value=f'{new_sub_last15days}')
        with total3:
            st.info('Last 1 Month')
            st.metric(label="", value=f'{new_sub_last30days}')
        with total4:
            st.info('Last 1 Year')
            st.metric(label="", value=f'{new_sub_1_year}')
        

        last_7_days = today - datetime.timedelta(days=7)
        last_15_days = today - datetime.timedelta(days=15)
        last_30_days = today - datetime.timedelta(days=30)
        last_1_year = today - datetime.timedelta(days=365)
        new_renew_last7days = revenue_df[(revenue_df['created'].dt.date >= last_7_days) & (revenue_df['created'].dt.date < today)]['subscription'].nunique()
        new_renew_last15days = revenue_df[(revenue_df['created'].dt.date >= last_15_days) & (revenue_df['created'].dt.date < today)]['subscription'].nunique()
        new_renew_last30days = revenue_df[(revenue_df['created'].dt.date >= last_30_days) & (revenue_df['created'].dt.date < today)]['subscription'].nunique()
        new_renew_1_year = revenue_df[(revenue_df['created'].dt.date >= last_1_year) & (revenue_df['created'].dt.date < today)]['subscription'].nunique()
        st.subheader("Subscriptions Renewed")
        total1, total2, total3, total4 = st.columns(4, gap='small')
        with total1:
            st.info('Last 7 Days')
            st.metric(label="", value=f'{new_renew_last7days}')
        with total2:   
            st.info('Last 15 Days')
            st.metric(label="", value=f'{new_renew_last15days}')
        with total3:
            st.info('Last 1 Month')
            st.metric(label="", value=f'{new_renew_last30days}')
        with total4:
            st.info('Last 1 Year')
            st.metric(label="", value=f'{new_renew_1_year}')
        
        total_monthly_subscriptions = len(revenue_df[revenue_df['created'].dt.date == today]['subscription'].unique())
        total_yearly_subscriptions = len(revenue_df[revenue_df['created'].dt.date == today]['subscription'].unique())
        total_partners_on_trial = len(revenue_df[revenue_df['created'].dt.date == today]['subscription'].unique())
        total_partners_monthly_paid = len(revenue_df[revenue_df['created'].dt.date == today]['subscription'].unique())
        total1, total2, total3, total4 = st.columns(4, gap='small')
        with total1:
            st.info('Total Monthly Subscriptions')
            st.metric(label="", value=f'{total_monthly_subscriptions}')
        with total2:   
            st.info('Total Yearly Subscriptions')
            st.metric(label="", value=f'{total_yearly_subscriptions}')
        with total3:
            st.info('Total Partners on Trial')
            st.metric(label="", value=f'{total_partners_on_trial}')
        with total4:
            st.info('Total Partners Monthly paid')
            st.metric(label="", value=f'{total_partners_monthly_paid}')
        
        
        


        total1, total2, total3 = st.columns(3, gap='small')
        with total1:
            st.info('New Users')
            st.metric(label="New users today", value=f" {new_users_today}")
    
        with total2:
            st.info('New Users in last 7 days')
            st.metric(label="New users in last 7 days", value=f"{new_users_last7days}")

        with total3:
            st.info('New Users in last 30 days')
            st.metric(label="New users in last 30 days", value=f"{new_users_last30days}")
        
        total1, total2, total3 = st.columns(3, gap='small')
        with total1:
            st.info('New Subscriptions')
            st.metric(label="New Subscriptions today", value=f"{new_sub_today}")
        
        with total2:
            st.info('New Subscriptions in last 7 days')
            st.metric(label="New Subscriptions in last 7 days", value=f" {new_sub_last7days}")

        with total3:
            st.info('New Subscriptions in last 30 days')
            st.metric(label="New Subscriptions in last 30 days", value=f" {new_sub_last30days}")
        
        # Ensure date columns are in datetime format
        revenue_df['created'] = pd.to_datetime(revenue_df['created'])
        # Extract month and year from creation dates
        revenue_df['month'] = revenue_df['created'].dt.to_period('M').astype(str)
        # Group by month and count new users and new subscriptions
        monthly_new_users = revenue_df.groupby('month').size().reset_index(name='new_users')
        # Create bar charts
        fig_users = px.bar(
            monthly_new_users,
            x='month',
            y='new_users',
            title='New Users by Month'
        )
        fig_users.update_xaxes(type='category')
        st.plotly_chart(fig_users)

        # New Subscriptions by Month bar chart 
        # Convert the 'created' column to datetime format
        subscriptions_df['created'] = pd.to_datetime(subscriptions_df['created'])
        # Create a new column 'month' that contains the month of the 'created' column
        subscriptions_df['month'] = subscriptions_df['created'].dt.to_period('M').astype(str)
        # Group the data by 'month' and count the number of new subscriptions for each month
        monthly_new_subscriptions = subscriptions_df.groupby('month').size().reset_index(name='new_subscriptions')
        # Create a bar chart using Plotly Express
        fig_subscriptions = px.bar(
            monthly_new_subscriptions,
            x='month',
            y='new_subscriptions',
            title='New Subscriptions by Month'
        )
        # Update the x-axis to be a category
        fig_subscriptions.update_xaxes(type='category')
        # Display the bar charts using Streamlit
        st.plotly_chart(fig_subscriptions)
        
        # Monthly Subscription Cancellations bar chart
        # Ensure 'created' column is in datetime format
        subscriptions_df['created'] = pd.to_datetime(subscriptions_df['created'], errors='coerce')
        # Ensure 'canceled_at' column is in datetime format with error handling
        subscriptions_df['canceled_at'] = pd.to_datetime(subscriptions_df['canceled_at'], errors='coerce')
        # Drop rows where 'canceled_at' is NaT
        subscriptions_df = subscriptions_df.dropna(subset=['canceled_at'])
        # Extract month and year from the cancellation date
        subscriptions_df['month'] = subscriptions_df['canceled_at'].dt.to_period('M').astype(str)
        # Group by month and count cancellations
        monthly_cancellations = subscriptions_df.groupby('month').size().reset_index(name='cancellations')
        # Create a bar chart
        fig = px.bar(
            monthly_cancellations, 
            x='month', 
            y='cancellations', 
            title='Monthly Subscription Cancellations'
        )
        st.plotly_chart(fig)

    def Revenue(self):
        # Use Streamlit's markdown function to add a style tag to hide the Streamlit element toolbar
        revenue_df = self.load_data_from_s3('revenue')
        charges_df = self.load_data_from_s3('charges')

        # Sidebar
        st.sidebar.header("Select Date Range:")
        # Get the start date and end date from the sidebar
        revenue_df['created'] = pd.to_datetime( revenue_df['created'], errors='coerce')
        start_date = st.sidebar.date_input("Start date", revenue_df["created"].min())
        end_date = st.sidebar.date_input("End date", revenue_df["created"].max())
        st.subheader(start_date)
        # Convert the start date and end date to datetime format
        start_date = pd.to_datetime(start_date)
        end_date = pd.to_datetime(end_date)

        # Filter the dataframe based on the start date and end date
        filtered_df = revenue_df.query("created >= @start_date and created <= @end_date")

        # 1. Total Transaction Amount (sum of all invoice amounts)
        total_transaction_amount = filtered_df['total_invoice_amount'].sum()

        # 2. Total Subscription Amount (assuming 'subscription' keyword in description)
        subscription_df = filtered_df[filtered_df['description'].str.contains('subscription', case=False, na=False)]
        total_subscription_amount = subscription_df['total_invoice_amount'].sum()

        # 3. Total Products Amount (rows where 'description' does NOT contain 'subscription')
        product_df = filtered_df[~filtered_df['description'].str.contains('subscription', case=False, na=False)]
        total_product_amount = product_df['total_invoice_amount'].sum()

        # 4. Tax Amount (assuming 'tax_info_type' provides relevant details)
        tax_amount = filtered_df['tax'].sum()  # Adjust this to the actual tax column

        # Display metrics for all required amounts
        total1, total2 , total3, total4 = st.columns(4, gap='small')
        with total1 :
            st.info('Total Amount',  icon="💸")
            st.metric(label="Total Transaction Amount", value=f"$ {total_transaction_amount:,.2f}")
        with total2:
            st.info('Total Subscription',icon="💸")
            st.metric(label="Total Subscription Amount", value=f"$ {total_subscription_amount:,.2f}")
        with total3:
            st.info('Total Product', icon="💸")
            st.metric(label="Total Product Amount", value=f"$ {total_product_amount:,.2f}")
        with total4:
            st.info('Total Tax', icon="💸") 
            st.metric(label="Total Tax Amount", value=f"$ {tax_amount:,.2f}")
        
        revenue_df = revenue_df[~revenue_df['created'].isnull()]
        revenue_df = revenue_df[revenue_df['created'] != 'NaT'] 
        

        revenue_df['created'] = pd.to_datetime(revenue_df['created'], format='%d-%m-%Y', errors='coerce')
        
        total_revenue = revenue_df["net_amount"].sum()
        total_sub_revenue = revenue_df[revenue_df.subscription.str.contains("Subscription", na=False)]["net_amount"].sum()
        total_monthly_sub_revenue = revenue_df[(revenue_df.subscription.str.contains("Subscription")) & revenue_df.subscription.str.contains("Month")]["net_amount"].sum()
        total_yearly_sub_revenue = revenue_df[(revenue_df.subscription.str.contains("Subscription")) & revenue_df.subscription.str.contains("Year")]["net_amount"].sum()
        
        total1, total2, total3, total4 = st.columns(4, gap='small')
        with total1:
            st.info('Total Revenue')
            st.metric(label="", value=f"$ {total_revenue:,.2f}")
        with total2:   
            st.info('Total Subscriptions Revenue')
            st.metric(label="", value=f"$ {total_sub_revenue:,.2f}")
        with total3:
            st.info('Total Monthly Subscriptions Revenue')
            st.metric(label="", value=f"$ {total_monthly_sub_revenue:,.2f}")
        with total4:
            st.info('Total Yearly Subscriptions Revenue')
            st.metric(label="", value=f"$ {total_yearly_sub_revenue:,.2f}")
        
        
        legacy_monthly_revenue = revenue_df[(revenue_df.subscription.str.contains("Legacy")) & revenue_df.subscription.str.contains("Month")]["net_amount"].sum()
        legacy_yearly_revenue = revenue_df[(revenue_df.subscription.str.contains("Legacy")) & revenue_df.subscription.str.contains("Yearly")]["net_amount"].sum()
        total_partners_monthly_sub_revenue = revenue_df[(revenue_df.subscription.str.contains("Professional")) & revenue_df.subscription.str.contains("Month")]["net_amount"].sum()
        total_partners_yearly_sub_revenue = revenue_df[(revenue_df.subscription.str.contains("Professional")) & revenue_df.subscription.str.contains("Yearly")]["net_amount"].sum()
        
        total1, total2, total3, total4 = st.columns(4, gap='small')
        with total1:
            st.info('Legacy Monthly Revenue')
            st.metric(label="", value=f"$ {legacy_monthly_revenue:,.2f}")
        with total2:   
            st.info('Legacy Yearly Revenue')
            st.metric(label="", value=f"$ {legacy_yearly_revenue:,.2f}")
        with total3:
            st.info('Total Partners Monthly Sub Revenue')
            st.metric(label="", value=f"$ {total_partners_monthly_sub_revenue:,.2f}")
        with total4:
            st.info('Total Partners Yearly Sub Revenue')
            st.metric(label="", value=f"$ {total_partners_yearly_sub_revenue:,.2f}")
        
        
        total_retail_monthly_sub_revenue = revenue_df[(revenue_df.description.str.contains("BrainTap")) & (revenue_df.description.str.contains("Monthly")) & (~revenue_df.description.str.contains("Legacy|Professional"))]["net_amount"].sum()
        total_retail_yearly_sub_revenue = revenue_df[(revenue_df.description.str.contains("BrainTap")) & (revenue_df.description.str.contains("Yearly")) & (~revenue_df.description.str.contains("Legacy|Professional"))]["net_amount"].sum()
        revenue_from_accessories = revenue_df[revenue_df['description'].str.contains('Charging Cable|Replacement Battery|Accessory Shipping')]['net_amount'].sum()
        revenue_from_products = revenue_df[revenue_df['description'].str.contains('Headset|Chair')]['net_amount'].sum()
        
        total1, total2, total3, total4 = st.columns(4, gap='small')
        with total1:
            st.info('Total Retailers Monthly Sub Revenue')
            st.metric(label="", value=f"$ {total_retail_monthly_sub_revenue:,.2f}")
        with total2:   
            st.info('Total Retailers Yearly Sub Revenue')
            st.metric(label="", value=f"$ {total_retail_yearly_sub_revenue:,.2f}")
        with total3:
            st.info('Revenue by Accessories')
            st.metric(label="", value=f"$ {revenue_from_accessories:,.2f}")
        with total4:
            st.info('Revenue by Products')
            st.metric(label="", value=f"$ {revenue_from_products:,.2f}")
        
        revenue_by_new_sub = charges_df[~charges_df['charge_description'].str.contains("Subscription update", na=False)]['charge_amount'].sum()
        revenue_by_renewed_sub =  charges_df[charges_df['charge_description'].str.contains("Subscription update", na=False)]['charge_amount'].sum()
        
        total1, total2 = st.columns(2, gap='small')
        with total1:
            st.info('Revenue by New Subscriptions')
            st.metric(label="", value=f"$ {revenue_by_new_sub:,.2f}")
        with total2:   
            st.info('Revenue by Renewed Subscriptions')
            st.metric(label="", value=f"$ {revenue_by_renewed_sub:,.2f}")
            

        search_term = st.text_input("Search by email:")

        # Filter data based on the search term
        filtered_df_search = filtered_df[
            (filtered_df['email'].str.contains(search_term, case=False, na=False)) 
        ]
        with st.expander("VIEW DATA"):
            showData = st.multiselect('Filter: ', filtered_df_search.columns, default=[
                'created', 'customer_id', 'email', 'phone', 'name',  'subscription', 'invoice_number',
                'description', 'quantity', 'currency', 'line_item_amount',
                'total_invoice_amount', 'discount', 'fee', 'tax', 'net_amount'
            ])
            st.dataframe(filtered_df_search[showData])

        # GEAPH 1 
        filtered_df['year_month'] = filtered_df['created'].dt.to_period('M')
        monthly_net_amount = filtered_df.groupby('year_month')['net_amount'].sum().reset_index() # Group the filtered dataframe by year_month and sum the net_amount column
        monthly_net_amount['year_month'] = monthly_net_amount['year_month'].astype(str) # Convert the year_month column to string type
        fig_1 = px.bar(monthly_net_amount, x='year_month', y='net_amount', title="Total Net Amount by Month",
                    labels={'year_month': 'Month', 'net_amount': 'Total Net Amount ($)'})# Create a bar plot using the Plotly Express library
        
        # GEAPH 2  
        monthly_tax = filtered_df.groupby('year_month')['tax'].sum().reset_index() # Group the filtered dataframe by year_month and sum the tax values
        monthly_tax['year_month'] = monthly_tax['year_month'].astype(str) # Convert the year_month column to string type
        fig_2 = px.bar(monthly_tax, x='tax', y='year_month', title="Total Tax by Month",
            labels={'year_month': 'Month', 'tax': 'Total Tax ($)'}) # Create a pie chart using the monthly_tax dataframe, with the tax values as the values, the year_month as the names, and the title as "Total Tax by Month"


        total1, total2 = st.columns(2, gap='small')
        with total1:
            st.plotly_chart(fig_1)

        with total2:
            st.plotly_chart(fig_2)

        # Graph 3
        filtered_df['total_invoice_amount'] = filtered_df['total_invoice_amount'].astype(int)# Convert the 'total_invoice_amount' column to integer type
        top_customers = filtered_df.groupby('email')['total_invoice_amount'].sum().reset_index()# Group the data by 'customer_id' and sum the 'total_invoice_amount' for each customer
        top_customers = top_customers.sort_values(by='total_invoice_amount', ascending=False).head(5)# Sort the data by 'total_invoice_amount' in descending order and select the top 10 customers
        fig_3 = px.pie(top_customers, names='email', values='total_invoice_amount', title='Top 5 Customers by Revenue')# Create a pie chart using Plotly Express with 'customer_id' on the x-axis and 'total_invoice_amount' on the y-axis

        # Graph 4
        revenue_by_product = product_df.groupby('description')['total_invoice_amount'].sum().reset_index() # Group the data by 'description' and sum the 'total_invoice_amount' for each product
        top_revenue_by_product = revenue_by_product.sort_values(by='total_invoice_amount', ascending=False).head(5) # Sort the values and get the top 10
        fig_4 = px.pie(top_revenue_by_product, values='total_invoice_amount', names='description', title='Top 5 Products by Revenue') # Create the pie chart visualization

        total1 ,total2 = st.columns(2, gap='small')
        with total1:
            st.plotly_chart(fig_3)

            with st.expander("VIEW DATA"): # Create an expander to display the data
                st.dataframe(top_customers)  # Display the top customers dataframe

        with total2:
            st.plotly_chart(fig_4, use_container_width=True)

            with st.expander("VIEW DATA"):
                st.dataframe(top_revenue_by_product)
        
        # Graph 5
        filtered_df['month'] = filtered_df['created'].dt.strftime('%Y-%m') # Convert the 'created' column to a string in the format 'YYYY-MM'
        tax_fee = filtered_df.groupby('month').agg({'tax': 'sum', 'fee': 'sum'}).reset_index() # Group the data by month and sum the 'tax' and 'fee' columns
        fig_5 = px.bar(tax_fee, x='month', y=['tax', 'fee'], title='Tax and Fee Analysis Over Time', labels={'month': 'Month'}) # Create a bar chart with the 'month' on the x-axis and 'tax' and 'fee' on the y-axis
        fig_5.update_xaxes(type='category') # Ensure the x-axis is treated as categorical
        st.plotly_chart(fig_5)

        with st.expander("VIEW DATA"):
            st.dataframe(tax_fee)

        # Graph 6
        subscription_analysis = filtered_df['subscription'].value_counts().reset_index() # Create a dataframe with the count of each subscription type
        subscription_analysis.columns = ['Subscription', 'Count'] # Rename the columns of the dataframe
        fig_6 = px.bar(subscription_analysis, x='Subscription', y='Count', title='Revenue by Subscription') # Create a bar chart with the subscription type on the x-axis and the count on the y-axis
        st.plotly_chart(fig_6)

        with st.expander("VIEW DATA"):
            st.dataframe(subscription_analysis)

    def Customers(self):
        customers_df = self.load_data_from_s3('customers')
        subscriptions_df = self.load_data_from_s3('subscriptions')
        cust_metadata_df = self.load_data_from_s3('customer_metadata')
        
        customers_df = customers_df[customers_df["deleted"]==False]
        
        # Convert 'trial_end' and 'created' to datetime
        subscriptions_df['trial_end'] = pd.to_datetime(subscriptions_df['trial_end'])
        subscriptions_df['created'] = pd.to_datetime(subscriptions_df['created'])

        # Sidebar filter for date range
        st.sidebar.header("Select Date Range:")
        start_date = st.sidebar.date_input("Start date", subscriptions_df['created'].min().date())
        end_date = st.sidebar.date_input("End date", subscriptions_df['created'].max().date())
        start_date = pd.to_datetime(start_date)
        end_date = pd.to_datetime(end_date)

        # Filter the subscription data
        filtered_sub_df = subscriptions_df[(subscriptions_df["trial_end"] >= start_date) & (subscriptions_df["trial_end"] <= end_date)]
        filtered_cust_sub_df = filtered_sub_df.merge(customers_df, left_on="customer_id", right_on="id", how="inner")
        # Filter data
        customers_df['created'] = pd.to_datetime(customers_df['created'], errors='coerce')
        filtered_df = customers_df[(customers_df['created'] >= pd.to_datetime(start_date)) & (customers_df['created'] <= pd.to_datetime(end_date))]

        

        # Calculate the total number of active, inactive, trialing, past due, paused, and incomplete expired subscriptions
        total_active = filtered_cust_sub_df[filtered_cust_sub_df["status"] == "active"].shape[0] # Calculate the total number of active customers
        total_inactive = filtered_cust_sub_df[filtered_cust_sub_df["status"] != "active"].shape[0] # Calculate the total number of inactive customers
        total_trialing = filtered_cust_sub_df[filtered_cust_sub_df["status"] == "trialing"].shape[0] # Calculate the total number of trialing customers

        total_customers = total_active + total_inactive + total_trialing
        total1 , total2 ,total3,total4 = st.columns(4)
        with total1:
            # Display churn rate in metrics
            st.info('Total Customers')
            st.metric(label="Total Customers", value=f" {total_customers:,.0f}")
        with total2:
            st.info('Active Customers')
            st.metric(label="Active Customers", value=f" {total_active:,.0f}")
        
        with total3:
            st.info('Inactive Customers')
            st.metric(label="Inactive Customers", value=f" {total_inactive:,.0f}")
        with total4:
            st.info('Trialing Customers')
            st.metric(label="Trialing Customers", value=f" {total_trialing:,.0f}")
        
        today = customers_df['created'].dt.date.max()
        last7days = today - datetime.timedelta(days=7)
        last30days = today - datetime.timedelta(days=30)
        last1year = today - datetime.timedelta(days=365)

        # today customer 
        new_users_today = customers_df[customers_df['created'].dt.date == today]['id'].nunique()
        new_users_last7days = customers_df[(customers_df['created'].dt.date >= last7days) & (customers_df['created'].dt.date < today)]['id'].nunique()
        new_users_last30days = customers_df[(customers_df['created'].dt.date >= last30days) & (customers_df['created'].dt.date < today)]['id'].nunique()
        new_users_1_year = customers_df[(customers_df['created'].dt.date >= last1year) & (customers_df['created'].dt.date < today)]['id'].nunique()

        
        st.subheader("New Customers")
        total1, total2, total3,total4 = st.columns(4, gap='small')
        with total1 :
            st.info('Today')
            st.metric(label="", value=f'{new_users_today}')
        with total2:
            st.info('Last 7 Days')
            st.metric(label="", value=f'{new_users_last7days}')
        with total3:   
            st.info('Last 30 Days')
            st.metric(label="", value=f'{new_users_last30days}')
        with total4:
            st.info('Last 1 Year')
            st.metric(label="", value=f'{new_users_1_year}')
        
        # st.subheader("Search by email:")
        search_term = st.text_input("Search by email:")

        # Filter data based on the search term
        filtered_df_search = filtered_cust_sub_df[
            (filtered_cust_sub_df['email'].str.contains(search_term, case=False, na=False)) 
        ]

        # Display filtered data only in the dataframe
        with st.expander("VIEW DATA"):
            st.dataframe(filtered_df_search[['customer_id','name','phone','email', 'status','trial_start', 'trial_end', ]], use_container_width=True)
        
        
        #Graph 1
        filtered_df['created'] = pd.to_datetime(filtered_df['created']) # Convert 'created' to datetime if it's not already
        current_date = pd.to_datetime("today") # Filter data for the last 6 months
        start_date = current_date - pd.DateOffset(months=6)
        filtered_customers = filtered_df[filtered_df['created'] >= start_date]
        filtered_customers.set_index('created', inplace=True) # Group by month and count new customers
        monthly_new_customers = filtered_customers.resample('ME').size().reset_index(name='new_customers_count')
        monthly_new_customers['year_month'] = monthly_new_customers['created'].dt.strftime('%Y-%m') # Correctly align data with the months
        monthly_new_customers = monthly_new_customers.sort_values(by='created', ascending=True) # Sort by 'year_month' in ascending order
        st.subheader('New Customer Sign-Up Trend')
        # Plot the data
        fig = px.bar(
            monthly_new_customers,
            x='year_month',
            y='new_customers_count',
            title="New Customer Sign-Ups by Month",
            width=1200,
            height=400,
            color_discrete_sequence=['#636EFA']
        )

        fig.update_layout(
            xaxis_title='Month',
            yaxis_title='New Customers Count',
            barmode='group',
            bargap=0.15,
            bargroupgap=0.1
        )

        st.plotly_chart(fig)
        
        #Graph 2
        # Filter data for the last 6 months
        df_sign_up = filtered_df[["id", "created"]]
        df_sign_up["created"] = pd.to_datetime(df_sign_up["created"])
        df_sign_up["Month_year"] = df_sign_up["created"].dt.strftime('%Y-%m')
        df_sign_up = df_sign_up[["id", "Month_year"]]
        df_sign_up["Cust_count_month"] = df_sign_up.groupby("Month_year")["id"].transform('count')
        df_sign_up_data = df_sign_up[["Month_year", "Cust_count_month"]]
        df_sign_up_data = df_sign_up_data.drop_duplicates()
        df_sign_up_data = df_sign_up_data.sort_values(by=['Month_year'], ascending=False)
        df_sign_up_data.reset_index(drop=True, inplace=True)
        with st.expander("VIEW DATA"):
            st.dataframe(df_sign_up_data, use_container_width=True) #
                
    
        geo_data = filtered_df[['shipping_address_city', 'shipping_address_country']].dropna()
        city_counts = geo_data['shipping_address_city'].value_counts().reset_index()
        city_counts.columns = ['City', 'Count']

        fig = px.bar(city_counts.head(10), x='City', y='Count', title='Top 10 Cities by Customer Count')
        st.plotly_chart(fig)

        #Graph 3
        # Display an interactive table
        city_counts = filtered_df['shipping_address_city'].value_counts().reset_index()
        city_counts.columns = ['City', 'Count']
        with st.expander("VIEW DATA"):
            st.dataframe(city_counts)

        # Prepare data for the donut chart
        country_counts = filtered_df['shipping_address_country'].value_counts().reset_index()
        country_counts.columns = ['Country', 'Count']

        fig = px.pie(country_counts.head(5), values='Count', names='Country', title='Top 5 Countries by Customer Count', hole=0.4)

        fig.update_traces(textinfo='percent+label')
        fig.update_layout(annotations=[dict(text='Countries', x=0.5, y=0.5, font_size=20, showarrow=False)])
        st.plotly_chart(fig)

        st.subheader("Customers by Source")

        # Key Filter
        keys = cust_metadata_df['key'].unique()
        selected_key = st.selectbox("Select Key", keys)
        
        # Filter Data
        filtered_data = cust_metadata_df[cust_metadata_df['key'] == selected_key]
        
        # Count occurrences of each source (value)
        value_counts = filtered_data['value'].value_counts().reset_index()
        value_counts.columns = ['value', 'count']
        
        # Sort the data by count (high to low)
        value_counts = value_counts.sort_values(by='count', ascending=False).reset_index(drop=True)
        
        # Create Pie Chart with Proper Sorting
        pie_chart = alt.Chart(value_counts).mark_arc().encode(
            theta=alt.Theta(field='count', type='quantitative', stack=True),
            color=alt.Color('value:N', title='Source', 
                            sort=value_counts['value'].tolist(),  # Sort explicitly by value
                            scale=alt.Scale(scheme='tableau10')),
            tooltip=[alt.Tooltip('value:N', title='Source'), 
                    alt.Tooltip('count:Q', title='Count')]
        ).properties(
            width=400,
            height=400,
            title=f"Distribution of Sources for Key: {selected_key}"
        )
        
        # Display Chart
        st.altair_chart(pie_chart, use_container_width=True)
        
        # Expander to View Data
        with st.expander("View Data"):
            st.dataframe(value_counts)


    def Subscriptions(self):
        st.title("Subscriptions")
        subscriptions_df = self.load_data_from_s3('subscriptions')
        customers_df = self.load_data_from_s3('customers')
        revenue_df = self.load_data_from_s3('revenue')

        # Convert 'trial_end' and 'created' to datetime
        subscriptions_df['trial_end'] = pd.to_datetime(subscriptions_df['trial_end'])
        subscriptions_df['created'] = pd.to_datetime(subscriptions_df['created'])
        revenue_df['created'] = pd.to_datetime(revenue_df['created'])

        # Sidebar filter for date range
        st.sidebar.header("Select Date Range:")
        start_date = st.sidebar.date_input("Start date", subscriptions_df['created'].min().date())
        end_date = st.sidebar.date_input("End date", subscriptions_df['created'].max().date())
        start_date = pd.to_datetime(start_date)
        end_date = pd.to_datetime(end_date)
        
        

        # Filter the subscription data
        filtered_sub_df = subscriptions_df[(subscriptions_df["trial_end"] >= start_date) & (subscriptions_df["trial_end"] <= end_date)]
        filtered_cust_sub_df = filtered_sub_df.merge(customers_df, left_on="customer_id", right_on="id", how="inner")

        
        st.subheader("Upcoming Subscription End Customers")
        search_term = st.text_input("Search by email:")

        # Filter data based on the search term
        filtered_df_search = filtered_cust_sub_df[
            (filtered_cust_sub_df['email'].str.contains(search_term, case=False, na=False)) 
        ]

        with st.expander("VIEW DATA"):
            filtered_cust_sub_df['trial_start'] = pd.to_datetime(filtered_cust_sub_df['trial_start']).dt.date
            filtered_cust_sub_df['trial_end'] = pd.to_datetime(filtered_cust_sub_df['trial_end']).dt.date
            showData = st.multiselect('Filter: ', filtered_df_search.columns, default=[
                "name", "phone", "email", "trial_start","trial_end"])
            st.dataframe(filtered_df_search[showData], use_container_width=True) 

        customer_df_temp = customers_df[["id","name","email"]]
        customer_df_temp.rename({"id":"cust_id"},axis=1, inplace=True)
        merged_df = pd.merge(customer_df_temp, subscriptions_df, left_on='cust_id', right_on='customer_id', how='inner')

        merged_df["description"] =merged_df["description"].fillna("No sub")
        total_users = merged_df.shape[0]
        total_no_of_sub = merged_df[merged_df["description"]!='No sub'].shape[0]
        total_monthly_sub = merged_df[merged_df["description"].str.contains('Monthly|month|Month')].shape[0]
        total_yearly_sub = merged_df[merged_df["description"].str.contains('Yearly|year|Year')].shape[0]
        total_promo_sub = merged_df[merged_df["description"].str.contains('Promo|promo')].shape[0]

        total_Legacy_Monthly_Sub = merged_df[(merged_df["description"].str.contains('Legacy')) & merged_df["description"].str.contains('Monthly')].shape[0]
        total_Legacy_Yearly_Sub = merged_df[(merged_df["description"].str.contains('Legacy')) & merged_df["description"].str.contains('Yearly')].shape[0]
        total_partners_monthly = merged_df[(merged_df["description"].str.contains('Professional')) & merged_df["description"].str.contains('Monthly')].shape[0]
        total_partners_yearly = merged_df[(merged_df["description"].str.contains('Professional')) & merged_df["description"].str.contains('Yearly')].shape[0]

        partners = merged_df[merged_df["description"].str.contains('Professional')]
        total_no_of_users_trail = merged_df[merged_df["status"]=="trialing"].shape[0]
        total_no_of_Partners_trail = partners[partners["status"]=="trialing"].shape[0]
        retailers =merged_df[merged_df["description"].str.contains("BrainTap Yearly Subscription|BrainTap Monthly Subscription")]
        total_no_of_retails_trail = retailers[retailers["status"]=="trialing"].shape[0]

        total_retail_Monthly_sub = merged_df[merged_df["description"].str.contains("BrainTap Monthly Subscription")].shape[0]
        total_retail_yearly_sub =merged_df[merged_df["description"].str.contains("BrainTap Yearly Subscription")].shape[0]

        


        # Calculate the total number of active, inactive, trialing, past due, paused, and incomplete expired subscriptions
        total_active = filtered_sub_df[filtered_sub_df["status"] == "active"].shape[0] # Calculate the total number of active customers
        total_inactive = filtered_sub_df[filtered_sub_df["status"] != "active"].shape[0] # Calculate the total number of inactive customers
        total_trialing = filtered_sub_df[filtered_sub_df["status"] == "trialing"].shape[0] # Calculate the total number of trialing customers
        total_past_due = filtered_sub_df[filtered_sub_df["status"] == "past_due"].shape[0] # Calculate the total number of past due customers
        total_paused = filtered_sub_df[filtered_sub_df["status"] == "paused"].shape[0] # Calculate the total number of paused customers
        total_incomplete_expired = subscriptions_df[subscriptions_df["status"] == "incomplete_expired"].shape[0] # Calculate the total number of incomplete expired subscriptions


        total1, total2,total3, total4 = st.columns(4,gap ='small')
        with total1:
            st.info('Total Users')
            st.metric("",total_users)
        with total2:
            st.info('Total Subscriptions')
            st.metric("",total_no_of_sub)
        with total3:
            st.info("Total Montly Subscriptions")
            st.metric("", total_monthly_sub)
        with total4:
            st.info("Total Yearly Subscriptions")
            st.metric("", total_yearly_sub)
        
        total1, total2, total3, total4 = st.columns(4, gap ='small')
        with total1:
            st.info("Total Promo Subscriptions")
            st.metric("", total_promo_sub)
        with total2:
            st.info("Total Legacy Monthly Subscriptions")
            st.metric("", total_Legacy_Monthly_Sub)
        with total3:
            st.info("Total Legacy Yearly Subscriptions")
            st.metric("", total_Legacy_Yearly_Sub)
        with total4:
            st.info("Total Partners Monthly")
            st.metric("", total_partners_monthly)

        
        total1, total2, total3 ,  total4= st.columns(4, gap ='small')
        with total1:
            st.info("Total Partners Yearly")
            st.metric("", total_partners_yearly)
            
        with total2:
            st.info("Total Users on Trail")
            st.metric("", total_no_of_users_trail)
        with total3:
            st.info("Total Partners on Trail")
            st.metric("", total_no_of_Partners_trail)
        with total4 :
            st.info("Total Retailers on Trail ")
            st.metric("", total_no_of_retails_trail)

        
        total1, total2,total3, total4  = st.columns(4, gap ='small')
        with total1:
            st.info("Total Retail on Monthly Sub")
            st.metric("", total_retail_Monthly_sub)
        with total2:
            st.info("Total Retail on Yearly Sub")
            st.metric("", total_retail_yearly_sub)
        with total3:
            st.info('Total Active Subscriptions')
            st.metric(label="", value=str(total_active))        
        with total4:
            st.info('Total Inactive Subscriptions')
            st.metric(label="", value=str(total_inactive))

        # Create columns in Streamlit
        total1, total2, total3, total4 = st.columns(4, gap='small')

        # Display total active and inactive subscriptions in the columns
        with total1:
            st.info('Total Trialing Subscriptions')
            st.metric(label="", value=str(total_trialing))    
        with total2:
            st.info('Past Due Subscriptions')
            st.metric(label="", value=str(total_past_due))
        with total3:
            st.info('Total Paused Subscriptions')
            st.metric(label="", value=str(total_paused))
        with total4:
            st.info('Incomplete Expired Subscriptions')
            st.metric(label="", value=str(total_incomplete_expired))

        total_payment_failed = subscriptions_df[subscriptions_df["status"] == "canceled"].shape[0] # Calculate the total number of payment failed subscriptions
        partners = merged_df[merged_df["description"].str.contains('Professional')]
        total_partners_failed_payment =  partners[partners["status"] == "canceled"].shape[0] # Calculate the total number of payment failed subscriptions
        total_retail_failed_payment =  retailers[retailers["status"] == "canceled"].shape[0] # Calculate the total number of payment failed subscriptions
        total_Legacy_failed_payment = merged_df[(merged_df["description"].str.contains('Legacy')) & merged_df["status"] == "canceled"].shape[0]
        # ZeroDivisionError: divis
        total1, total2, total3, total4 = st.columns(4, gap='small')
        with total1:
            st.info('Total Payment Failed Subscriptions')
            st.metric(label="", value=str(total_payment_failed))
        with total2:
            st.info('Total Payment Failed Partners')
            st.metric(label="", value=str(total_partners_failed_payment))
        with total3:
            st.info('Total Payment Failed Retailers')
            st.metric(label="", value=str(total_retail_failed_payment))
        with total4:
            st.info('Total Legacy Monthly Subscriptions')
            st.metric(label="", value=str(total_Legacy_failed_payment))

        #Subscriber Growth Rate (By all above categories)
        try:
            sub_growth_rate = ((total_active - total_inactive) / total_inactive) * 100
        except ZeroDivisionError:
            sub_growth_rate = 0
        #Churn Rate (By all above categories)
        try:
            churn_rate = ((total_inactive - total_active) / total_active) * 100
        except ZeroDivisionError:
            churn_rate = 0
        # Trial Conversion (By all above categories)
        try:
            trail_conversion = ((total_active - total_trialing) / total_trialing) * 100
        except ZeroDivisionError:
            trail_conversion = 0
        # Canceled due to Faild  
        try:
            canceld_due_to_failed = ((total_payment_failed - total_partners_failed_payment - total_retail_failed_payment - total_Legacy_failed_payment) / total_payment_failed) * 100
        except ZeroDivisionError:
            canceld_due_to_failed = 0
        
        total1,total2,total3,total4 = st.columns(4, gap='small')
        with total1 :
            st.info('Subscriber Growth Rate')
            st.metric(label="", value=f'{sub_growth_rate:.2f}%')
        with total2 :
            st.info('Churn Rate')
            st.metric(label="", value=f'{churn_rate:.2f}%')
        with total3 :
            st.info('Trial Conversion')
            st.metric(label="", value=f'{trail_conversion:.2f}%')
        with total4:
            st.info('Canceled due to Failed')
            st.metric(label="", value=f'{canceld_due_to_failed:.2f}')
        
                # Ensure the 'created_date' column is in datetime format
        merged_df['created'] = pd.to_datetime(merged_df['created'])

        # Extract counts per date for each subscription type
        legacy_monthly = merged_df[
            (merged_df["description"].str.contains('Legacy')) &
            (merged_df["description"].str.contains('Monthly'))
        ].groupby('created').size()

        partners_monthly = merged_df[
            (merged_df["description"].str.contains('Professional')) &
            (merged_df["description"].str.contains('Monthly'))
        ].groupby('created').size()

        retail_monthly = merged_df[
            merged_df["description"].str.contains("BrainTap Monthly Subscription")
        ].groupby('created').size()

        # Combine data into a single DataFrame for plotting
        line_chart_data = pd.DataFrame({
            'Legacy Monthly Sub': legacy_monthly,
            'Partners Monthly Sub': partners_monthly,
            'Retail Monthly Sub': retail_monthly
        }).fillna(0)

        # Plot the line chart
        plt.figure(figsize=(12, 6))
        for column in line_chart_data.columns:
            plt.plot(line_chart_data.index, line_chart_data[column], label=column)

        plt.title('Monthly Subscription Trends')
        plt.xlabel('Date')
        plt.ylabel('Number of Subscriptions')
        plt.legend()
        plt.grid()
        plt.show()



        # today = filtered_sub_df['created'].dt.date.max()
        # last7days_sub_sold= today - datetime.timedelta(days=7)
        # last15days_sub_sold = today - datetime.timedelta(days=15)
        # last1month_sub_sold = today - datetime.timedelta(days=30)
        # last1year_sub_sold = today - datetime.timedelta(days=365)

        # sub_sold_7days = filtered_sub_df[filtered_sub_df['created'] > last7days_sub_sold]
        # sub_sold_15days = filtered_sub_df[filtered_sub_df['created'] > last15days_sub_sold]
        # sub_sold_1month = filtered_sub_df[filtered_sub_df['created'] > last1month_sub_sold]
        # sub_sold_1year = filtered_sub_df[filtered_sub_df['created'] > last1year_sub_sold]

        # st.subheader("Subscriptions Sold")
        # total1,total2,total3,total4 = st.columns(4, gap='small')
        # with total1 :
        #     st.info('Last 7 Days')
        #     st.metric(label="", value=f'{sub_sold_7days}')
        # with total2 :   
        #     st.info('Last 15 Days')
        #     st.metric(label="", value=f'{sub_sold_15days}')
        # with total3 :
        #     st.info('Last 1 Month')
        #     st.metric(label="", value=f'{sub_sold_1month}')
        # with total4:
        #     st.info('Last 1 Year')
        #     st.metric(label="", value=f'{sub_sold_1year}')

        # today = filtered_sub_df['trial_end'].dt.date.max()
        # last7days_sub_renewed= today - datetime.timedelta(days=7)
        # last15days_sub_renewed = today - datetime.timedelta(days=15)
        # last1month_sub_renewed = today - datetime.timedelta(days=30)
        # last1year_sub_renewed = today - datetime.timedelta(days=365)

        # sub_7trial = filtered_sub_df[filtered_sub_df['trial_end'] > last7days_sub_renewed]
        # sub_15trial = filtered_sub_df[filtered_sub_df['trial_end'] > last15days_sub_renewed]
        # sub_1monthtrial = filtered_sub_df[filtered_sub_df['trial_end'] > last1month_sub_renewed]
        # sub_1yeartrial = filtered_sub_df[filtered_sub_df['trial_end'] > last1year_sub_renewed]
        
        # st.subheader("Subscriptions Renewed")
        # total1,total2,total3,total4 = st.columns(4, gap='small')
        # with total1 :
        #     st.info('Last 7 Days')
        #     st.metric(label="", value=f'{sub_7trial}')
        # with total2 :   
        #     st.info('Last 15 Days')
        #     st.metric(label="", value=f'{sub_15trial}')
        # with total3 :
        #     st.info('Last 1 Month')
        #     st.metric(label="", value=f'{sub_1monthtrial}')
        # with total4:
        #     st.info('Last 1 Year')
        #     st.metric(label="", value= f'{sub_1yeartrial}')
        
        # # Display upcoming subscription end customers
        # st.subheader("Upcoming Subscription End Customers")
        # with st.expander("VIEW DATA"):
            # filtered_cust_sub_df['trial_start'] = pd.to_datetime(filtered_cust_sub_df['trial_start']).dt.date
            # filtered_cust_sub_df['trial_end'] = pd.to_datetime(filtered_cust_sub_df['trial_end']).dt.date
            # showData = st.multiselect('Filter: ', filtered_cust_sub_df.columns, default=[
            #     "name", "phone", "email", "trial_start","trial_end"])
            # st.dataframe(filtered_cust_sub_df[showData], use_container_width=True) 


        # Graph 2
        # Monthly Active Subscriptions
        filtered_sub_df["month"] = filtered_sub_df["created"].dt.to_period('M').astype(str)
        monthly_active_subs = filtered_sub_df.groupby("month")["customer_id"].count().reset_index()
        fig_monthly_2 = px.bar(monthly_active_subs, x="month", y="customer_id", title="Monthly Active Subscriptions")
        st.plotly_chart(fig_monthly_2)

        # Graph 3
        # Daily Active Subscriptions
        filtered_sub_df = filtered_sub_df[filtered_sub_df["status"] == "active"] # Filter the dataframe to only include rows where the subscription status is active
        filtered_sub_df["day"] = filtered_sub_df["created"].dt.strftime('%Y-%m-%d') # Create a new column in the dataframe that contains the date of the subscription creation
        daily_active_subs = filtered_sub_df.groupby("day")["customer_id"].count().reset_index() # Group the dataframe by the date of subscription creation and count the number of unique customer IDs for each date
        fig_daily_3 = px.bar(daily_active_subs, x="day", y="customer_id", title="Daily Active Subscriptions") # Create a bar chart using Plotly Express to display the number of active subscriptions for each date
        fig_daily_3.update_layout(
            xaxis_title='Date',
            yaxis_title='Number of Active Subscriptions',
            xaxis_tickformat='%Y-%m-%d'
        ) # Update the layout of the bar chart to include titles for the x and y axes and format the x-axis tick labels
        st.plotly_chart(fig_daily_3)




        merged_df = pd.merge(revenue_df, subscriptions_df, on="customer_id", how="left")

        # Streamlit App
        st.subheader("Subscription status")

        # Selectbox for filtering by subscription
        if 'subscription' in merged_df.columns:
            unique_subscriptions = ["All"] + list(merged_df["subscription"].unique())
            selected_subscription = st.selectbox(
                "Filter by Subscription Type",
                options=unique_subscriptions,
                index=0  # Default selects "All"
            )

            # Apply filter
            if selected_subscription == "All":
                filtered_df = merged_df  # Show all data by default
            else:
                filtered_df = merged_df[merged_df["subscription"] == selected_subscription]

            # Pie chart for status distribution
            status_counts = filtered_df["status"].value_counts().reset_index()
            status_counts.columns = ["status", "count"]
            fig = px.pie(status_counts, values="count", names="status", title="Subscription Status ")
            st.plotly_chart(fig)
        else:
            st.warning("The 'subscription' column is not present in the dataset.")
            st.dataframe(merged_df)  # Show all data by default

        with st.expander("VIEW DATA"):
            # Display the filtered DataFrame with an additional column for total count of each unique subscription
            subscription_counts = filtered_df['subscription'].value_counts().reset_index()
            subscription_counts.columns = ['subscription', 'subscription_total_count']
            st.dataframe(subscription_counts, use_container_width=True)

        subscriptions_df['created'] = pd.to_datetime(subscriptions_df['created'])
        subscriptions_df['month'] = subscriptions_df['created'].dt.to_period('M')
        compare = subscriptions_df.groupby(['status','month']).agg(total_users=('customer_id', 'count')).reset_index()
        compare.sort_values(by= 'month')

                # Convert created column to datetime and extract month
        subscriptions_df['created'] = pd.to_datetime(subscriptions_df['created'])
        subscriptions_df['month'] = subscriptions_df['created'].dt.to_period('M')

        # Group by status and month to calculate total users
        compare = subscriptions_df.groupby(['status', 'month']).agg(total_users=('customer_id', 'count')).reset_index()
        compare['month'] = compare['month'].dt.to_timestamp()  # Convert Period to Timestamp for plotting
        compare.sort_values(by='month', inplace=True)

        # Streamlit App
        st.subheader("Subscription Trends Analysis")

        # Line chart
        fig = px.line(
            compare,
            x='month',
            y='total_users',
            color='status',
            title="Monthly Trends in Subscription Status",
            labels={'month': 'Month', 'total_users': 'Total Users'},
            markers=True
        )

        st.plotly_chart(fig)



    def Payment(self):
        st.title("Payment Dashboard")
        payment_df = self.load_data_from_s3('payment')

        st.sidebar.header("Select Date Range:")
        payment_df['created_date'] = pd.to_datetime(payment_df['created_date'], errors='coerce')

        start_date = st.sidebar.date_input("Start date", payment_df["created_date"].min().date())
        end_date = st.sidebar.date_input("End date", payment_df["created_date"].max().date())

        # Filter data
        filtered_df  = payment_df[(payment_df['created_date'] >= pd.to_datetime(start_date)) & (payment_df['created_date'] <= pd.to_datetime(end_date))]
        
        search_term = st.text_input("Search by email:")

        # Filter data based on the search term
        filtered_df_search = filtered_df[
            (filtered_df['description'].str.contains(search_term, case=False, na=False)) 
        ]
        # Display data
        with st.expander("VIEW DATA"):
            # filtered_df['created'] = pd.to_datetime(filtered_df['created']).dt.date
            showData = st.multiselect('Filter: ', filtered_df_search.columns, default=[
                'id', 'amount','description', 'amount_refunded', 'balance_transaction_id',
                'calculated_statement_descriptor',  'currency', 'customer_id',
                'status'])
            st.dataframe(filtered_df_search[showData], use_container_width=True)

        total_transactions = filtered_df.shape[0] # Calculate the total number of transactions
        successful_transactions = filtered_df[filtered_df["status"] == "succeeded"].shape[0] # Calculate the number of successful transactions
        failed_transactions = filtered_df[filtered_df["status"] == "failed"].shape[0] # Calculate the number of failed transactions

        total1, total2, total3 = st.columns(3, gap='small')
        with total1:
            st.info('Total Transactions')
            st.metric(label="Total Transactions", value=f" {total_transactions:,.0f}")

        with total2:
            st.info('Number of successful transactions')
            st.metric(label="Number of successful transactions:", value=f"{successful_transactions:,.0f}")

        with total3:
            st.info('Number of failed transactions')
            st.metric(label="Number of failed transactions:", value=f"{failed_transactions:,.0f}")

        st.markdown("---")
        
        # Graph 1
        # Pie chart
        total1, total2 = st.columns(2, gap='small')
        with total1:
            refunded_line_items = filtered_df[filtered_df["refunded"] == True]["description"].value_counts() # Filter the dataframe to only include rows where the "refunded" column is True
            top_2 = refunded_line_items.head(2)
            other = refunded_line_items[2:].sum() if len(refunded_line_items) > 2 else 0
            top_2_with_other = pd.concat([top_2, pd.Series({'Other': other})])

            fig_1 = px.pie(values=top_2_with_other, names=top_2_with_other.index, title="Top 2 Refunded Line Items and Others",
                        labels={'index': 'Refunded Items', 'values': 'Count'}, hole=0.3)
            st.plotly_chart(fig_1)
        
        # Graph 2
        with total2:
            status_counts = filtered_df['status'].value_counts() # Count the number of times each status appears in the filtered dataframe
            if not status_counts.empty and 'succeeded' in status_counts and 'failed' in status_counts: # Check if the dataframe is not empty and if 'succeeded' and 'failed' statuses exist
                succeeded_count = status_counts['succeeded'] # Get the count of 'succeeded' and 'failed' statuses
                failed_count = status_counts['failed']
                labels = ['Succeeded', 'Failed']  # Prepare the data for the pie chart
                values = [succeeded_count, failed_count]
                fig_2 = px.pie(values=values, names=labels, title="Payment Status Distribution",
                            labels={'index': 'Payment Status', 'values': 'Count'}, hole=0.3)  # Create a Plotly pie chart for payment statuses
                st.plotly_chart(fig_2)
            else:
                st.write("No data available for succeeded or failed payments.") # If the dataframe is empty or 'succeeded' and 'failed' statuses do not exist, display a message

        # Graph 3
        failure_reasons = (filtered_df["failure_code"].value_counts(normalize=True).head() * 100).round(2) # Calculate the percentage of each failure reason in the filtered dataframe
        failure_reasons_df = failure_reasons.reset_index() # Reset the index of the failure_reasons dataframe
        failure_reasons_df.columns = ['Failure Reason', 'Percentage'] # Rename the columns of the failure_reasons dataframe
        fig_3 = px.bar(
            failure_reasons_df, 
            x='Failure Reason', 
            y='Percentage',
            title="Top 5 Failure Reasons",
            labels={'Failure Reason': 'Failure Reason', 'Percentage': 'Percentage (%)'},
            text='Percentage',
            width=800,  # Adjusted width
            height=600
        ) # Create a bar chart using Plotly Express
        fig_3.update_traces(texttemplate='%{text:.2f}%', textposition='outside') # Update the text of the bar chart to display the percentage
        fig_3.update_layout(
            xaxis_title='Failure Reason', 
            yaxis_title='Percentage (%)', 
            xaxis_tickangle=320,
            margin=dict(l=20, r=20, t=40, b=20),  # Adjust margins if needed
        ) # Update the layout of the bar chart
        st.plotly_chart(fig_3) # Plot the bar chart using Streamlit

        # Graph 4
        refunded_amounts = filtered_df[filtered_df["amount_refunded"] > 0]["amount_refunded"].value_counts().head() # Get the value counts of the refunded amounts in the filtered dataframe
        st.subheader("Most Frequent Refunded Amounts") # Create a subheader for the most frequent refunded amounts
        st.bar_chart(refunded_amounts,x_label="Amount Refunded", y_label="Count") # Create a bar chart of the most frequent refunded amounts

    def financial(self):
        financial_df = self.load_data_from_s3('financial')
        
        st.title("Financial Dashboard")
    
        
        # Sidebar options
        st.sidebar.header("Select Date Range:")
        financial_df['month'] = pd.to_datetime(financial_df['month'], errors='coerce')

        start_date = st.sidebar.date_input("Start date", financial_df["month"].min().date())
        end_date = st.sidebar.date_input("End date", financial_df["month"].max().date())

        # Filter data
        filtered_df = financial_df[(financial_df['month'] >= pd.to_datetime(start_date)) & (financial_df['month'] <= pd.to_datetime(end_date))]

        # Create an expander to view the data
        with st.expander("VIEW DATA"):
            showData = st.multiselect('Filter: ',  filtered_df.columns, default=[
                'month','currency','total_sales','total_refunds','total_payouts','net_profit_loss'])
            st.dataframe( filtered_df[showData], use_container_width=True)


        total_sales = filtered_df['total_sales'].sum() # Calculate the total sales from the filtered dataframe
        total_refunds = filtered_df['total_refunds'].sum() # Calculate the total refunds from the filtered dataframe
        total_payouts = filtered_df['total_payouts'].sum() # Calculate the total payouts from the filtered dataframe
        net_profit_loss = filtered_df['net_profit_loss'].sum() # Calculate the net profit or loss from the filtered dataframe


        total1, total2 = st.columns(2, gap='small')

        with total1:
            st.info('Total Sales',icon="💸")
            st.metric(label="Total Sales", value=f"$ {total_sales:,.0f}")

        with total2:
            st.info('Total Refunds',icon="💸")
            st.metric(label="Total Refunds:", value=f"$ {total_refunds:,.0f}")


        total3, total4 = st.columns(2, gap='small')

        with total3:
            st.info('Total Payouts',icon="💸")
            st.metric(label="Total Payouts:", value=f"$ {total_payouts:,.0f}")

        with total4:
            st.info('Net Pofit & Loss',icon="📊")
            st.metric(label="Net Pofit & Loss:", value=f"$ {net_profit_loss:,.0f}")

        

        # Plotting the data
        st.header("Financial Overview")
        total1, total2 = st.columns(2, gap='small')

        with total1:
            fig_sales = px.bar(filtered_df, x='month', y='total_sales', title='Total Sales Over Time')
            st.plotly_chart(fig_sales)


        with total2:
            fig_refunds = px.bar(filtered_df, x='month', y='total_refunds', title='Total Refunds Over Time')
            st.plotly_chart(fig_refunds)

        total3, total4 = st.columns(2, gap='medium')

        with total3:
            fig_payouts = px.bar(filtered_df, x='month', y='total_payouts', title='Total Payouts Over Time')
            st.plotly_chart(fig_payouts)

        with total4:
            fig_net_profit_loss = px.bar(filtered_df, x='month', y='net_profit_loss', title='Net Profit/Loss Over Time')
            st.plotly_chart(fig_net_profit_loss)



    def main(self):
        with st.sidebar:
            selected = option_menu(
                menu_title="Select a Page",
                options=["Summary", "Subscriptions", "Customers", "Payment", "Revenue", "Financial"],
                icons=["", "cash", "people", "bar-chart", "credit-card", "file-text"],
                menu_icon="cast",
                default_index=0
            )

        if selected == "Summary":
            self.Summary()
        elif selected == "Revenue":
            self.Revenue()
        elif selected == "Customers":
            self.Customers()
        elif selected == "Subscriptions":
            self.Subscriptions()
        elif selected == "Payment":
            self.Payment()
        elif selected == "Financial":
            self.financial()

if __name__ == "__main__":
    
    dashboard = Dashboard()
    dashboard.main()
