import pandas as pd

df=pd.read_csv("D:/DATA ANALYST/New folder/IKEA Gifting Dataset/IKEA Gifting Dataset/RetailCleaned.csv", header=None)
df.columns = ['Invoice', 'StockCode','Description', 'Quantity', 'InvoiceDate', 'Price', 'Customer ID', 'Country', 'Sourcesheet']
df ['InvoiceDate']= pd.to_datetime(df ['InvoiceDate'])
print(df.shape)
df.info()

print(df.columns.tolist())
#FILTER AND CALCULATE RECENCY, FREQUENCY, MONETARY

rfm_data = df[(df['Customer ID'].notna()) & (df['Quantity'] > 0)].copy()
snapshot_date = pd.to_datetime('2011-12-10')

rfm=rfm_data.groupby('Customer ID').agg(
    Recency=('InvoiceDate', lambda x:(snapshot_date - x.max()).days),
    Frequency=('Invoice', 'nunique'), 
    Monetary=('Quantity', lambda x: (x*rfm_data.loc[x.index, 'Price']).sum())
).reset_index()

# SCORE CUSTOMERS AND ASSIGN BUSINESS SEGMENTS

rfm['R_Score'] = pd.qcut(rfm['Recency'],5, labels= [5, 4, 3, 2, 1]).astype(int)
rfm['F_Score'] = pd.qcut(rfm ['Frequency'].rank(method='first'), 5, labels=[1, 2, 3, 4, 5]).astype(int)
rfm['M_Score'] = pd.qcut(rfm['Monetary'],5, labels= [1, 2, 3, 4, 5]).astype(int)


def segment_customer(row):
    if row['R_Score']>=4 and row['F_Score'] >= 4 and row['M_Score'] >=4:
        return 'Champions'
    elif row['R_Score'] >=3 and row['F_Score'] >=3:
        return 'Loyal'
    elif row['R_Score'] <=2 and row['F_Score'] >=3:
        return 'At Risk'
    elif row['R_Score'] >=4 and row['F_Score'] <=2:
        return 'New'
    elif row['R_Score'] == 3 and row['F_Score'] <=2:
        return 'Needs Attention'
    else:
        return 'Lost'

rfm['Segment'] = rfm.apply(segment_customer, axis=1)
rfm['IsChurned'] = rfm['Recency']> 90



# MERGE RFM RESULTS BACK ONTO TRANSACTIONS AND EXPORT

df = df[(df['Customer ID'].notna()) & (df[ 'Quantity'] > 0)].copy()
df['InvoiceMonth'] = df['InvoiceDate'].dt.to_period('M').dt.to_timestamp()
df['Revenue'] = df['Quantity']* df['Price']
df_final=df.merge(
    rfm[['Customer ID', 'Recency', 'Frequency', 'Monetary', 'R_Score', 'F_Score', 'M_Score', 'Segment', 'IsChurned']],
    on= 'Customer ID', how='left'
)

df_final.to_excel('EcommerceDashboardData.xlsx', index=False)