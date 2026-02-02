import React, { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls';
import { STLLoader } from 'three/examples/jsm/loaders/STLLoader';

export default function STLViewer3D({ stlUrl, onAnalysis }) {
  const mountRef = useRef(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [meshInfo, setMeshInfo] = useState(null);
  const sceneRef = useRef(null);
  const rendererRef = useRef(null);
  const meshRef = useRef(null);

  useEffect(() => {
    if (!stlUrl) return;

    // Scene setup
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x1a1a2e);
    sceneRef.current = scene;

    // Camera
    const camera = new THREE.PerspectiveCamera(
      60,
      mountRef.current.clientWidth / mountRef.current.clientHeight,
      0.1,
      10000
    );

    // Renderer
    const renderer = new THREE.WebGLRenderer({
      antialias: true,
      alpha: true
    });
    renderer.setSize(mountRef.current.clientWidth, mountRef.current.clientHeight);
    renderer.setPixelRatio(window.devicePixelRatio);
    renderer.shadowMap.enabled = true;
    mountRef.current.appendChild(renderer.domElement);
    rendererRef.current = renderer;

    // Controls
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    controls.screenSpacePanning = false;
    controls.minDistance = 10;
    controls.maxDistance = 1000;

    // Lighting
    const ambientLight = new THREE.AmbientLight(0x404040, 1.5);
    scene.add(ambientLight);

    const directionalLight1 = new THREE.DirectionalLight(0xffffff, 0.8);
    directionalLight1.position.set(100, 100, 100);
    directionalLight1.castShadow = true;
    scene.add(directionalLight1);

    const directionalLight2 = new THREE.DirectionalLight(0xffffff, 0.4);
    directionalLight2.position.set(-100, 50, -100);
    scene.add(directionalLight2);

    const directionalLight3 = new THREE.DirectionalLight(0xffffff, 0.2);
    directionalLight3.position.set(0, -100, 0);
    scene.add(directionalLight3);

    // Grid
    const gridHelper = new THREE.GridHelper(500, 50, 0x444444, 0x222222);
    scene.add(gridHelper);

    // Load STL
    const loader = new STLLoader();
    setLoading(true);
    setError(null);

    loader.load(
      stlUrl,
      (geometry) => {
        // Center geometry
        geometry.computeBoundingBox();
        geometry.computeVertexNormals();
        
        const center = new THREE.Vector3();
        geometry.boundingBox.getCenter(center);
        geometry.translate(-center.x, -center.y, -center.z);

        // Material with better visual properties
        const material = new THREE.MeshStandardMaterial({
          color: 0x00d4ff,
          roughness: 0.3,
          metalness: 0.5,
          flatShading: false
        });

        const mesh = new THREE.Mesh(geometry, material);
        mesh.castShadow = true;
        mesh.receiveShadow = true;
        scene.add(mesh);
        meshRef.current = mesh;

        // Calculate mesh info
        const bbox = geometry.boundingBox;
        const size = new THREE.Vector3();
        bbox.getSize(size);

        const info = {
          vertices: geometry.attributes.position.count,
          faces: geometry.attributes.position.count / 3,
          dimensions: {
            x: size.x.toFixed(2),
            y: size.y.toFixed(2),
            z: size.z.toFixed(2)
          },
          volume: calculateVolume(geometry)
        };

        setMeshInfo(info);
        if (onAnalysis) onAnalysis(info);

        // Position camera
        const maxDim = Math.max(size.x, size.y, size.z);
        camera.position.set(maxDim * 1.5, maxDim * 1.2, maxDim * 1.5);
        camera.lookAt(0, 0, 0);
        controls.target.set(0, 0, 0);

        setLoading(false);
      },
      (progress) => {
        console.log((progress.loaded / progress.total * 100) + '% loaded');
      },
      (error) => {
        console.error('Error loading STL:', error);
        setError('Failed to load 3D model');
        setLoading(false);
      }
    );

    // Animation loop
    function animate() {
      requestAnimationFrame(animate);
      controls.update();
      renderer.render(scene, camera);
    }
    animate();

    // Handle window resize
    const handleResize = () => {
      if (!mountRef.current) return;
      
      const width = mountRef.current.clientWidth;
      const height = mountRef.current.clientHeight;
      
      camera.aspect = width / height;
      camera.updateProjectionMatrix();
      renderer.setSize(width, height);
    };
    window.addEventListener('resize', handleResize);

    // Cleanup
    return () => {
      window.removeEventListener('resize', handleResize);
      if (mountRef.current && renderer.domElement) {
        mountRef.current.removeChild(renderer.domElement);
      }
      renderer.dispose();
      controls.dispose();
    };
  }, [stlUrl]);

  function calculateVolume(geometry) {
    // Simplified volume calculation using tetrahedron method
    const positions = geometry.attributes.position.array;
    let volume = 0;

    for (let i = 0; i < positions.length; i += 9) {
      const p1 = new THREE.Vector3(positions[i], positions[i + 1], positions[i + 2]);
      const p2 = new THREE.Vector3(positions[i + 3], positions[i + 4], positions[i + 5]);
      const p3 = new THREE.Vector3(positions[i + 6], positions[i + 7], positions[i + 8]);

      volume += p1.dot(p2.cross(p3)) / 6;
    }

    return Math.abs(volume) / 1000; // Convert mm³ to cm³
  }

  const toggleWireframe = () => {
    if (meshRef.current) {
      meshRef.current.material.wireframe = !meshRef.current.material.wireframe;
    }
  };

  const changeColor = (color) => {
    if (meshRef.current) {
      meshRef.current.material.color.setHex(color);
    }
  };

  return (
    <div className="relative w-full h-full">
      <div ref={mountRef} className="w-full h-full" />
      
      {loading && (
        <div className="absolute inset-0 flex items-center justify-center bg-gray-900 bg-opacity-75">
          <div className="text-center">
            <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-500 mx-auto mb-4"></div>
            <p className="text-white">Loading 3D Model...</p>
          </div>
        </div>
      )}

      {error && (
        <div className="absolute inset-0 flex items-center justify-center bg-gray-900 bg-opacity-75">
          <div className="bg-red-500 text-white p-4 rounded">
            {error}
          </div>
        </div>
      )}

      {meshInfo && !loading && (
        <div className="absolute top-4 right-4 bg-gray-800 bg-opacity-90 text-white p-4 rounded shadow-lg">
          <h3 className="font-bold mb-2">Model Info</h3>
          <div className="text-sm space-y-1">
            <p>Vertices: {meshInfo.vertices.toLocaleString()}</p>
            <p>Faces: {meshInfo.faces.toLocaleString()}</p>
            <p>Size: {meshInfo.dimensions.x} × {meshInfo.dimensions.y} × {meshInfo.dimensions.z} mm</p>
            <p>Volume: {meshInfo.volume.toFixed(2)} cm³</p>
          </div>
          
          <div className="mt-4 space-y-2">
            <button
              onClick={toggleWireframe}
              className="w-full px-3 py-1 bg-blue-600 hover:bg-blue-700 rounded text-sm"
            >
              Toggle Wireframe
            </button>
            
            <div className="flex gap-2">
              <button onClick={() => changeColor(0x00d4ff)} className="flex-1 h-6 bg-cyan-400 rounded"></button>
              <button onClick={() => changeColor(0xff6b6b)} className="flex-1 h-6 bg-red-400 rounded"></button>
              <button onClick={() => changeColor(0x4ecdc4)} className="flex-1 h-6 bg-teal-400 rounded"></button>
              <button onClick={() => changeColor(0xffd93d)} className="flex-1 h-6 bg-yellow-400 rounded"></button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}