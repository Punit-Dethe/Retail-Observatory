export type Page = 'Overview'|'Sales'|'Customers'|'Products'|'Markets'|'Data lab'
export interface Quality {rawRows:number;duplicates:number;missingCustomer:number;missingDescription:number;nonPositivePrice:number;cancellationRows:number;negativeQuantity:number;cleanRows:number;excludedRows?:number;retainedMissingCustomer?:number;exclusions?:{name:string;rows:number}[]}
export interface Meta {name:string;sourceUrl:string;license:string;rawRows:number;start:string;end:string;countries:string[];quality:Quality;generatedAt:string}
export interface Filters {start:string;end:string;country:string}
export interface Summary {revenue:number;grossRevenue:number;returns:number;orders:number;customers:number;units:number;aov:number;returnRate:number;repeatRate:number;products:number;countries:number;rows:number;identifiedRevenueShare:number}
export interface Trend {date:string;revenue:number;grossRevenue:number;returns:number;orders:number;customers:number;units:number}
export interface Country {country:string;revenue:number;grossRevenue:number;returns:number;orders:number;customers:number;share:number}
export interface Product {code:string;name:string;revenue:number;units:number;orders:number;returns:number;returnRate:number;price:number}
export interface Customer {id:string;country:string;recency:number;frequency:number;monetary:number;segment:string;cluster:number;r:number;f:number;m:number}
export interface Segment {name:string;customers:number;revenue:number;share:number;avgRecency:number;avgFrequency:number;avgMonetary:number}
export interface Cluster {name:string;customers:number;avgRecency:number;avgFrequency:number;avgMonetary:number}
export interface Cohort {month:string;size:number;retention:(number|null)[]}
export interface HeatCell {day:number;hour:number;orders:number;revenue:number}
export interface Rule {antecedent:string;consequent:string;support:number;confidence:number;lift:number;count:number}
export interface Analytics {filters:Filters;summary:Summary;previous:Summary & {available:boolean};trend:Trend[];daily:{date:string;revenue:number;orders:number}[];partialMonths:string[];countries:Country[];products:Product[];customers:Customer[];segments:Segment[];clusters:Cluster[];cohorts:Cohort[];heatmap:HeatCell[];basket:{transactions:number;eligibleProducts:number;minSupport:number;rules:Rule[]};orderDistribution:{range:string;count:number}[];pareto:{percentProducts:number;percentRevenue:number}[];quality:Quality;insights:{title:string;body:string;tone:'blue'|'green'|'amber'}[];methods:{clustering:string;basket:string;cohort:string;scope:string};clusterQuality?:{silhouette:number|null;k:number;sampleSize:number}}
