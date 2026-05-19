import React from 'react';

const ENTITIES = [
    { type: 'ball', label: 'Sphere', icon: '⚪' },
    { type: 'block', label: 'Cube', icon: '🟥' },
    { type: 'ramp', label: 'Incline', icon: '📐' },
    { type: 'gear', label: 'Gear', icon: '⚙️' },
    { type: 'lever', label: 'Lever', icon: '⚖️' },
    { type: 'spring', label: 'Spring', icon: '〰️' },
    { type: 'pendulum', label: 'Pendulum', icon: '⏱️' }
];

export const ToolboxPanel: React.FC = () => {
    
    const handleDragStart = (e: React.DragEvent<HTMLDivElement>, entityType: string) => {
        e.dataTransfer.setData('application/json', JSON.stringify({ entity_type: entityType }));
        e.dataTransfer.effectAllowed = 'copy';
    };

    return (
        <div style={{
            position: 'absolute',
            left: 20,
            top: 20,
            width: 240,
            backgroundColor: 'rgba(15, 23, 42, 0.8)',
            backdropFilter: 'blur(10px)',
            border: '1px solid #334155',
            borderRadius: 8,
            padding: 16,
            color: 'white',
            fontFamily: 'SF Pro Display, Inter, sans-serif',
            zIndex: 100,
            boxShadow: '0 10px 25px rgba(0,0,0,0.5)'
        }}>
            <h3 style={{ margin: '0 0 16px 0', fontSize: 16, color: '#00eeff' }}>Physics Asset Library</h3>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
                {ENTITIES.map(ent => (
                    <div 
                        key={ent.type}
                        draggable
                        onDragStart={(e) => handleDragStart(e, ent.type)}
                        style={{
                            backgroundColor: 'rgba(30, 41, 59, 0.6)',
                            border: '1px solid #475569',
                            borderRadius: 6,
                            padding: '12px 8px',
                            textAlign: 'center',
                            cursor: 'grab',
                            transition: 'all 0.2s ease',
                            userSelect: 'none'
                        }}
                        onMouseEnter={(e) => e.currentTarget.style.borderColor = '#00eeff'}
                        onMouseLeave={(e) => e.currentTarget.style.borderColor = '#475569'}
                    >
                        <div style={{ fontSize: 24, marginBottom: 4 }}>{ent.icon}</div>
                        <div style={{ fontSize: 11, color: '#94a3b8' }}>{ent.label}</div>
                    </div>
                ))}
            </div>
            <p style={{ fontSize: 11, color: '#64748b', marginTop: 16, textAlign: 'center' }}>
                Drag and drop into the canvas to spawn.
            </p>
        </div>
    );
};
