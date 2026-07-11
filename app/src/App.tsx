import { useEffect } from 'react'
import { useStore } from './store'
import { loadCatalog } from './lib/data'
import Lobby from './components/Lobby'
import RoomWorkspace from './components/RoomWorkspace'

export default function App() {
  const catalog = useStore((s) => s.catalog)
  const setCatalog = useStore((s) => s.setCatalog)
  const view = useStore((s) => s.view)

  useEffect(() => {
    loadCatalog().then(setCatalog).catch((e) => console.error('catalog load failed', e))
  }, [setCatalog])

  if (!catalog) {
    return (
      <div style={{ height: '100%', display: 'grid', placeItems: 'center' }}>
        <div className="mono muted" style={{ letterSpacing: '.15em' }}>◈ loading observatory…</div>
      </div>
    )
  }
  return view === 'room' ? <RoomWorkspace /> : <Lobby />
}
