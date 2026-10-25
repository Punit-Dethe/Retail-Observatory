import { getPreset, retailMeta, retailSourceSha256 } from '../presets'
import type { AnalysisNode, Block, Board, BoardState, Evidence } from './types'
import { uid } from './types'

export const STORAGE_KEY='retail-investigation-canvas.v1'
export function starterBoard(name='The retail picture'):Board {
 const scope={start:retailMeta.start,end:retailMeta.end,country:'all'}
 const data=getPreset(scope)!
 const groupId=uid()
 const evidence=(query:string):Evidence=>({tool:'starter',source:'UCI Online Retail II',sourceUrl:retailMeta.sourceUrl,sourceSha256:retailSourceSha256,scope,rowCount:data.summary.rows,definitions:['All amounts are GBP. Cleaned merchandise lines only.','Net revenue equals positive sales less observed credits. December 2011 is incomplete.'],query,generatedAt:new Date().toISOString()})
 const blocks:Block[]=[
 {id:uid(),kind:'chart',title:'The sales story',subtitle:'Net merchandise revenue · monthly',chartType:'line',rows:data.trend.map(r=>({month:r.date,revenue:r.revenue})),xKey:'month',series:[{key:'revenue',label:'Net revenue'}],format:'currency',evidence:evidence('Group eligible line amounts by invoice month and sum signed values.')},
 {id:uid(),kind:'chart',title:'Where customers buy',subtitle:'Top six markets · net revenue',chartType:'bar',rows:data.countries.slice(0,6).map(r=>({country:r.country,revenue:r.revenue})),xKey:'country',series:[{key:'revenue',label:'Net revenue'}],format:'currency',evidence:evidence('Group eligible signed line amounts by country; order by net revenue, descending; take six.')},
 {id:uid(),kind:'chart',title:'Products with an impact',subtitle:'Top five products · positive sales',chartType:'bar',rows:data.products.slice(0,5).map(r=>({product:r.name.trim().toLowerCase(),revenue:r.revenue})),xKey:'product',series:[{key:'revenue',label:'Positive sales'}],format:'currency',evidence:evidence('Positive-quantity merchandise sales grouped by product. Rank positive sales and take five.')},
 {id:uid(),kind:'note',title:'Start with a question.',body:`These are real transactions, ready to explore. Across this cleaned extract, ${data.summary.orders.toLocaleString('en-GB')} sale invoices connect ${data.summary.customers.toLocaleString('en-GB')} identified customers across ${data.summary.countries} markets.\n\nSelect a chart to continue from its evidence, or ask a new question on the right. Credits and anonymous shoppers remain visible in the definitions.`,tone:'blue',evidence:evidence('Overview summary from the fixed All markets / All data analysis values.')},
 ]
 const nodes:Board['nodes']=[{id:uid(),type:'heading',position:{x:70,y:65},data:{title:'Retail at a glance',subtitle:'One starting point. Many directions to explore.',groupId},draggable:true,selectable:false}]
 const positions=[{x:70,y:133},{x:650,y:133},{x:70,y:550},{x:650,y:550}]
 blocks.forEach((block,i)=>nodes.push({id:block.id,type:'analysis',position:positions[i],data:{block,groupId,originQuestion:'Retail at a glance'},style:{width:i%2?350:550},width:i%2?350:550} as AnalysisNode))
 const viewportWidth=typeof window==='undefined'?1366:window.innerWidth
 const dockWidth=viewportWidth>1024?438:0
 const zoom=Math.max(.25,Math.min(.92,(viewportWidth-112-dockWidth)/930))
 return {id:uid(),name,nodes,edges:[],scope,viewport:{x:88-70*zoom,y:32-65*zoom,zoom},messages:[{id:uid(),role:'assistant',content:'Your retail data is already on the canvas. Ask a question, follow a pattern, or select a chart to take the next step.',mode:'guided'}],updatedAt:new Date().toISOString()}
}
export function readBoards():BoardState {
 try {const raw=localStorage.getItem(STORAGE_KEY);if(raw){const parsed=JSON.parse(raw);if(validateState(parsed)){
  return parsed
 }}}catch{}
 const board=starterBoard();return {version:1,activeId:board.id,boards:[board]}
}
export function saveBoards(state:BoardState):boolean{try{localStorage.setItem(STORAGE_KEY,JSON.stringify(state));return true}catch{return false}}
export function validateState(value:unknown):value is BoardState {
 const object=(x:unknown):x is Record<string,any>=>Boolean(x)&&typeof x==='object'&&!Array.isArray(x)
 const strings=(x:unknown,max=1000):x is string[]=>Array.isArray(x)&&x.length<=max&&x.every(v=>typeof v==='string')
 const finite=(x:unknown):x is number=>typeof x==='number'&&Number.isFinite(x)
 const scope=(x:unknown)=>object(x)&&typeof x.start==='string'&&typeof x.end==='string'&&typeof x.country==='string'&&(x.productCode===undefined||typeof x.productCode==='string')&&(x.countries===undefined||strings(x.countries,100))
 const evidence=(x:unknown)=>object(x)&&['tool','source','sourceUrl','sourceSha256','query','generatedAt'].every(k=>typeof x[k]==='string')&&scope(x.scope)&&finite(x.rowCount)&&x.rowCount>=0&&strings(x.definitions,100)
 const followUps=(x:unknown)=>Array.isArray(x)&&x.length<=30&&x.every(v=>object(v)&&typeof v.label==='string'&&typeof v.prompt==='string'&&['sales','markets','product','customers','baskets'].includes(v.tool)&&(v.productCode===undefined||typeof v.productCode==='string'))
 const block=(x:unknown)=>object(x)&&typeof x.id==='string'&&typeof x.title==='string'&&['chart','note'].includes(x.kind)&&evidence(x.evidence)&&['subtitle','body','xKey'].every(k=>x[k]===undefined||typeof x[k]==='string')&&(x.tone===undefined||['neutral','blue','amber'].includes(x.tone))&&(x.format===undefined||['currency','percent','number'].includes(x.format))&&(x.kind!=='chart'||['line','bar','donut','scatter','table'].includes(x.chartType))&&(x.rows===undefined||(Array.isArray(x.rows)&&x.rows.length<=20000&&x.rows.every((r:unknown)=>object(r)&&Object.values(r).every(v=>v===null||typeof v==='string'||finite(v)))))&&(x.series===undefined||(Array.isArray(x.series)&&x.series.length<=30&&x.series.every((s:unknown)=>object(s)&&typeof s.key==='string'&&typeof s.label==='string')))
 if(!object(value)||value.version!==1||typeof value.activeId!=='string'||!Array.isArray(value.boards)||value.boards.length<1||value.boards.length>20)return false
 const ids=new Set<string>()
 return value.boards.every((b:unknown)=>{
  if(!object(b)||typeof b.id!=='string'||ids.has(b.id)||typeof b.name!=='string'||typeof b.updatedAt!=='string'||!scope(b.scope)||!object(b.viewport)||!finite(b.viewport.x)||!finite(b.viewport.y)||!finite(b.viewport.zoom)||b.viewport.zoom<.1||b.viewport.zoom>3||!Array.isArray(b.nodes)||b.nodes.length>300||!Array.isArray(b.edges)||b.edges.length>600||!Array.isArray(b.messages)||b.messages.length>500)return false
  ids.add(b.id);const nodeIds=new Set<string>()
  return b.nodes.every((n:unknown)=>{
   if(!object(n)||typeof n.id!=='string'||nodeIds.has(n.id)||!object(n.position)||!finite(n.position.x)||!finite(n.position.y)||!object(n.data)||typeof n.data.groupId!=='string')return false
   nodeIds.add(n.id)
   if(n.style!==undefined&&(!object(n.style)||Object.keys(n.style).some(k=>!['width','height'].includes(k))||Object.values(n.style).some(v=>!finite(v)||v<100||v>3000)))return false
   return n.type==='heading'?typeof n.data.title==='string'&&typeof n.data.subtitle==='string':n.type==='analysis'&&typeof n.data.originQuestion==='string'&&block(n.data.block)
  })&&b.edges.every((e:unknown)=>object(e)&&typeof e.id==='string'&&typeof e.source==='string'&&typeof e.target==='string'&&nodeIds.has(e.source)&&nodeIds.has(e.target)&&(e.label===undefined||typeof e.label==='string')&&(e.type===undefined||['smoothstep','default','straight','step'].includes(e.type)))&&b.messages.every((m:unknown)=>object(m)&&typeof m.id==='string'&&['user','assistant'].includes(m.role)&&typeof m.content==='string'&&(m.blockIds===undefined||strings(m.blockIds,300))&&(m.warnings===undefined||strings(m.warnings,100))&&(m.followUps===undefined||followUps(m.followUps)))
 })&&value.boards.some(b=>b.id===value.activeId)
}
