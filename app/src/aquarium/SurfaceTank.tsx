import { useEffect, useMemo, useRef } from 'react'
import { useFrame } from '@react-three/fiber'
import * as THREE from 'three'
import type { FrameSource, Transfer } from './types'
import { COLOR_GLSL, DEFAULT_APPEARANCE, MODE, PALETTE_INDEX, type Appearance } from './render/appearance'
import { makeFieldTexture, uploadField } from './render/texture'

// A 2D measured field. Relief is an explicitly artificial height encoding of that scalar, not 3D physics.
const VERT = /* glsl */ `
  uniform sampler2D uA;uniform sampler2D uB;uniform float uMix;
  uniform vec2 uAffA;uniform vec2 uAffB;uniform float uHeight;
  out vec2 vUv;out vec3 vWorld;
  ${COLOR_GLSL}
  void main(){
    vec2 field=decodeField(texture(uA,uv).rg,texture(uB,uv).rg,uMix,uAffA,uAffB);
    vUv=uv;
    vec3 p=position;p.z+=(uMode==2?0.0:field.x-0.5)*uHeight;
    vWorld=(modelMatrix*vec4(p,1.0)).xyz;
    gl_Position=projectionMatrix*modelViewMatrix*vec4(p,1.0);
  }
`
const FRAG = /* glsl */ `
  precision highp float;
  in vec2 vUv;in vec3 vWorld;out vec4 outColor;
  uniform sampler2D uA;uniform sampler2D uB;uniform float uMix;uniform vec2 uAffA;uniform vec2 uAffB;
  uniform bool uShading;uniform bool uContours;
  ${COLOR_GLSL}
  void main(){
    vec2 field=decodeField(texture(uA,vUv).rg,texture(uB,vUv).rg,uMix,uAffA,uAffB);
    float vVal=field.x,vConfidence=field.y;
    if(vConfidence<0.02)discard;
    vec3 color=fieldColor(vVal);
    if(uShading&&uMode!=2){
      vec3 n=normalize(cross(dFdx(vWorld),dFdy(vWorld)));
      float key=abs(dot(n,normalize(vec3(-0.4,0.8,0.5))));color*=0.76+0.24*key;
    }
    if(uContours){
      float distance=abs(fract(vVal*10.0+0.5)-0.5)/max(fwidth(vVal)*10.0,0.025);
      float ink=1.0-smoothstep(0.5,1.3,distance);color=mix(color,color*0.48,ink*0.55);
    }
    outColor=vec4(color,vConfidence);
  }
`
export default function SurfaceTank({ src, transfer, clock, relief, appearance=DEFAULT_APPEARANCE }: {
  src: FrameSource;transfer: Transfer;clock: React.MutableRefObject<number>;relief:number;appearance?:Appearance
}) {
  const cyclic=transfer==='cyclic',gridKey=src.grid.join('x')
  const textures=useMemo(()=>[makeFieldTexture(src.grid,cyclic),makeFieldTexture(src.grid,cyclic)] as const,[gridKey,cyclic])
  const loaded=useRef<[number,number]>([-1,-1])
  const segments=Math.min(192,Math.max(src.grid[0],src.grid[1])*2)
  const material=useMemo(()=>new THREE.ShaderMaterial({
    glslVersion:THREE.GLSL3,vertexShader:VERT,fragmentShader:FRAG,transparent:true,
    side:THREE.DoubleSide,toneMapped:false,
    uniforms:{uA:{value:textures[0]},uB:{value:textures[1]},uMix:{value:0},uHeight:{value:relief},
      uAffA:{value:new THREE.Vector2(1,0)},uAffB:{value:new THREE.Vector2(1,0)},
      uMode:{value:MODE[transfer]},uPalette:{value:0},uShading:{value:true},uContours:{value:false}},
  }),[textures])
  useEffect(()=>{loaded.current=[-1,-1]},[src,textures])
  useEffect(()=>()=>{textures.forEach(t=>t.dispose());material.dispose()},[textures,material])
  useFrame(()=>{
    if(src.count<1)return
    const position=Math.min(Math.max(clock.current,0),src.count-1)
    const a=Math.floor(position),b=appearance.interpolate?Math.min(a+1,src.count-1):a
    for(const [slot,frame] of [[0,a],[1,b]] as const){
      const key=src.key(frame)
      if(loaded.current[slot]!==key&&uploadField(textures[slot],src.data(frame),cyclic))loaded.current[slot]=key
    }
    const u=material.uniforms
    u.uMix.value=appearance.interpolate?position-a:0
    u.uAffA.value.set(...src.affine(a));u.uAffB.value.set(...src.affine(b))
    u.uMode.value=MODE[transfer];u.uPalette.value=PALETTE_INDEX[appearance.palette]
    u.uHeight.value=relief;u.uShading.value=appearance.shading;u.uContours.value=appearance.contours
  })
  return <mesh material={material} rotation={[-Math.PI/2,0,0]} position={[0,-0.15,0]}>
    <planeGeometry args={[1,1,segments,segments]}/>
  </mesh>
}
