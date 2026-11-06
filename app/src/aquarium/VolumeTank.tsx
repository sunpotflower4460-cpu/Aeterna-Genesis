import { useEffect, useMemo, useRef } from 'react'
import { useFrame, useThree } from '@react-three/fiber'
import * as THREE from 'three'
import type { FrameSource, Transfer } from './types'
import { AXIS_INDEX, COLOR_GLSL, DEFAULT_APPEARANCE, MODE, PALETTE_INDEX, QUALITY_STEPS, type Appearance } from './render/appearance'
import { makeFieldTexture, uploadField } from './render/texture'

// Read-only volume rendering. Opacity, palette, gradient lighting and slicing are visualization choices;
// no particle, geometry, interpolation or illumination is fed back to the solver or its diagnostics.
const VERT = /* glsl */ `
  out vec3 vObj;
  void main(){vObj=position;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0);}
`
const FRAG = /* glsl */ `
  precision highp float;
  precision highp sampler3D;
  in vec3 vObj; out vec4 outColor;
  uniform sampler3D uA; uniform sampler3D uB; uniform float uMix;
  uniform vec2 uAffA; uniform vec2 uAffB; uniform vec3 uCam; uniform vec3 uVoxel;
  uniform float uThr; uniform float uDensity; uniform float uSteps;
  uniform bool uShading; uniform bool uSlice; uniform bool uSurface; uniform int uAxis; uniform float uPosition;
  ${COLOR_GLSL}
  vec2 sampleField(vec3 p){return decodeField(texture(uA,p).rg,texture(uB,p).rg,uMix,uAffA,uAffB);}
  float delta(float a,float b){float d=a-b;return uMode==2?d-floor(d+0.5):d;}
  vec2 hitBox(vec3 o,vec3 d){
    // Avoid 0*infinity at a cube face for an exactly axial camera.
    vec3 inv=sign(d+vec3(1e-10))/max(abs(d),vec3(1e-8));
    vec3 a=(vec3(-0.5)-o)*inv,b=(vec3(0.5)-o)*inv;
    vec3 lo=min(a,b),hi=max(a,b);
    return vec2(max(max(lo.x,lo.y),lo.z),min(min(hi.x,hi.y),hi.z));
  }
  void main(){
    vec3 rd=normalize(vObj-uCam);vec2 span=hitBox(uCam,rd);span.x=max(span.x,0.0);
    if(span.x>=span.y)discard;
    if(uSlice){
      float dir=uAxis==0?rd.x:(uAxis==1?rd.y:rd.z);
      float origin=uAxis==0?uCam.x:(uAxis==1?uCam.y:uCam.z);
      if(abs(dir)<1e-7)discard;
      float s=(uPosition-0.5-origin)/dir;
      if(s<span.x||s>span.y)discard;
      vec2 field=sampleField(uCam+rd*s+0.5);
      if(field.y<0.02)discard;
      outColor=vec4(fieldColor(field.x),field.y);return;
    }
    float dt=1.7320508/uSteps;
    if(uSurface){
      vec2 previous=sampleField(uCam+rd*span.x+0.5);
      float previousS=span.x;
      for(int i=0;i<320;i++){
        float s=min(span.x+(float(i)+1.0)*dt,span.y);
        vec2 field=sampleField(uCam+rd*s+0.5);
        bool wrap=uMode==2&&abs(field.x-previous.x)>0.5;
        if(!wrap&&field.y>0.02&&previous.y>0.02&&abs(field.x-previous.x)>1e-6&&(field.x-uThr)*(previous.x-uThr)<=0.0){
          float a=previousS,b=s,va=previous.x;
          for(int j=0;j<5;j++){
            float mid=(a+b)*0.5;float v=sampleField(uCam+rd*mid+0.5).x;
            if((va-uThr)*(v-uThr)<=0.0)b=mid;else{a=mid;va=v;}
          }
          vec3 p=uCam+rd*(a+b)*0.5+0.5;
          vec3 color=fieldColor(uThr);
          if(uShading){
            vec3 g=vec3(delta(sampleField(p+vec3(uVoxel.x,0.0,0.0)).x,sampleField(p-vec3(uVoxel.x,0.0,0.0)).x),
                        delta(sampleField(p+vec3(0.0,uVoxel.y,0.0)).x,sampleField(p-vec3(0.0,uVoxel.y,0.0)).x),
                        delta(sampleField(p+vec3(0.0,0.0,uVoxel.z)).x,sampleField(p-vec3(0.0,0.0,uVoxel.z)).x))/uVoxel;
            vec3 n=g/max(length(g),1e-6);if(dot(n,rd)>0.0)n=-n;
            vec3 light=normalize(vec3(-0.4,0.8,0.5));
            float key=max(dot(n,light),0.0),fill=max(dot(n,normalize(vec3(0.7,0.2,-0.5))),0.0);
            float specular=pow(max(dot(n,normalize(light-rd)),0.0),32.0);
            color=color*(0.30+0.60*key+0.20*fill)+vec3(0.16)*specular;
          }
          outColor=vec4(color,1.0);return;
        }
        if(s>=span.y)break;previous=field;previousS=s;
      }
      discard;
    }
    vec4 acc=vec4(0.0);
    for(int i=0;i<320;i++){
      float s=span.x+(float(i)+0.5)*dt;
      if(s>span.y||acc.a>0.995)break;
      vec3 p=uCam+rd*s+0.5;vec2 field=sampleField(p);float v=field.x;
      float weight;
      if(uMode==0)weight=smoothstep(uThr,1.0,v);
      else if(uMode==1)weight=1.0-smoothstep(0.0,uThr,v);
      else if(uMode==2)weight=0.12*uThr;
      else weight=smoothstep(uThr*0.5,0.5,abs(v-0.5));
      weight*=field.y;if(weight<0.002)continue;
      vec3 color=fieldColor(v);
      if(uShading&&uMode!=2){
        // A normal of the measured scalar field, used solely to make its shape legible.
        vec3 gradient=vec3(sampleField(p+vec3(uVoxel.x,0.0,0.0)).x-v,
                           sampleField(p+vec3(0.0,uVoxel.y,0.0)).x-v,
                           sampleField(p+vec3(0.0,0.0,uVoxel.z)).x-v)/uVoxel;
        float magnitude=length(gradient);
        if(magnitude>1e-4){
          vec3 n=gradient/magnitude;
          float key=abs(dot(n,normalize(vec3(-0.4,0.8,0.5))));
          float rim=pow(1.0-abs(dot(n,-rd)),2.0);
          color*=0.66+0.34*key;color+=color*0.20*rim;
        }
      }
      // Beer-Lambert opacity, independent of chosen ray sampling density.
      float alpha=1.0-exp(-weight*uDensity*48.0*dt);
      acc.rgb+=(1.0-acc.a)*alpha*color;acc.a+=(1.0-acc.a)*alpha;
    }
    if(acc.a<0.003)discard;
    // acc is premultiplied; Three's normal blending expects straight alpha.
    outColor=vec4(acc.rgb/max(acc.a,1e-6),acc.a);
  }
`
export default function VolumeTank({ src, transfer, clock, threshold, density, appearance = DEFAULT_APPEARANCE }: {
  src: FrameSource; transfer: Transfer; clock: React.MutableRefObject<number>
  threshold: number; density: number; appearance?: Appearance
}) {
  const mesh = useRef<THREE.Mesh>(null)
  const { camera } = useThree()
  const cyclic = transfer === 'cyclic'
  const gridKey = src.grid.join('x')
  const textures = useMemo(() => [makeFieldTexture(src.grid, cyclic), makeFieldTexture(src.grid, cyclic)] as const, [gridKey, cyclic])
  const loaded = useRef<[number, number]>([-1, -1])
  const inverse = useMemo(() => new THREE.Matrix4(), [])
  const material = useMemo(() => new THREE.ShaderMaterial({
    glslVersion: THREE.GLSL3, vertexShader: VERT, fragmentShader: FRAG,
    transparent: true, depthWrite: false, side: THREE.BackSide, toneMapped: false,
    uniforms: {
      uA:{value:textures[0]},uB:{value:textures[1]},uMix:{value:0},uCam:{value:new THREE.Vector3()},
      uAffA:{value:new THREE.Vector2(1,0)},uAffB:{value:new THREE.Vector2(1,0)},
      uVoxel:{value:new THREE.Vector3(1/src.grid[2],1/src.grid[1],1/src.grid[0])},
      uMode:{value:MODE[transfer]},uPalette:{value:0},uThr:{value:threshold},uDensity:{value:density},
      uSteps:{value:144},uShading:{value:true},uSlice:{value:false},uSurface:{value:false},uAxis:{value:2},uPosition:{value:0.5},
    },
  }), [textures])
  useEffect(() => { loaded.current=[-1,-1] }, [src, textures])
  useEffect(() => () => { textures.forEach((t) => t.dispose());material.dispose() }, [textures, material])
  useFrame(() => {
    if(!mesh.current || src.count<1)return
    const position=Math.min(Math.max(clock.current,0),src.count-1)
    const a=Math.floor(position),b=appearance.interpolate?Math.min(a+1,src.count-1):a
    for(const [slot,frame] of [[0,a],[1,b]] as const){
      const key=src.key(frame)
      if(loaded.current[slot]!==key && uploadField(textures[slot],src.data(frame),cyclic)) loaded.current[slot]=key
    }
    const u=material.uniforms
    u.uMix.value=appearance.interpolate?position-a:0
    u.uAffA.value.set(...src.affine(a));u.uAffB.value.set(...src.affine(b))
    u.uMode.value=MODE[transfer];u.uPalette.value=PALETTE_INDEX[appearance.palette]
    u.uThr.value=threshold;u.uDensity.value=density;u.uSteps.value=QUALITY_STEPS[appearance.quality]
    u.uShading.value=appearance.shading;u.uSlice.value=appearance.mode==='slice'
    u.uSurface.value=appearance.mode==='surface'
    u.uAxis.value=AXIS_INDEX[appearance.axis];u.uPosition.value=appearance.slice
    mesh.current.updateMatrixWorld()
    u.uCam.value.copy(camera.position).applyMatrix4(inverse.copy(mesh.current.matrixWorld).invert())
  })
  return <mesh ref={mesh} material={material}><boxGeometry args={[1,1,1]}/></mesh>
}
