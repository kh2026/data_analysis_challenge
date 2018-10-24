# -*- coding: utf-8 -*-
"""
Created on Sun Oct 21 19:19:45 2018

@author: Kevin Huang
"""

import pandas as pd
import numpy as np
from scipy.stats.stats import linregress
import pylab as pl
import datetime
import calendar



df = pd.read_csv('data_challenge_transactions.csv')
current_day = datetime.date(2016, 5, 1)

# convert transaction date and join date to datetime format
df['transaction_date'] = pd.to_datetime(df['transaction_date'])
df['join_date'] = pd.to_datetime(df['join_date'])

# clean data of rows with missing information
df = df.dropna()
# clean data of invalid rows where the join date is later than the transaction date
dropped = []
for index, row in df.iterrows():  
    if int((row['transaction_date'] - row['join_date']).days) < 0:
        dropped.append(index)
df = df.drop(dropped)





# get the sales in every month and year
monthly_sales = {}
yearly_sales = {}
for year in range(2013,2017):
    for month in range(1,13):
        sales = df[(df['transaction_date'].dt.year == year) & (df['transaction_date'].dt.month == month)]  
        period = str(month) + "/" + str(year)
        monthly_sales[period] = sales['sales_amount'].sum()
    sales = df[(df['transaction_date'].dt.year == year)] 
    yearly_sales[year] = sales['sales_amount'].sum()
# remove months wehere sales is 0 
monthly_sales = {k:v for (k,v) in monthly_sales.items() if v > 0}
# delete 2016 sales since its not a full year
del yearly_sales[2016]




#group by region and get information for every region
region_info = {}
for region in range(ord('A'), ord('U') +1):
    region_info[chr(region)] = df[df['region'] == chr(region)]

transactions_per_region = {}
for region, info in region_info.items():
    transactions_per_region[region] = info.shape[0]

sales_per_region = {}
for region, info in region_info.items():
    sales_per_region[region] = info['sales_amount'].sum()
    
customers_per_region = {}
for region, info in region_info.items():
    customers_per_region[region] = (info.groupby('user').size()).shape[0]

growth_per_region = {}
avg_growth_per_region = {}
for region, info in region_info.items():
    s = info[(info['transaction_date'].dt.year == 2013)]
    sales_2013 =s['sales_amount'].sum()
    s = info[(info['transaction_date'].dt.year == 2014)]
    sales_2014 =s['sales_amount'].sum()
    s = info[(info['transaction_date'].dt.year == 2015)]
    sales_2015 =s['sales_amount'].sum()    
    
    growth_per_region[region] = [sales_2014/sales_2013, sales_2015/sales_2014]
    avg_growth_per_region[region] = (sales_2015/sales_2013 - 1) * 100


expected_per_region = {}
for k, v in sales_per_region.items():
    # the expected sales for the next five years is calculated by taking the average yearly sales
    # since sales_per_region is over 3.33 years and then factoring in the growth for each year
    avg_growth = (avg_growth_per_region[k] / 100) + 1
    expected_per_region[k] = (sales_per_region[k]/(3+1/3)) *(avg_growth + avg_growth**2 + avg_growth**3 + avg_growth**4 + avg_growth**5)

    

    

#group by costomers
# get the amount of new customers who have joined every month
new_customers = {}
for year in range(2013,2017):
    for month in range(1,13):
        customers = df[(df['join_date'].dt.year == year) & (df['join_date'].dt.month == month)]
        period = str(month) + "/" + str(year)       
        new_customers[period] = customers['user'].nunique()
new_customers = {k:v for (k,v) in new_customers.items() if v > 0}

# get the average length of time a customer is a customer 
retention = []
for i in range(10001):
    user = df[df['user'] == i]
    
    # we assume that if the last purchase was made over a year before the current date the customer has dropped
    if len(user) > 0 and int((current_day - max(user['transaction_date']).date()).days) > 365:
        x= int((max(user['transaction_date']) -max(user['join_date'])).days)
        retention.append(x)
avg_retention = sum(retention)/len(retention)


#get the average sales of a customer who joined in a particular month
customer_quality = {}
for year in range(2013,2017):
    for month in range(1,13):

        sales = df[(df['join_date'].dt.year == year) & (df['join_date'].dt.month == month)]  

        sales_by_user = sales.groupby('user').sum()

        
        period = str(month) + "/" + str(year)       
        customer_quality[period] = sales_by_user['sales_amount'].mean()
        # divide the average sales by the number of days for which the customer has joined
        if int(((current_day) - datetime.date(year, month, 1)).days) > 0:
            customer_quality[period] /= int(((current_day) - datetime.date(year, month, 1)).days) *30
# remove months wehere sales is 0 
customer_quality = {k:v for (k,v) in customer_quality.items() if (v > 0 and '2016' not in k)}



# get the average first sale amount for each costomer 
first_sale = {}
for year in range(2013,2017):
    for month in range(1,13):
        sales = df[(df['join_date'].dt.year == year) & (df['join_date'].dt.month == month)]  
        sales = sales[sales['join_date'] == sales['transaction_date']]
        period = str(month) + "/" + str(year)       
        first_sale[period] = sales['sales_amount'].mean()
# remove months wehere sales is 0 
first_sale = {k:v for (k,v) in first_sale.items() if v > 0}


# compare the average sales of each month to the overall average
seasonality = {}
number = {}
avg_sales = sum(monthly_sales.values())/(len(monthly_sales))
for k,v, in monthly_sales.items():
    for i in range(1,13):
        if  str(i) + '/' == k[0:len(str(i)+'/')]:
            seasonality[i] = seasonality.get(i, 0)
            seasonality[i] += v
            number[i] = number.get(i,0)
            number[i] += 1
