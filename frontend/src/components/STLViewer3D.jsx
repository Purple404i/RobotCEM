import React, { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls';
import { STLLoader } from 'three/examples/jsm/loaders/STLLoader';
import { Box, Layers, Maximize2, Loader2 } from 'lucide-react';

export default function STLViewer3D({ stlUrl, mode = 'threejs', jobId, apiBase }) {
  const mountRef = useRef(null);
  const [loading, setLoading] = useState(true);
  const [meshInfo, setMeshInfo] = useState(null);
  const sceneRef = useRef(null);
  const rendererRef = useRef(null);
  const meshRef = useRef(null);

  useEffect(() => {
    setLoading(true);
    if (!stlUrl || mode !== 'threejs') return;

    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x121216);
    sceneRef.current = scene;

    const camera = new THREE.PerspectiveCamera(50, mountRef.current.clientWidth / mountRef.current.clientHeight, 0.1, 1000);
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(mountRef.current.clientWidth, mountRef.current.clientHeight);
    renderer.setPixelRatio(window.devicePixelRatio);
    mountRef.current.appendChild(renderer.domElement);
    rendererRef.current = renderer;

    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;

    scene.add(new THREE.AmbientLight(0xffffff, 0.5));
    const pointLight = new THREE.PointLight(0x3b82f6, 1);
    pointLight.position.set(10, 10, 10);
    scene.add(pointLight);

    const grid = new THREE.GridHelper(100, 20, 0x334155, 0x1e293b);
    grid.position.y = -10;
    scene.add(grid);

    const loader = new STLLoader();
    setLoading(true);

    loader.load(stlUrl, (geometry) => {
      geometry.center();
      const material = new THREE.MeshPhongMaterial({
        color: 0x3b82f6,
        specular: 0x111111,
        shininess: 200,
        flatShading: false
      });
      const mesh = new THREE.Mesh(geometry, material);
      scene.add(mesh);
      meshRef.current = mesh;

      geometry.computeBoundingBox();
      const size = new THREE.Vector3();
      geometry.boundingBox.getSize(size);

      setMeshInfo({
        vertices: geometry.attributes.position.count,
        x: size.x.toFixed(1),
        y: size.y.toFixed(1),
        z: size.z.toFixed(1)
      });

      camera.position.set(size.x * 2, size.y * 2, size.z * 2);
      setLoading(false);
    });

    const animate = () => {
      requestAnimationFrame(animate);
      controls.update();
      renderer.render(scene, camera);
    };
    animate();

    const handleResize = () => {
        if (!mountRef.current) return;
        camera.aspect = mountRef.current.clientWidth / mountRef.current.clientHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(mountRef.current.clientWidth, mountRef.current.clientHeight);
    };
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      if (mountRef.current) mountRef.current.removeChild(renderer.domElement);
      renderer.dispose();
    };
  }, [stlUrl]);

  return (
    <div className="relative w-full h-full group">
      {mode === 'threejs' ? (
        <div ref={mountRef} className="w-full h-full" />
      ) : (
        <div className="w-full h-full flex items-center justify-center bg-slate-950 relative">
          <img
            src={`${apiBase}/api/render/${jobId}`}
            className="max-w-full max-h-full object-contain shadow-2xl"
            alt="Blender Scientific Render"
            onLoad={() => setLoading(false)}
            onError={() => setLoading(false)}
          />
          {loading && (
             <div className="absolute inset-0 flex items-center justify-center bg-slate-900/40 backdrop-blur-sm">
                <Loader2 className="animate-spin text-blue-500" size={32} />
             </div>
          )}
          <div className="absolute bottom-6 right-6 px-4 py-2 bg-black/60 backdrop-blur rounded-xl border border-white/10 text-[10px] font-bold text-white uppercase tracking-widest">
            Cycles Photorealistic Render
          </div>
        </div>
      )}

      {loading && mode === 'threejs' && (
        <div className="absolute inset-0 flex flex-col items-center justify-center bg-slate-900/50 backdrop-blur-sm z-20">
          <Loader2 className="animate-spin text-blue-500 mb-2" size={32} />
          <span className="text-[10px] font-black uppercase tracking-widest text-slate-400">Loading Geometry</span>
        </div>
      )}

      {meshInfo && (
        <div className="absolute bottom-6 left-6 p-4 rounded-2xl bg-slate-900/80 backdrop-blur border border-slate-800 pointer-events-none transition-opacity duration-500 flex gap-6">
           <div className="space-y-1">
              <span className="text-[10px] font-bold text-slate-500 uppercase tracking-tight">Geometry Size</span>
              <p className="text-xs font-mono text-slate-200">{meshInfo.x} × {meshInfo.y} × {meshInfo.z} <span className="opacity-40">mm</span></p>
           </div>
           <div className="space-y-1">
              <span className="text-[10px] font-bold text-slate-500 uppercase tracking-tight">Complexity</span>
              <p className="text-xs font-mono text-slate-200">{meshInfo.vertices.toLocaleString()} <span className="opacity-40">verts</span></p>
           </div>
        </div>
      )}

      <div className="absolute top-6 right-6 flex flex-col gap-2">
         <ControlButton icon={<Layers size={16} />} onClick={() => {
            if (meshRef.current) meshRef.current.material.wireframe = !meshRef.current.material.wireframe;
         }} />
         <ControlButton icon={<Maximize2 size={16} />} onClick={() => {}} />
      </div>
    </div>
  );
}

function ControlButton({ icon, onClick }) {
    return (
        <button
            onClick={onClick}
            className="w-10 h-10 rounded-xl bg-slate-900/80 backdrop-blur border border-slate-800 text-slate-400 hover:text-white hover:border-slate-700 transition-all flex items-center justify-center"
        >
            {icon}
        </button>
    )
}
