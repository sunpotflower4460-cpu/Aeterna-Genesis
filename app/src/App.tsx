import { useEffect, useState } from 'react'
import { useStore } from './store'
import { loadCatalog } from './lib/data'
import Lobby from './components/Lobby'
import RoomWorkspace from './components/RoomWorkspace'
import CompareView from './components/CompareView'
import Inbox from './components/Inbox'
import AquariumView from './aquarium/AquariumView'
import LabView from './lab/LabView'
import { labAvailable } from './lab/api'

// read before the aquarium rewrites the hash to its template id
const WANT_LAB = typeof location !== 'undefined' && location.hash === '#lab'

export default function App() {
  const catalog = useStore((s) => s.catalog)
  const setCatalog = useStore((s) => s.setCatalog)
  const view = useStore((s) => s.view)
  const toLobby = useStore((s) => s.toLobby)
  const toAquarium = useStore((s) => s.toAquarium)
  const toLab = useStore((s) => s.toLab)
  const [labOk, setLabOk] = useState(false)
  const [labChecked, setLabChecked] = useState(false)
  const [catalogError, setCatalogError] = useState<string | null>(null)

  useEffect(() => {
    // The catalog is generated data (tools/build_catalog.py); the aquarium works without it.
    loadCatalog().then(setCatalog).catch((e) => setCatalogError(String(e)))
  }, [setCatalog])

  useEffect(() => {
    // The live lab exists only when the app is served by tools/lab/server.py (not on the static deploy).
    labAvailable().then((ok) => {
      setLabOk(ok)
      setLabChecked(true)
      if (ok && WANT_LAB) toLab()
    })
  }, [toLab])

  if (view === 'lab') return <LabView onExit={() => { history.replaceState(null, '', location.pathname + location.search); toAquarium() }} />
  if (WANT_LAB && !labChecked) return <div className="aq-center mono muted">◈ connecting to the lab…</div>
  if (view === 'aquarium') {
    return <AquariumView onOpenObservatory={catalog ? toLobby : undefined}
      onOpenLab={labOk ? () => { history.replaceState(null, '', '#lab'); toLab() } : undefined} />
  }

  if (!catalog) {
    return (
      <div style={{ height: '100%', display: 'grid', placeItems: 'center', textAlign: 'center', padding: 24 }}>
        <div className="mono muted" style={{ letterSpacing: '.1em' }}>
          {catalogError
            ? <>Observatory のデータが未生成です（python tools/build_catalog.py && python tools/collect_app_data.py）</>
            : <>◈ loading observatory…</>}
          <div style={{ marginTop: 16 }}><button className="tbtn" onClick={toAquarium}>← 水槽へ</button></div>
        </div>
      </div>
    )
  }
  const body = view === 'room' ? <RoomWorkspace /> : view === 'compare' ? <CompareView /> : view === 'inbox' ? <Inbox /> : <Lobby />
  return (
    <>
      {body}
      <button className="tbtn aq-back" onClick={toAquarium} title="水槽へ戻る">◈ 水槽</button>
    </>
  )
}
