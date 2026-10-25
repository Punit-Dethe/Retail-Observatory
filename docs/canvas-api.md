# Canvas API contract

All endpoints relative to existing Python server, same origin `/api`. Amounts GBP; dates inclusive. No synthetic results.

GET `/api/canvas/capabilities`
`{mode:"guided"|"llm",llmConfigured:boolean,model:string|null,source:"Online Retail II",start,end,countries:string[],suggestions:[{label,prompt,tool}]}`. Tool enum `sales|markets|product|customers|baskets`. Model configuration absent => guided explicitly. Error from configured model must be surfaced, not silently masquerade as LLM success.

GET `/api/canvas/catalog?q=<search>`
`{products:[{code,name}],countries:string[]}` product search across full cleaned catalog, up to30, initial top30sold. Search input debounced optional.

POST `/api/canvas/investigate`
JSON `{message:string,scope:{start:string,end:string,country:string},tool?:"sales"|"markets"|"product"|"customers"|"baskets",productCode?:string,countries?:string[],selected?:[{id:string,title:string,evidence?:Evidence}],history?:[{role:"user"|"assistant",content:string}]}`.
Defaults source full coverage, all markets. Guided mode inherits a product code from selected evidence when no product is explicitly supplied; dates and markets use the current scope or a recognized explicit question. The model also receives selected scope/definitions as context. Request `tool` deterministic button executes directly (guided even with model config); open message uses model if configured otherwise conservative supported-intent router.

Response `{id,title,mode:"guided"|"llm",message,blocks:Block[],connections:[{source:string,target:string,label:string}],followUps:[{label,prompt,tool,productCode?:string}],warnings:string[]}`.

Block fields:
`{id,kind:"chart"|"note",title,subtitle?:string,body?:string,tone?:"neutral"|"blue"|"amber",chartType?:"line"|"bar"|"donut"|"scatter"|"table",rows?:Record<string,string|number|null>[],xKey?:string,series?:[{key:string,label:string}],format?:"currency"|"percent"|"number",evidence:Evidence}`.

Evidence: `{tool:string,source:"UCI Online Retail II",sourceUrl:string,sourceSha256:string,scope:{start,end,country,productCode?:string,countries?:string[]},rowCount:number,definitions:string[],query:string,generatedAt:string}`. `rowCount` counts eligible cleaned transaction rows for the analysis, not aggregated displayed rows. Query is human-readable reproducible definition, not an executable arbitrary query endpoint.

Each response block ID unique across requests; use responseconnections for derived links. Frontend owns spatial layout and connecting new neighborhood to selected prior node (label"Follow-up"). No servercoordinates; place new nodes beside selected/belowexisting, never rerender entireboard or auto-rearrange priornodes. Blocks usually3–6, never padded toquota. Notes draw calculated facts and explicit limitations. No-data scopes return note and explanatory response; unsupported guided request returns no blocks with supportedexamples; malformedargs400, providerfailure502.

Initial frontend board can use bundled existing presets (getPreset/retailMeta) without API waiting: salesmonthlychart, topmarketbar, productbar and note. Label real source and scope; evidence on initialcharts follows same shape. No startupLLMcall. Frontend API response always checked and user can retry/cancel. Localstorage persists boards/data/chat/viewport, no serveraccounts. Export JSON includes source/version and all result data; import validates envelope/arrays and limits reasonablefile size.
