import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Background, BackgroundVariant, Controls, MiniMap, ReactFlow, ReactFlowProvider, applyEdgeChanges, applyNodeChanges, getNodesBounds, useReactFlow } from '@xyflow/react'
import type { Connection, Edge, EdgeChange, NodeChange } from '@xyflow/react'
import { ArrowDownToLine, ArrowLeft, ArrowUpRight, BarChart3, CalendarDays, Check, Focus, Hand, HelpCircle, Import, Link2, Menu, MessageSquare, MousePointer2, PencilLine, Plus, Redo2, Undo2, X } from 'lucide-react'
import { retailMeta } from '../presets'
import { CanvasActions, nodeTypes } from './CanvasNodes'
import { CanvasChat } from './CanvasChat'
import { EvidencePanel } from './EvidencePanel'
import { readBoards, saveBoards, starterBoard, validateState } from './storage'
import { uid } from './types'
import type { AnalysisNode, AnalysisResponse, Board, BoardNode, Capabilities, InvestigateRequest, Tool } from './types'
import '@xyflow/react/dist/style.css'
import './canvas.css'

const clone=(board:Board):Board=>structuredClone(board)
function Workspace(){
 const [state,setState]=useState(readBoards),current=useRef(state)
 const board=state.boards.find(b=>b.id===state.activeId)!
 const history=useRef<{past:Board[];future:Board[]}>({past:[],future:[]})
 const [historyVersion,setHistoryVersion]=useState(0)
 const [saved,setSaved]=useState<boolean|null>(true),[feedback,setFeedback]=useState(''),[capabilities,setCapabilities]=useState<Capabilities|null>(null)
 const [chatOpen,setChatOpen]=useState(()=>window.innerWidth>1024),[evidenceId,setEvidenceId]=useState<string|null>(null),[showEdges,setShowEdges]=useState(false),[panMode,setPanMode]=useState(false),[showMap,setShowMap]=useState(false),[help,setHelp]=useState(false)
 const [pending,setPending]=useState(false),[slow,setSlow]=useState(false),[error,setError]=useState('')
 const [notice,setNotice]=useState(''),[rename,setRename]=useState(false)
 const [popover,setPopover]=useState<'menu'|'scope'|null>(null),[scopeDraft,setScopeDraft]=useState(board.scope),[scopeError,setScopeError]=useState('')
 const menuButton=useRef<HTMLButtonElement>(null),scopeButton=useRef<HTMLButtonElement>(null),popoverPanel=useRef<HTMLDivElement>(null)
 const controller=useRef<AbortController|null>(null),requestId=useRef(0),lastRequest=useRef<Parameters<typeof send>|null>(null)
 const file=useRef<HTMLInputElement>(null),resizeRecording=useRef(false)
 const flow=useReactFlow<BoardNode,Edge>()
 const selected=board.nodes.filter((n):n is AnalysisNode=>n.type==='analysis'&&Boolean(n.selected))
 const evidenceNode=board.nodes.find((n):n is AnalysisNode=>n.id===evidenceId&&n.type==='analysis')
 const record=useCallback((old:Board)=>{history.current.past.push(clone(old));if(history.current.past.length>35)history.current.past.shift();history.current.future=[];setHistoryVersion(v=>v+1)},[])
 const update=useCallback((fn:(old:Board)=>Board,remember=true)=>{const before=current.current;const old=before.boards.find(b=>b.id===before.activeId)!;if(remember)record(old);const changed={...fn(old),updatedAt:new Date().toISOString()};const next={...before,boards:before.boards.map(b=>b.id===old.id?changed:b)};current.current=next;setState(next);setSaved(null)},[record])
 useEffect(()=>{const timer=setTimeout(()=>setSaved(saveBoards(state)),450);return()=>clearTimeout(timer)},[state])
 useEffect(()=>{const flush=()=>saveBoards(current.current);window.addEventListener('pagehide',flush);return()=>{window.removeEventListener('pagehide',flush);flush()}},[])
 useEffect(()=>{const c=new AbortController();fetch('/api/canvas/capabilities',{signal:c.signal}).then(async r=>{if(!r.ok)throw new Error('Analyst service is unavailable.');return r.json()}).then(setCapabilities).catch(e=>{if(e.name!=='AbortError')setNotice('Canvas ready. Start the local server to run new investigations.')});return()=>c.abort()},[])
 useEffect(()=>{if(!pending){setSlow(false);return}const timer=setTimeout(()=>setSlow(true),5000);return()=>clearTimeout(timer)},[pending])
 useEffect(()=>()=>controller.current?.abort(),[])
 useEffect(()=>{if(!feedback)return;const timer=setTimeout(()=>setFeedback(''),3200);return()=>clearTimeout(timer)},[feedback])
 useEffect(()=>{
   if(!popover)return
   popoverPanel.current?.querySelector<HTMLElement>('button, input, select')?.focus()
   const dismiss=(event:PointerEvent)=>{if(!popoverPanel.current?.contains(event.target as Node)&&!menuButton.current?.contains(event.target as Node)&&!scopeButton.current?.contains(event.target as Node))setPopover(null)}
   const escape=(event:KeyboardEvent)=>{if(event.key==='Escape'){event.preventDefault();setPopover(null);(popover==='menu'?menuButton:scopeButton).current?.focus()}}
   document.addEventListener('pointerdown',dismiss);document.addEventListener('keydown',escape)
   return()=>{document.removeEventListener('pointerdown',dismiss);document.removeEventListener('keydown',escape)}
 },[popover])

 const cancel=useCallback(()=>{controller.current?.abort();requestId.current++;setPending(false);setError('')},[])
 const focus=useCallback((ids:string[])=>{const targets=flow.getNodes().filter(n=>ids.includes(n.id));if(!targets.length)return;const bounds=getNodesBounds(targets);const mobile=window.innerWidth<=1024;if(mobile){setChatOpen(false);setEvidenceId(null)}const left=mobile?72:88,right=(chatOpen||evidenceId)&&!mobile?462:24,top=32,bottom=90;const usableWidth=Math.max(120,window.innerWidth-left-right),usableHeight=Math.max(120,window.innerHeight-top-bottom);const zoom=Math.min(.96,Math.max(.22,Math.min(usableWidth/Math.max(bounds.width,1),usableHeight/Math.max(bounds.height,1))));flow.setViewport({zoom,x:left+(usableWidth-bounds.width*zoom)/2-bounds.x*zoom,y:top+(usableHeight-bounds.height*zoom)/2-bounds.y*zoom},{duration:window.matchMedia('(prefers-reduced-motion: reduce)').matches?0:300})},[flow,chatOpen,evidenceId])
 const fit=useCallback(()=>focus(flow.getNodes().map(n=>n.id)),[focus,flow])
 const undo=useCallback(()=>{const before=current.current.boards.find(b=>b.id===current.current.activeId)!;const old=history.current.past.pop();if(!old)return;history.current.future.push(clone(before));update(()=>old,false);setHistoryVersion(v=>v+1)},[update])
 const redo=useCallback(()=>{const before=current.current.boards.find(b=>b.id===current.current.activeId)!;const next=history.current.future.pop();if(!next)return;history.current.past.push(clone(before));update(()=>next,false);setHistoryVersion(v=>v+1)},[update])
 const remove=useCallback((id:string)=>{update(b=>({...b,nodes:b.nodes.filter(n=>n.id!==id),edges:b.edges.filter(e=>e.source!==id&&e.target!==id)}));setEvidenceId(null)},[update])
 const duplicate=useCallback((id:string)=>{update(b=>{const node=b.nodes.find(n=>n.id===id);if(!node||node.type!=='analysis')return b;const copied=structuredClone(node);copied.id=uid();copied.data.block.id=copied.id;copied.position={x:node.position.x+45,y:node.position.y+45};copied.selected=false;return {...b,nodes:[...b.nodes,copied]}})},[update])
 const editNote=useCallback((id:string,title:string,body:string)=>update(b=>({...b,nodes:b.nodes.map(n=>n.id===id&&n.type==='analysis'?{...n,data:{...n.data,block:{...n.data.block,title,body}}}:n)})),[update])
 const actions=useMemo(()=>({inspect:(id:string)=>{setEvidenceId(id);setChatOpen(true)},duplicate,remove}),[duplicate,remove])
 const clearSelection=useCallback(()=>update(b=>({...b,nodes:b.nodes.map(n=>({...n,selected:false}))}),false),[update])
 const nodesChange=useCallback((changes:NodeChange<BoardNode>[])=>{
   if(changes.some(c=>c.type==='dimensions'&&c.resizing)&&!resizeRecording.current){record(current.current.boards.find(b=>b.id===current.current.activeId)!);resizeRecording.current=true}
   if(changes.some(c=>c.type==='dimensions'&&c.resizing===false))resizeRecording.current=false
   const removed=new Set(changes.filter(c=>c.type==='remove').map(c=>c.id));update(b=>({...b,nodes:applyNodeChanges(changes,b.nodes),edges:b.edges.filter(e=>!removed.has(e.source)&&!removed.has(e.target))}),removed.size>0)
 },[update,record])
 const edgesChange=useCallback((changes:EdgeChange[])=>update(b=>({...b,edges:applyEdgeChanges(changes,b.edges)}),changes.some(c=>c.type==='remove')),[update])
 const connect=useCallback((connection:Connection)=>{if(connection.source===connection.target)return;update(b=>b.edges.some(e=>e.source===connection.source&&e.target===connection.target)?b:{...b,edges:[...b.edges,{id:uid(),source:connection.source,target:connection.target,label:'Related',type:'smoothstep',data:{relation:'related'}}]});setShowEdges(true)},[update])
 const addNote=()=>{const left=window.innerWidth<=1024?72:88;const right=window.innerWidth>1024&&(chatOpen||evidenceId)?462:24;const position=flow.screenToFlowPosition({x:left+Math.max(120,window.innerWidth-left-right)/2-100,y:160});const id=uid();const scope=board.scope;const node:AnalysisNode={id,type:'analysis',position,style:{width:330},data:{groupId:uid(),originQuestion:'Your note',block:{id,kind:'note',title:'A thought worth keeping',body:'Add your interpretation, question, or next step here.',tone:'neutral',evidence:{tool:'user-note',source:'UCI Online Retail II',sourceUrl:retailMeta.sourceUrl,sourceSha256:'User-authored note',scope,rowCount:0,definitions:['This note is a user interpretation, not a calculated finding.'],query:'User-authored note; no new calculation.',generatedAt:new Date().toISOString()}}}};update(b=>({...b,nodes:[...b.nodes,node]}));setEvidenceId(id);setChatOpen(true)}
 const newBoard=()=>{cancel();const next=starterBoard(`Investigation ${state.boards.length+1}`);next.nodes=[];next.edges=[];next.messages=[{id:uid(),role:'assistant',content:'What would you like to understand? Ask about sales, compare markets, or explore a product. Findings will arrive here as an investigation you can arrange.',mode:'guided'}];const nextState={...current.current,activeId:next.id,boards:[...current.current.boards,next]};current.current=nextState;setState(nextState);history.current={past:[],future:[]};setHistoryVersion(v=>v+1);setEvidenceId(null);flow.setViewport(next.viewport);setSaved(null)}
 const switchBoard=(id:string)=>{if(id===board.id)return;cancel();const next={...current.current,activeId:id};current.current=next;setState(next);history.current={past:[],future:[]};setHistoryVersion(v=>v+1);setEvidenceId(null);const target=next.boards.find(b=>b.id===id)!;flow.setViewport(target.viewport);setSaved(null)}
 const openScope=()=>{setHelp(false);setScopeDraft(board.scope);setScopeError('');setPopover(popover==='scope'?null:'scope')}
 const setYear=(year:string)=>{setScopeDraft(s=>({...s,start:year==='all'?retailMeta.start:`${year}-01-01`,end:year==='2010'?'2010-12-31':retailMeta.end}));setScopeError('')}
 const year=scopeDraft.start===retailMeta.start&&scopeDraft.end===retailMeta.end?'all':scopeDraft.start==='2010-01-01'&&scopeDraft.end==='2010-12-31'?'2010':scopeDraft.start==='2011-01-01'&&scopeDraft.end===retailMeta.end?'2011':'custom'
 const applyScope=()=>{if(!scopeDraft.start||!scopeDraft.end){setScopeError('Choose both a start and an end date.');return}if(scopeDraft.start<retailMeta.start||scopeDraft.end>retailMeta.end||scopeDraft.start>retailMeta.end||scopeDraft.end<retailMeta.start){setScopeError('Choose dates from 1 Dec 2009 to 9 Dec 2011.');return}if(scopeDraft.start>scopeDraft.end){setScopeError('End date must be on or after the start date.');return}update(b=>({...b,scope:{...scopeDraft}}),false);setPopover(null);scopeButton.current?.focus();setFeedback('Scope updated for new investigations.')}

 async function send(message:string,tool?:Tool,productCode?:string,countries?:string[]){
   if(pending||!message.trim())return
   lastRequest.current=[message,tool,productCode,countries]
   const id=++requestId.current,activeId=current.current.activeId,request=new AbortController();controller.current=request
   setPending(true);setError('');setEvidenceId(null);setChatOpen(true)
   const before=current.current.boards.find(b=>b.id===activeId)!
   const context=before.nodes.filter((n):n is AnalysisNode=>n.type==='analysis'&&Boolean(n.selected))
   const payload:InvestigateRequest={message,scope:before.scope,tool,productCode,countries,selected:context.map(n=>({id:n.id,title:n.data.block.title,evidence:n.data.block.evidence})),history:before.messages.slice(-10).filter(m=>!m.error).map(m=>({role:m.role,content:m.content}))}
   update(b=>({...b,messages:[...b.messages,{id:uid(),role:'user',content:message}]}),false)
   try{
     const response=await fetch('/api/canvas/investigate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload),signal:request.signal})
     const result=await response.json().catch(()=>({}));if(!response.ok)throw new Error(result.error||`This investigation could not be calculated (HTTP ${response.status}). Check that the Python server is running on port 8000 and see its terminal for details.`)
     if(request.signal.aborted||id!==requestId.current||current.current.activeId!==activeId)return
     const answer=result as AnalysisResponse;if(!Array.isArray(answer.blocks)||typeof answer.message!=='string')throw new Error('The analysis response was incomplete. Please try again.')
     const blocks=answer.blocks.slice(0,15),groupId=answer.id||uid(),width=440,gap=30
     update(b=>{
       const anchor=context[0];const maxBottom=Math.max(70,...b.nodes.map(n=>n.position.y+(n.measured?.height||n.height||(n.type==='heading'?65:360))))
       const baseX=anchor?anchor.position.x+Number(anchor.measured?.width||anchor.width||440)+110:70
       const baseY=anchor?anchor.position.y:Math.max(90,maxBottom+120)
       const nodes:BoardNode[]=blocks.length?[{id:uid(),type:'heading',position:{x:baseX,y:baseY},selectable:false,data:{title:answer.title||'A new direction',subtitle:message.length>100?message.slice(0,99)+'…':message,groupId}}]:[]
       // Leave room for wrapped headings, the partial-month caption, and longer notes.
       let rowY=baseY+70
       const theory=blocks[0]?.kind==='note'&&blocks[0].verdict?blocks[0]:null
       if(theory){const full=width*2+gap;nodes.push({id:theory.id,type:'analysis',position:{x:baseX,y:rowY},style:{width:full},data:{block:theory,groupId,originQuestion:message}});rowY+=Math.max(300,Math.ceil((theory.body||'').length/120)*23+(theory.body||'').split('\n').length*8+190)}
       const evidenceBlocks=theory?blocks.slice(1):blocks
       evidenceBlocks.forEach((block,index)=>{
         nodes.push({id:block.id,type:'analysis',position:{x:baseX+(index%2)*(width+gap),y:rowY},style:{width},data:{block,groupId,originQuestion:message}})
         if(index%2===1){const pair=evidenceBlocks.slice(index-1,index+1);rowY+=Math.max(440,...pair.map(item=>item.kind==='note'?Math.ceil((item.body||'').length/55)*23+180:440))}
       })
       const nodeIds=new Set([...b.nodes,...nodes].map(n=>n.id));const edges=(answer.connections||[]).filter(e=>nodeIds.has(e.source)&&nodeIds.has(e.target)&&e.source!==e.target).map(e=>({...e,id:uid(),type:'smoothstep'}))
       if(anchor&&blocks.length)edges.push({id:uid(),source:anchor.id,target:blocks[0].id,label:'Follow-up',type:'smoothstep'})
       return {...b,nodes:[...b.nodes,...nodes],edges:[...b.edges,...edges],messages:[...b.messages,{id:uid(),role:'assistant',content:answer.message,blockIds:blocks.map(v=>v.id),followUps:answer.followUps||[],mode:answer.mode,warnings:answer.warnings||[]}]}
     })
     if(blocks.length)setFeedback(`${blocks.length} findings added. Use “Show on canvas” to find them.`)
   }catch(e){if(!request.signal.aborted&&id===requestId.current)setError(e instanceof Error?e.message:'The local analysis failed. Try again.')}finally{if(id===requestId.current)setPending(false)}
 }
 const exportBoard=()=>{const data=JSON.stringify({version:1,activeId:board.id,boards:[board]},null,2);const url=URL.createObjectURL(new Blob([data],{type:'application/json'}));const link=document.createElement('a');link.href=url;link.download=`${board.name.toLowerCase().replace(/[^a-z0-9]+/g,'-')||'investigation'}.retail-canvas.json`;link.click();URL.revokeObjectURL(url);setPopover(null);setFeedback('Investigation exported, including results and evidence.')}
 const importBoard=async(fileToImport:File)=>{try{if(fileToImport.size>10*1024*1024)throw new Error('Choose a canvas file smaller than 10 MB.');const parsed=JSON.parse(await fileToImport.text());if(!validateState(parsed))throw new Error('This file is not a supported retail canvas.');const incoming=parsed.boards.map(b=>({...b,id:uid(),name:`${b.name} (imported)`}));const next={...current.current,activeId:incoming[0].id,boards:[...current.current.boards,...incoming]};if(next.boards.length>20)throw new Error('Keep at most 20 investigations in this browser.');cancel();current.current=next;setState(next);history.current={past:[],future:[]};setHistoryVersion(v=>v+1);setEvidenceId(null);flow.setViewport(incoming[0].viewport);setSaved(null);setFeedback('Investigation imported.')}catch(e){setFeedback(e instanceof Error?e.message:'Could not import this file.')}finally{if(file.current)file.current.value=''}}
 const visibleEdges=useMemo(()=>board.edges.map(e=>({...e,hidden:!showEdges&&!selected.some(n=>n.id===e.source||n.id===e.target),style:{stroke:'#9aafc2',strokeWidth:1.3},labelStyle:{fontSize:10,fill:'#617487'},labelBgStyle:{fill:'#f7f9fb',fillOpacity:.95},labelBgPadding:[5,3] as [number,number]})),[board.edges,showEdges,selected.map(n=>n.id).join(',')])
 return <div className={`cv-app ${(chatOpen||evidenceNode)?'has-dock':''}`}>
 <div className="cv-board-stage"><CanvasActions.Provider value={actions}><ReactFlow<BoardNode,Edge> nodes={board.nodes} edges={visibleEdges} nodeTypes={nodeTypes} onNodesChange={nodesChange} onEdgesChange={edgesChange} onConnect={connect} onNodeDragStart={()=>record(current.current.boards.find(b=>b.id===current.current.activeId)!)} onMoveEnd={(_,viewport)=>update(b=>({...b,viewport}),false)} defaultViewport={board.viewport} minZoom={.22} maxZoom={1.6} panOnDrag={panMode?[0,1,2]:[1,2]} selectionOnDrag={!panMode} nodesDraggable={!panMode} deleteKeyCode={['Backspace','Delete']} selectionKeyCode="Shift" multiSelectionKeyCode="Shift" zoomOnDoubleClick={false} onlyRenderVisibleElements proOptions={{hideAttribution:false}} onPaneClick={()=>setEvidenceId(null)} aria-label="Retail investigation canvas">
 <Background variant={BackgroundVariant.Dots} color="#a6a6a6" gap={24} size={1.4}/><Controls className="cv-flow-controls" showInteractive={false} showFitView={false}/>{showMap&&<MiniMap className="cv-minimap" nodeColor={n=>n.type==='heading'?'transparent':(n.data.block as {kind?:string})?.kind==='note'?'#d9e5f1':'#fff'} maskColor="rgba(241,241,241,.7)" pannable zoomable/>}
 </ReactFlow></CanvasActions.Provider></div>
 <div className="cv-toolrail" role="group" aria-label="Canvas tools">
 <button ref={menuButton} className={`cv-menu-trigger ${popover==='menu'?'active':''}`} aria-label="Investigation menu" aria-expanded={popover==='menu'} aria-controls="cv-board-menu" aria-haspopup="dialog" title="Investigation menu" onClick={()=>{setHelp(false);setPopover(popover==='menu'?null:'menu')}}><Menu size={19}/></button><i/>
 <button className={!panMode?'active':''} aria-label="Select and move nodes" aria-pressed={!panMode} title="Select and move" onClick={()=>setPanMode(false)}><MousePointer2 size={18}/></button>
 <button className={panMode?'active':''} aria-label="Pan canvas" aria-pressed={panMode} title="Pan canvas" onClick={()=>setPanMode(true)}><Hand size={18}/></button><i/>
 <button aria-label="Add text note" title="Add note" onClick={addNote}><PencilLine size={18}/></button>
 <button className={showEdges?'active':''} aria-label="Toggle all connections" aria-pressed={showEdges} title="Show connections" onClick={()=>setShowEdges(!showEdges)}><Link2 size={18}/></button><i/>
 <button ref={scopeButton} className={popover==='scope'?'active':''} aria-label="Scope for new investigations" aria-expanded={popover==='scope'} aria-controls="cv-scope-panel" aria-haspopup="dialog" title="Dates and market" onClick={openScope}><CalendarDays size={18}/></button>
 <button aria-label="Undo canvas change" title="Undo canvas change" disabled={!history.current.past.length} onClick={undo}><Undo2 size={18}/></button>
 <button aria-label="Redo canvas change" title="Redo canvas change" disabled={!history.current.future.length} onClick={redo}><Redo2 size={18}/></button><i/>
 <button aria-label="Fit canvas to findings" title="Fit all findings" onClick={fit}><Focus size={18}/></button>
 <button className={showMap?'active':''} aria-label="Toggle minimap" aria-pressed={showMap} title="Canvas overview" onClick={()=>setShowMap(!showMap)}><BarChart3 size={17}/></button>
 <button className={help?'active':''} aria-label="Canvas help" aria-pressed={help} title="Canvas help" onClick={()=>{setPopover(null);setHelp(!help)}}><HelpCircle size={18}/></button>
 </div>
 {popover==='menu'&&<div ref={popoverPanel} id="cv-board-menu" className="cv-chrome-popover cv-board-menu" role="dialog" aria-label="Investigation menu">
 <div className="cv-menu-heading"><div className="cv-board-name">{rename?<input autoFocus aria-label="Investigation name" value={board.name} maxLength={80} onChange={e=>update(b=>({...b,name:e.target.value}),false)} onBlur={()=>setRename(false)} onKeyDown={e=>{if(e.key==='Enter')setRename(false)}}/>:<button onClick={()=>setRename(true)} title="Rename investigation"><span>{board.name||'Untitled investigation'}</span><PencilLine size={14}/></button>}<span role="status">{saved?<><Check size={11}/>Saved on this device</>:saved===null?'Saving…':'Not saved — export a copy'}</span></div></div>
 <label className="cv-menu-switch">Switch investigation<select value={board.id} onChange={e=>switchBoard(e.target.value)}>{state.boards.map(b=><option key={b.id} value={b.id}>{b.name||'Untitled investigation'}</option>)}</select></label>
 <div className="cv-menu-actions"><button disabled={state.boards.length>=20} onClick={()=>{newBoard();setPopover(null)}}><Plus size={16}/>New investigation</button><button onClick={exportBoard}><ArrowDownToLine size={16}/>Export investigation</button><button onClick={()=>{file.current?.click();setPopover(null)}}><Import size={16}/>Import investigation</button></div>
 <a className="cv-menu-back" href="/"><ArrowLeft size={15}/>Back to dashboard</a>
 </div>}
 {popover==='scope'&&<div ref={popoverPanel} id="cv-scope-panel" className="cv-chrome-popover cv-scope-panel" role="dialog" aria-labelledby="cv-scope-title"><h2 id="cv-scope-title">Investigation scope</h2><p>Applies to new investigations. Existing findings keep their original scope.</p>
 <form noValidate onSubmit={e=>{e.preventDefault();applyScope()}}><div className="cv-year-group" role="group" aria-label="Period for new investigations">{[['all','All data'],['2010','2010'],['2011','2011']].map(([value,label])=><button type="button" key={value} className={year===value?'active':''} aria-pressed={year===value} onClick={()=>setYear(value)}>{label}</button>)}</div>
 <div className="cv-date-fields"><label>Start date<input type="date" required min={retailMeta.start} max={retailMeta.end} value={scopeDraft.start} aria-invalid={Boolean(scopeError)} aria-describedby={scopeError?'cv-scope-error':undefined} onChange={e=>{setScopeDraft(s=>({...s,start:e.target.value}));setScopeError('')}}/></label><label>End date<input type="date" required min={retailMeta.start} max={retailMeta.end} value={scopeDraft.end} aria-invalid={Boolean(scopeError)} aria-describedby={scopeError?'cv-scope-error':undefined} onChange={e=>{setScopeDraft(s=>({...s,end:e.target.value}));setScopeError('')}}/></label></div>
 <label className="cv-scope-market">Market<select value={scopeDraft.country} onChange={e=>setScopeDraft(s=>({...s,country:e.target.value}))}><option value="all">All markets</option>{retailMeta.countries.map(c=><option key={c}>{c}</option>)}</select></label>
 <p className="cv-coverage-note">1 Dec 2009 – 9 Dec 2011 · December 2011 is incomplete.</p>{scopeError&&<p id="cv-scope-error" className="cv-scope-error" role="alert">{scopeError}</p>}
 <div className="cv-scope-actions"><button type="button" className="cv-button" onClick={()=>{setPopover(null);scopeButton.current?.focus()}}>Cancel</button><button className="cv-button primary" type="submit">Apply scope<Check size={13}/></button></div></form></div>}
 {board.nodes.length===0&&<div className="cv-empty-board"><span><BarChart3 size={29}/></span><h1>A little space to explore.</h1><p>Start with a question. Your charts, findings, and next ideas will find their place here.</p><button className="cv-button primary" onClick={()=>{setChatOpen(true);send('Explore sales trends','sales')}}>Explore the sales story<ArrowUpRight size={15}/></button></div>}
 {help&&<div className="cv-help"><button className="cv-icon" aria-label="Close help" onClick={()=>setHelp(false)}><X size={15}/></button><h2>Follow your curiosity.</h2><p>Drag a card to arrange your thinking. Scroll to zoom; use the hand tool to pan. Select a finding before asking a follow-up.</p><p>Connections show relationships, never proof of cause. Your scope controls apply to new findings; existing evidence keeps its original filters.</p><p>Shift + drag selects several nodes. Delete removes selected nodes. Add a note to keep your own interpretation.</p></div>}
 {notice&&<div className="cv-service-notice"><span>{notice}</span><button aria-label="Dismiss service notice" onClick={()=>setNotice('')}><X size={12}/></button></div>}
 {(chatOpen||evidenceNode)?<div className={`cv-right-dock ${chatOpen?'is-open':''}`}>{evidenceNode?<EvidencePanel key={evidenceNode.id} node={evidenceNode} onClose={()=>setEvidenceId(null)} onEdit={editNote}/>:<CanvasChat messages={board.messages} capabilities={capabilities} selected={selected} pending={pending} slow={slow} error={error} onSend={send} onCancel={cancel} onClearSelection={clearSelection} onFocus={focus} onClose={()=>setChatOpen(false)} onRetry={()=>{if(lastRequest.current)send(...lastRequest.current)}}/>}</div>:null}
 <button className={`cv-chat-toggle ${chatOpen?'chat-is-open':''}`} aria-label={chatOpen?'Close retail analyst':'Open retail analyst'} onClick={()=>{setEvidenceId(null);setChatOpen(!chatOpen)}}><MessageSquare size={18}/><span>{pending?'Working…':'Retail analyst'}</span>{!capabilities?.llmConfigured&&<small>Guided</small>}</button>
 <div className="cv-bottom-caption"><span>UCI Online Retail II</span><i/>Historical data · GBP<i/><span>Pan, connect, explore.</span></div>
 {feedback&&<div className="cv-toast" role="status">{feedback}<button aria-label="Dismiss message" onClick={()=>setFeedback('')}><X size={12}/></button></div>}
 <input type="file" ref={file} className="cv-file-input" accept=".json" aria-label="Import investigation file" onChange={event=>{const f=event.target.files?.[0];if(f)importBoard(f)}}/>
 </div>
}
export default function CanvasApp(){return <ReactFlowProvider><Workspace/></ReactFlowProvider>}




