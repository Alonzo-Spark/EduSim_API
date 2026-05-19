import Matter from 'matter-js';
import { EngineCore } from './EngineCore';

export class DOMBinder {
    private engineCore: EngineCore;
    private bindings: Map<string, { body: Matter.Body, svgElement: SVGGElement }> = new Map();
    private updateLoopId: number | null = null;

    constructor(engineCore: EngineCore) {
        this.engineCore = engineCore;
    }

    public bindScene(svgRoot: SVGSVGElement, manifest: any) {
        // Clear previous bindings
        this.bindings.clear();
        this.engineCore.clear();

        // Apply global gravity from manifest
        if (manifest.gravity) {
            this.engineCore.engine.gravity.x = manifest.gravity.x;
            this.engineCore.engine.gravity.y = manifest.gravity.y;
        }

        const physicsNodes = svgRoot.querySelectorAll<SVGGElement>('g[id^="phys_"]');
        
        physicsNodes.forEach((node) => {
            const id = node.id.replace('phys_', ''); // extract the entity id
            const entityData = manifest.bodies[id];

            if (!entityData) {
                console.warn(`No physics manifest data found for ${id}`);
                return;
            }

            const { type, x, y, isStatic, mass, friction, restitution, geometry } = entityData;
            
            let body: Matter.Body;
            if (['ball', 'wheel', 'pulley', 'gear', 'blob'].includes(type)) {
                body = Matter.Bodies.circle(x, y, geometry.radius || 50, {
                    isStatic,
                    friction,
                    restitution,
                    mass
                });
            } else {
                const w = geometry.width || 100;
                const h = geometry.height || 100;
                body = Matter.Bodies.rectangle(x, y, w, h, {
                    isStatic,
                    friction,
                    restitution,
                    mass
                });
            }

            Matter.World.add(this.engineCore.engine.world, body);
            this.bindings.set(id, { body, svgElement: node });
        });

        this.startSyncLoop();
    }

    private startSyncLoop() {
        if (this.updateLoopId !== null) cancelAnimationFrame(this.updateLoopId);

        const sync = () => {
            this.bindings.forEach(({ body, svgElement }) => {
                if (!body.isStatic) {
                    // Calculate translation from original center
                    const bbox = svgElement.getBBox();
                    const origCx = bbox.x + bbox.width / 2;
                    const origCy = bbox.y + bbox.height / 2;
                    
                    const dx = body.position.x - origCx;
                    const dy = body.position.y - origCy;
                    const angle = body.angle * (180 / Math.PI); // Rad to Deg

                    // We apply the transform relative to the parent's starting transform or via transform-origin
                    svgElement.setAttribute(
                        'transform',
                        `translate(${dx}, ${dy}) rotate(${angle}, ${origCx}, ${origCy})`
                    );
                }
            });
            this.updateLoopId = requestAnimationFrame(sync);
        };
        sync();
    }

    public unmount() {
        if (this.updateLoopId !== null) cancelAnimationFrame(this.updateLoopId);
        this.bindings.clear();
        this.engineCore.clear();
    }
}
