"""Actual recorded molecules and fixed density projections, never synthetic objects."""
import argparse
import json
from pathlib import Path
import numpy as np
from scipy.ndimage import uniform_filter
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import experiment as model


def main(raw,out):
    raw,out=Path(raw),Path(out);n=48
    cases=['driven_minus','common_saddle_minus','matched_passive_minus']
    titles=['Different saddle; chemical drive -2','Common saddle; chemical drive -2','Passive matched equilibrium, df=.2']
    fig=plt.figure(figsize=(14,9),layout='constrained');inputs={};limits=[]
    for i,(case,title) in enumerate(zip(cases,titles)):
        path=raw/'volume'/f'{case}-d3-n48-T1000-s127'
        cells,pos,states,_=model.fields(path,n,3,100)
        for p in sorted(path.glob('state-100-*.bin')):inputs[str(p)]=model.digest(p)
        coords=np.array(np.unravel_index(pos,(n,n,n),order='F')).T
        ax=fig.add_subplot(2,3,i+1,projection='3d')
        for state,color,label in [(0,'#a9b0ba','I'),(1,'#176a9c','B')]:
            q=coords[states==state]
            ax.scatter(q[:,0],q[:,1],q[:,2],s=1.1,alpha=.55 if state else .2,c=color,label=label,rasterized=True,depthshade=False)
        ax.set(xlim=(0,n),ylim=(0,n),zlim=(0,n),xlabel='x',ylabel='y',zlabel='z',title=title)
        ax.set_box_aspect((1,1,1));ax.view_init(elev=24,azim=-55);ax.legend(loc='upper right',markerscale=4)
        rho=uniform_filter((cells>0).astype(float),size=4,mode='wrap')
        projection=rho.mean(axis=2).T;limits.append([float(projection.min()),float(projection.max())])
        bx=fig.add_subplot(2,3,i+4)
        image=bx.imshow(projection,origin='lower',extent=(0,n,0,n),vmin=0,vmax=1,cmap='viridis',interpolation='nearest')
        bx.set(xlabel='x',ylabel='y',title='Mean material density along z\nlocal average width=4 molecular cells')
        fig.colorbar(image,ax=bx,shrink=.75,label='occupied fraction (0..1)')
    fig.suptitle('Recorded 3D local fluid | N=48, t=1000, first holdout seed127\n'
                 'Every plotted point is one actual molecule; common-saddle and passive controls also concentrate. No membrane claim.',fontsize=11)
    fig.savefig(out,dpi=160)
    model.save(out.with_suffix('.json'),{'physics_modified':False,'source_sha256':inputs,
        'selection':'first preregistered holdout seed, largest preregistered volume, all three matched cases',
        'marker_is_one_recorded_molecule':True,'camera':{'elevation':24,'azimuth':-55},
        'density_projection_not_a_cross_section':True,'smoothing_width':4,'color_limits':[0,1],'actual_projection_limits':limits})


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('raw');p.add_argument('out');a=p.parse_args();main(a.raw,a.out)
