import { useEffect, useMemo } from 'react'
import * as THREE from 'three'

/** Coordinate guides only: no walls, forces, mirror images or invented particles. */
export default function FieldGuides({ dimension=3 }: { dimension?:2|3 }) {
  const geometry=useMemo(()=>{
    const points:number[]=[]
    const line=(a:number[],b:number[])=>points.push(...a,...b)
    const floor=dimension===3?-0.503:-0.32
    for(let i=0;i<=8;i++){
      const p=i/8-0.5
      line([p,floor,-0.5],[p,floor,0.5]);line([-0.5,floor,p],[0.5,floor,p])
    }
    if(dimension===3){
      for(const x of [-0.5,0.5])for(const z of [-0.5,0.5])line([x,-0.5,z],[x,0.5,z])
      for(const y of [-0.5,0.5]){
        line([-0.5,y,-0.5],[0.5,y,-0.5]);line([-0.5,y,0.5],[0.5,y,0.5])
        line([-0.5,y,-0.5],[-0.5,y,0.5]);line([0.5,y,-0.5],[0.5,y,0.5])
      }
    }
    const geo=new THREE.BufferGeometry();geo.setAttribute('position',new THREE.Float32BufferAttribute(points,3));return geo
  },[dimension])
  useEffect(()=>()=>geometry.dispose(),[geometry])
  return <lineSegments geometry={geometry} renderOrder={1}>
    <lineBasicMaterial color="#65869e" transparent opacity={0.24} depthWrite={false} toneMapped={false}/>
  </lineSegments>
}
