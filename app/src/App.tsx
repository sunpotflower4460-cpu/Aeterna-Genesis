import { useEffect } from 'react'
import { useStore } from './store'
import { loadCatalog, loadAquariumRegistry, loadAquariumNotebook } from './lib/data'
import Lobby from './components/Lobby'
import RoomWorkspace from './components/RoomWorkspace'
import CompareView from './components/CompareView'
import Inbox from './components/Inbox'
import AquariumLab from './components/AquariumLab'

export default function App() {
  const catalog = useStore((s) => s.catalog)
  const setCatalog = useStore((s) => s.setCatalog)
  const setAquariumRegistry = useStore((s) => s.setAquariumRegistry)
  const setAquariumNotebook = useStore((s) => s.setAquariumNotebook)
  const view = useStore((s) => s.view)

  useEffect(() => {
    loadCatalog().then(setCatalog).catch((e) => console.error('catalog load failed', e))
    loadAquariumRegistry().then(setAquariumRegistry).catch((e) => console.warn('aquarium registry load failed', e))
    loadAquariumNotebook().then(setAquariumNotebook).catch((e) => console.warn('aquarium notebook load failed', e))
  }, [setCatalog, setAquariumRegistry, setAquariumNotebook])

  if (!catalog) {
    return (
      <div style={{ height: '100%', display: 'grid', placeItems: 'center' }}>
        <div className="mono muted" style={{ letterSpacing: '.15em' }}>◈ loading observatory…</div>
      </div>
    )
  }
  if (view === 'room') return <RoomWorkspace />
  if (view === 'compare') return <CompareView />
  if (view === 'inbox') return <Inbox />
  if (view === 'aquaria') return <AquariumLab />
  return <Lobby />
}