for k,v in seasonality.items():
    seasonality[k] = seasonality[k] / (number[k] * sum(monthly_sales.values())/(len(monthly_sales)))
months = []
for i in range(1,13):
    months.append( calendar.month_abbr[i])
    


def plot_region_projection():
    X = np.arange(len(expected_per_region))
    pl.bar(X, list(expected_per_region.values()), align='center', width=0.5, color = 'g', bottom = 0.0)
    pl.xticks(X, expected_per_region.keys(), rotation = 90)
    pl.title('Projected Five Year Total Sales ($)')
    pl.savefig('region_projection.png', dpi = 600)
    pl.tight_layout()
    pl.show()
    
def plot_seasonality():
    X = np.arange(len(seasonality))
    pl.bar(X, list(seasonality.values()), align='center', width=0.5, color = 'b', bottom = 0.0)
    pl.xticks(X, months, rotation = 90)
    pl.title('Monthly Sales Compared to Average (ratio)')
    pl.savefig('seasonality.png', dpi = 600)
    pl.tight_layout()
    pl.show()
    
    
def plot_customer_growth():
    X = np.arange(len(new_customers))
    pl.bar(X, list(new_customers.values()), align='center', width=0.5, color = 'r', bottom = 0.0)
    pl.xticks(X, new_customers.keys(), rotation = 90)
    pl.title('New Customers (#)')
    pl.tight_layout()
    pl.savefig('customer_growth.png', dpi = 600)
    pl.show()
        
def plot_customer_quality():  
    X = np.arange(len(customer_quality))
    pl.bar(X, list(customer_quality.values()), align='center', width=0.5, color = 'b', bottom = 0.0)
    pl.xticks(X, monthly_sales.keys(), rotation = 90)
    pl.title('Customer Quality')
    pl.savefig('customer_quality.png', dpi = 600)
    pl.tight_layout()
    pl.show()
    
def plot_first_sale():  
    X = np.arange(len(first_sale))
    pl.bar(X, list(first_sale.values()), align='center', width=0.5, color = 'b', bottom = 0.0)
    pl.xticks(X, monthly_sales.keys(), rotation = 90)
    pl.title('Average First Sale ($)')
    pl.savefig('first_sale.png', dpi = 600)
    pl.tight_layout()
    pl.show()


def plot_sales_months():  
    X = np.arange(len(monthly_sales))
    pl.bar(X, list(monthly_sales.values()), align='center', width=0.5, color = 'r', bottom = 0.0)
    pl.xticks(X, monthly_sales.keys(), rotation = 90)
    pl.title('Total Sales by Month ($)')
    pl.tight_layout()
    pl.savefig('month.png', dpi = 600)
    pl.show()

def plot_sales_years():
    X = np.arange(len(yearly_sales))
    pl.bar(X, list(yearly_sales.values()), align='center', width=0.5, color = 'r', bottom = 0.0)
    pl.xticks(X, yearly_sales.keys(), rotation = 90)
    pl.title('Total Sales by Year')
    pl.tight_layout()
    pl.savefig('year.png', dpi = 600)
    pl.show()
    
def plot_region_growth():
    X = np.arange(len(avg_growth_per_region))
    pl.bar(X, list(avg_growth_per_region.values()), align='center', width=0.5, color = 'g', bottom = 0.0)
    pl.xticks(X, avg_growth_per_region.keys(), rotation = 90)
    pl.title('Avg Growth by Region (2013-2015)')
    pl.savefig('region_growth.png', dpi = 600)
    pl.tight_layout()
    pl.show()

def plot_region_sales():
    X = np.arange(len(sales_per_region))
    pl.bar(X, list(sales_per_region.values()), align='center', width=0.5, color = 'g', bottom = 0.0)
    pl.xticks(X, sales_per_region.keys(), rotation = 90)
    pl.title('Sales by Region ($)')
    pl.savefig('region_sales.png', dpi = 600)
    pl.tight_layout()
    pl.show()
        
    
def regress_2016():
    

    sixteen_total = 0
    sixteen_counter = 0
    
    for k,v in monthly_sales.items():
        if ("2016" in k):
            sixteen_counter += 1
            sixteen_total += v
            
    # we expect sales in 2016 to be the avg of the first 11 months sales + the last month's adjusted
    expected = (sixteen_total/sixteen_counter) * (11 + seasonality[12])
    
    print("2016 expected sales: "  + str(expected))
    print("2016/2015 growth: " + str(expected/ yearly_sales[2015]))
    
    
def regress(my_dict):
    count = 0
    x = []
    y = []
    for k,v, in my_dict.items() :
        x.append(count)
        count += 1
        y.append(v)
    m, b, r, p, std_err = linregress(x,y)
    print("b = " + str(b) + ", m = " +  str(m) + ", r^2 = " + str(r*r))
    
    
def plot():
    plot_sales_months()
    plot_sales_years()
    plot_customer_quality()
    plot_first_sale()
    plot_region_growth()
    plot_region_sales()
    plot_customer_growth()
    plot_seasonality()
    plot_region_projection()
    regress_2016()
    
    print("avg first sale regression")
    regress(first_sale)
    print("customer quality regression")
    regress(customer_quality)
    print("monthly_sales regression")
    regress(monthly_sales)
    print("new customers regression")
    regress(new_customers)
    
    
 
plot()                          

