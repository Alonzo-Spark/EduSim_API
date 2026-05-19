import Matter from 'matter-js';
import { EngineCore } from './EngineCore';

export class InteractionManager {
    private engineCore: EngineCore;
    private mouseConstraint: Matter.MouseConstraint | null = null;

    constructor(engineCore: EngineCore) {
        this.engineCore = engineCore;
    }

    public attach(canvasElement: HTMLElement) {
        // Matter.js needs a mouse object tied to the rendering surface
        const mouse = Matter.Mouse.create(canvasElement);
        
        this.mouseConstraint = Matter.MouseConstraint.create(this.engineCore.engine, {
            mouse: mouse,
            constraint: {
                stiffness: 0.2,
                render: {
                    visible: false
                }
            }
        });

        Matter.World.add(this.engineCore.engine.world, this.mouseConstraint);
    }

    public detach() {
        if (this.mouseConstraint) {
            Matter.World.remove(this.engineCore.engine.world, this.mouseConstraint);
            this.mouseConstraint = null;
        }
    }
}
