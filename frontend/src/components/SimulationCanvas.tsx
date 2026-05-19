import React, { useEffect, useRef, useState } from 'react';
import { EngineCore } from '../physics/EngineCore';
import { DOMBinder } from '../physics/DOMBinder';
import { InteractionManager } from '../physics/InteractionManager';
import { ToolboxPanel } from './ToolboxPanel';

export const SimulationCanvas: React.FC = () => {
    const containerRef = useRef<HTMLDivElement>(null);
    const svgRef = useRef<SVGSVGElement>(null);

    // References to engine subsystems
    const engineCore = useRef<EngineCore | null>(null);
    const domBinder = useRef<DOMBinder | null>(null);
    const interactionManager = useRef<InteractionManager | null>(null);

    // State for the Scene Graph and currently compiled SVG
    const [sceneGraph, setSceneGraph] = useState<any>({
        scene_id: "interactive_canvas_01",
        title: "Sandbox",
        gravity: [0.0, 1.0],
        entities: [
            {
                id: "ent_floor_1",
                entity_type: "block",
                material: "steel",
                transform: { x: 960, y: 1000, rotation: 0, scale_x: 1, scale_y: 1 },
                physics: { is_static: true }
            }
        ],
        joints: []
    });
    
    const [svgContent, setSvgContent] = useState<string>('');
    const [manifest, setManifest] = useState<any>(null);
    const [isCompiling, setIsCompiling] = useState(false);

    // Initialize Physics Engine once
    useEffect(() => {
        engineCore.current = new EngineCore();
        domBinder.current = new DOMBinder(engineCore.current);
        interactionManager.current = new InteractionManager(engineCore.current);

        engineCore.current.start();

        if (containerRef.current) {
            interactionManager.current.attach(containerRef.current);
        }

        return () => {
            interactionManager.current?.detach();
            domBinder.current?.unmount();
            engineCore.current?.stop();
        };
    }, []);

    // Sync SceneGraph to Backend Compiler whenever it changes
    useEffect(() => {
        const compileScene = async () => {
            setIsCompiling(true);
            try {
                // In a real app, this points to your FastAPI backend port
                const res = await fetch('http://127.0.0.1:8000/api/svg/compile', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(sceneGraph)
                });
                
                if (!res.ok) throw new Error('Compilation failed');
                
                const data = await res.json();
                setSvgContent(data.svg_content);
                setManifest(data.physics_manifest);
            } catch (err) {
                console.error(err);
            } finally {
                setIsCompiling(false);
            }
        };

        compileScene();
    }, [sceneGraph]);

    // Bind Matter.js when we receive a new SVG + Manifest
    useEffect(() => {
        if (svgContent && manifest && svgRef.current && domBinder.current) {
            // Give React a tick to update the dangerouslySetInnerHTML
            setTimeout(() => {
                if (svgRef.current) {
                    domBinder.current!.bindScene(svgRef.current, manifest);
                }
            }, 50);
        }
    }, [svgContent, manifest]);


    // Handle Drop Events
    const handleDragOver = (e: React.DragEvent) => {
        e.preventDefault();
        e.dataTransfer.dropEffect = 'copy';
    };

    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault();
        
        try {
            const data = JSON.parse(e.dataTransfer.getData('application/json'));
            if (!data.entity_type) return;

            // Calculate SVG coordinates based on viewport scaling
            const rect = containerRef.current!.getBoundingClientRect();
            
            // Map screen coords to 1920x1080 viewBox
            const scaleX = 1920 / rect.width;
            const scaleY = 1080 / rect.height;
            
            const dropX = (e.clientX - rect.left) * scaleX;
            const dropY = (e.clientY - rect.top) * scaleY;

            const newEntityId = `ent_${data.entity_type}_${Date.now()}`;
            
            const newEntity = {
                id: newEntityId,
                entity_type: data.entity_type,
                material: "steel",
                transform: { x: dropX, y: dropY, rotation: 0, scale_x: 1, scale_y: 1 },
                physics: { is_static: false }
            };

            setSceneGraph((prev: any) => ({
                ...prev,
                entities: [...prev.entities, newEntity]
            }));

        } catch (err) {
            console.error("Drop failed:", err);
        }
    };

    const handleSave = async () => {
        try {
            const res = await fetch('http://127.0.0.1:8000/api/svg/save', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(sceneGraph)
            });
            const data = await res.json();
            if (data.success) {
                alert(`Saved as ${data.filename} in the backend svgs/ folder!`);
            } else {
                alert('Save failed.');
            }
        } catch (err) {
            console.error("Failed to save:", err);
            alert("Error saving scene.");
        }
    };

    return (
        <div 
            ref={containerRef} 
            style={{ width: '100%', height: '100%', position: 'relative' }}
            onDragOver={handleDragOver}
            onDrop={handleDrop}
        >
            <ToolboxPanel />
            
            {/* Save Button */}
            <button 
                onClick={handleSave}
                style={{
                    position: 'absolute',
                    top: 20,
                    right: 20,
                    padding: '10px 20px',
                    backgroundColor: '#00eeff',
                    color: '#0f172a',
                    border: 'none',
                    borderRadius: 8,
                    fontWeight: 'bold',
                    cursor: 'pointer',
                    zIndex: 100,
                    boxShadow: '0 0 10px rgba(0,238,255,0.5)'
                }}
            >
                💾 Save Scene
            </button>

            {/* The compiled SVG is dynamically injected here */}
            {svgContent ? (
                <svg 
                    ref={svgRef}
                    xmlns="http://www.w3.org/2000/svg" 
                    width="100%" height="100%" 
                    viewBox="0 0 1920 1080"
                    preserveAspectRatio="xMidYMid slice"
                    style={{ backgroundColor: '#05080f' }}
                    dangerouslySetInnerHTML={{
                        // Extract inner tags from the compiled <svg> string
                        __html: svgContent.replace(/<svg[^>]*>|<\/svg>/g, '')
                    }}
                />
            ) : (
                <div style={{ width: '100%', height: '100%', backgroundColor: '#05080f' }} />
            )}

            {isCompiling && (
                <div style={{ position: 'absolute', bottom: 20, right: 20, color: '#00eeff', fontFamily: 'monospace' }}>
                    Compiling Scene...
                </div>
            )}
        </div>
    );
};

export default SimulationCanvas;
