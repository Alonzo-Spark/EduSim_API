import Matter from 'matter-js';

export class EngineCore {
    public engine: Matter.Engine;
    public render: Matter.Render | null = null;
    public runner: Matter.Runner;

    constructor() {
        this.engine = Matter.Engine.create();
        this.runner = Matter.Runner.create();
        
        // Default gravity (can be updated via SceneGraph)
        this.engine.gravity.y = 1;
        this.engine.gravity.x = 0;
    }

    start() {
        Matter.Runner.run(this.runner, this.engine);
    }

    stop() {
        Matter.Runner.stop(this.runner);
    }

    clear() {
        Matter.World.clear(this.engine.world, false);
        Matter.Engine.clear(this.engine);
    }
}
