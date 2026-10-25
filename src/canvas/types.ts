import type { Edge, Node, Viewport } from '@xyflow/react'

export type Tool = 'sales' | 'markets' | 'product' | 'customers' | 'baskets'
export interface Scope { start:string; end:string; country:string; productCode?:string; countries?:string[] }
export interface Evidence { tool:string;source:string;sourceUrl:string;sourceSha256:string;scope:Scope;rowCount:number;definitions:string[];query:string;generatedAt:string }
export interface Block {id:string;kind:'chart'|'note';title:string;subtitle?:string;body?:string;tone?:'neutral'|'blue'|'amber';chartType?:'line'|'bar'|'donut'|'scatter'|'table';rows?:Record<string,string|number|null>[];xKey?:string;series?:{key:string;label:string}[];format?:'currency'|'percent'|'number';evidence:Evidence}
export interface FollowUp {label:string;prompt:string;tool:Tool;productCode?:string}
export interface AnalysisResponse {id:string;title:string;mode:'guided'|'llm';message:string;blocks:Block[];connections:{source:string;target:string;label:string}[];followUps:FollowUp[];warnings:string[]}
export interface Capabilities {mode:'guided'|'llm';llmConfigured:boolean;model:string|null;source:string;start:string;end:string;countries:string[];suggestions:FollowUp[]}
export interface CanvasNodeData extends Record<string,unknown> {block:Block;groupId:string;originQuestion:string}
export type AnalysisNode = Node<CanvasNodeData,'analysis'>
export interface HeadingData extends Record<string,unknown> {title:string;subtitle:string;groupId:string}
export type HeadingNode = Node<HeadingData,'heading'>
export type BoardNode = AnalysisNode | HeadingNode
export interface ChatMessage {id:string;role:'user'|'assistant';content:string;blockIds?:string[];followUps?:FollowUp[];mode?:'guided'|'llm';warnings?:string[];error?:boolean}
export interface Board {id:string;name:string;nodes:BoardNode[];edges:Edge[];messages:ChatMessage[];scope:Scope;viewport:Viewport;updatedAt:string}
export interface BoardState {version:1;activeId:string;boards:Board[]}
export interface InvestigateRequest {message:string;scope:Scope;tool?:Tool;productCode?:string;countries?:string[];selected?:{id:string;title:string;evidence:Evidence}[];history?:{role:'user'|'assistant';content:string}[]}
export const uid = () => crypto.randomUUID()
