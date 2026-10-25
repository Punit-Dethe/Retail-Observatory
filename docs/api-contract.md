# Local API contract

Python API on 127.0.0.1:8000. Vite proxies /api. JSON floats finite; unknown values null. All amounts GBP.

GET /api/meta
`{name:"Online Retail II",sourceUrl,license,rawRows,start:"2009-12-01",end:"2011-12-09",countries:string[],quality:{rawRows,duplicates,missingCustomer,missingDescription,nonPositivePrice,cancellationRows,negativeQuantity,cleanRows},generatedAt}`

GET /api/analytics?start=2010-12-01&end=2011-12-09&country=all
Defaults full range. start/end inclusive. All following analyses respect selected dates/country, except quality (dataset-wide). Historical extract, no live status.

Response:
- `filters:{start,end,country}`
- `summary:{revenue,grossRevenue,returns,orders,customers,units,aov,returnRate,repeatRate,products,countries,rows,identifiedRevenueShare}` revenue = gross minus absolute negative-quantity value; orders = distinct positive sale invoices; repeatRate = customers with >=2 positive invoices / identified customers; returnRate = return value/gross*100.
- `previous`: same summary for preceding equal-length period, with `available:boolean`. Do not show change when unavailable.
- `trend:[{date:"2010-01",revenue,grossRevenue,returns,orders,customers,units}]` monthly; partialMonths strings in `partialMonths`.
- `daily:[{date:"2011-01-01",revenue,orders}]` includes zero-activity days within selected/source coverage when scope has records.
- `countries:[{country,revenue,grossRevenue,returns,orders,customers,share}]` sorted revenue desc
- `products:[{code,name,revenue,units,orders,returns,returnRate,price}]` sorted revenue desc; up to 100. revenue and units positive sales for product ranking, returns separately.
- `customers:[{id,country,recency,frequency,monetary,segment,cluster,r,f,m}]` up to 6000, sorted monetary desc; all identified sale customers. segment labels Champions, Loyal customers, Potential loyalists, New customers, At risk, Hibernating. recency measured from day after selection end. monetary positive spend. cluster numeric 0..3.
- `segments:[{name,customers,revenue,share,avgRecency,avgFrequency,avgMonetary}]`
- `clusters:[{name,customers,avgRecency,avgFrequency,avgMonetary}]` K-means on standardized log1p R/F/M, seeded, 4 clusters, explanatory.
- `clusterQuality:{silhouette:number|null,k:number,sampleSize:number}` silhouette evaluated on at most 1500 seeded sampled customers.
- `cohorts:[{month,size,retention:(number|null)[]}]` first observed selected-period purchase, index0=100; future unobserved null, latest12 cohorts and first12 ages.
- `heatmap:[{day:number,hour:number,orders:number,revenue:number}]` day0 Monday to6 Sunday; distinct invoices per cell, 24 hours.
- `basket:{transactions,eligibleProducts,minSupport,rules:[{antecedent,consequent,support,confidence,lift,count}]}` exact pair co-occurrence, positive merchandise baskets, top80 by invoice frequency, min count >=20, directional confidence, maximum20 rules sorted lift. Percent values 0..100.
- `orderDistribution:[{range,count}]` positive invoice totals bins £0–50,50–100,100–250,250–500,500–1000,1000+.
- `pareto:[{percentProducts,percentRevenue}]` cumulative all merchandise products sales, percent0..100.
- `quality`: dataset-wide from meta.
- `insights:[{title,body,tone:"blue"|"green"|"amber"}]` calculated observations.
- `methods:{clustering:string,basket:string,cohort:string,scope:string}`

Zero-row selection returns empty arrays and zero summary, never fake data. App handles loading/error/empty states.

GET /api/export?start=...&end=...&country=...&kind=products|customers|countries|trend|transactions
CSV download. Transactions exports cleaned selected rows. Other kinds use corresponding analytics arrays. Product table local search/sort client-side, customer table search/segment client-side. Include filtered scope in export.
