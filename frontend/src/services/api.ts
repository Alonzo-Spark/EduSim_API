import axios from 'axios';

// Get backend API URL from env or fallback to localhost:8000
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export interface SVGGenerateResponse {
  success: boolean;
  prompt: string;
  svg_code: string;
  file_path: string;
  filename: string;
  message?: string;
}

export interface SVGHistoryItem {
  filename: string;
  prompt: string;
  file_path: string;
  created_at: string;
}

// -------------------------------------------------------------
// Interactive Physics Simulation DSL Types
// -------------------------------------------------------------

export interface Vector2D {
  x: number;
  y: number;
}

export interface SimulationObject {
  id: string;
  category: string;
  bodyType: 'dynamic' | 'static' | 'kinematic';
  shape: {
    type: 'circle' | 'rectangle' | 'ramp' | 'polygon';
    radius?: number;
    width?: number;
    height?: number;
  };
  position: Vector2D;
  velocity?: Vector2D;
  physics: {
    mass: number;
    density?: number;
    affectedByGravity?: boolean;
    fixedRotation?: boolean;
    isSensor?: boolean;
  };
  material: {
    friction: number;
    restitution: number;
  };
  visual: {
    color: string;
    label?: string;
    showLabel?: boolean;
    showVelocityVector?: boolean;
    showTrail?: boolean;
    asset?: {
      enabled: boolean;
      assetId: string;
      scale?: number;
      rotationSync?: boolean;
    };
  };
}

export interface ControlParameter {
  id: string;
  type: 'slider' | 'toggle';
  label: string;
  symbol?: string;
  bind: string; // e.g. "environment.gravity.y" or "objects[0].physics.mass"
  min?: number;
  max?: number;
  step?: number;
}

export interface ControlAction {
  id: string;
  type: 'button';
  label: string;
  action: 'startSimulation' | 'togglePause' | 'resetSimulation';
}

export interface Controls {
  parameters: ControlParameter[];
  actions: ControlAction[];
}

export interface Observable {
  id: string;
  label: string;
  source: string; // e.g. "objects[0].velocity.magnitude"
  precision: number;
  unit?: string;
}

export interface FormulaVariable {
  path: string;
  role: 'independent' | 'dependent';
}

export interface FormulaBinding {
  id: string;
  formula: string;
  variables: Record<string, FormulaVariable>;
}

export interface SimulationDSL {
  meta: {
    id: string;
    title: string;
    topic: string;
    simulationType: string;
    difficulty: string;
  };
  environment: {
    gravity: Vector2D;
    airResistance: number;
    background?: { color: string };
  };
  objects: SimulationObject[];
  formulaBindings: FormulaBinding[];
  controls: Controls;
  observables: Observable[];
}

export interface EduSimResponse {
  success: boolean;
  id?: string;
  dsl: SimulationDSL;
  knowledge?: {
    relevant_formulas: string[];
    related_concepts: string[];
    learningObjectives?: string[];
  };
}

export const generateSVG = async (prompt: string): Promise<SVGGenerateResponse> => {
  // We can try to hit the router prefix `/api/svg/generate-svg` or the direct root `/generate-svg`
  try {
    const response = await axios.post<SVGGenerateResponse>(`${API_BASE_URL}/api/svg/generate-svg`, {
      prompt
    });
    return response.data;
  } catch (error) {
    // If router prefix isn't loaded, fallback to root endpoint
    console.warn("API router prefix generation failed, attempting root fallback:", error);
    const response = await axios.post<SVGGenerateResponse>(`${API_BASE_URL}/generate-svg`, {
      prompt
    });
    return response.data;
  }
};

export const generateSimulationDSL = async (prompt: string): Promise<EduSimResponse> => {
  const response = await axios.post<EduSimResponse>(`${API_BASE_URL}/api/simulations/synthesis/generate`, {
    prompt
  });
  return response.data;
};

export const getSVGHistory = async (): Promise<SVGHistoryItem[]> => {
  const response = await axios.get<SVGHistoryItem[]>(`${API_BASE_URL}/api/svg/history`);
  return response.data;
};

export const getFullSvgUrl = (path: string): string => {
  if (path.startsWith('http')) return path;
  return `${API_BASE_URL}${path}`;
};

