import React, { lazy, Suspense } from 'react'
import ReactDOM from 'react-dom/client'
import '@fontsource-variable/dm-sans'
import App from './App'
import './styles.css'
import './motion.css'
const CanvasApp = lazy(() => import('./canvas/CanvasApp'))
ReactDOM.createRoot(document.getElementById('root')!).render(<React.StrictMode>{window.location.pathname.startsWith('/canvas')?<Suspense fallback={<div style={{padding:32,color:'#617487',fontSize:13}}>Opening your investigation canvas…</div>}><CanvasApp/></Suspense>:<App/>}</React.StrictMode>)
