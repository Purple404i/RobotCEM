import React, { useEffect, useRef, useState } from 'react';
import './STLViewer3D.css';
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
    scene.background = new THREE.Color(0x0a0e1a);
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
    const gridHelper = new THREE.GridHelper(500, 50, 0x333344, 0x1a1a2e);
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
    <div className="stl-viewer">
      <div ref={mountRef} className="stl-canvas" />
      
      {loading && (
        <div className="stl-loading">
          <div className="loading-content">
            <div className="loading-spinner"></div>
            <p className="loading-text">Loading 3D Model...</p>
          </div>
        </div>
      )}

      {error && (
        <div className="stl-error">
          <div className="error-content">
            {error}
          </div>
        </div>
      )}

      {meshInfo && !loading && (
        <div className="stl-controls">
          <h3 className="controls-title">Model Info</h3>
          <div className="model-info">
            <div className="info-item">
              <span className="info-label">Vertices:</span>
              <span className="info-value">{meshInfo.vertices.toLocaleString()}</span>
            </div>
            <div className="info-item">
              <span className="info-label">Faces:</span>
              <span className="info-value">{meshInfo.faces.toLocaleString()}</span>
            </div>
            <div className="info-item">
              <span className="info-label">Size:</span>
              <span className="info-value">
                {meshInfo.dimensions.x} × {meshInfo.dimensions.y} × {meshInfo.dimensions.z} mm
              </span>
            </div>
            <div className="info-item">
              <span className="info-label">Volume:</span>
              <span className="info-value">{meshInfo.volume.toFixed(2)} cm³</span>
            </div>
          </div>
          
          <div className="controls-actions">
            <button onClick={toggleWireframe} className="control-btn">
              Toggle Wireframe
            </button>
            
            <div className="color-picker">
              <button onClick={() => changeColor(0x00d4ff)} className="color-btn color-cyan" title="Cyan"></button>
              <button onClick={() => changeColor(0xff6b6b)} className="color-btn color-red" title="Red"></button>
              <button onClick={() => changeColor(0x4ecdc4)} className="color-btn color-teal" title="Teal"></button>
              <button onClick={() => changeColor(0xffd93d)} className="color-btn color-yellow" title="Yellow"></button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}