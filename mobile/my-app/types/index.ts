export interface Point {
  id: number;
  name: string;
  lat: number;
  lon: number;
  passengers: number;
}

export interface Stop {
  name: string;
  coords: [number, number]; // [latitude, longitude]
  passengers?: number;
}

export interface Route {
  driver_id: number;
  load: number;
  distance: number;
  points: [number, number][]; // Array of [latitude, longitude] coordinates
  stops: Stop[];
}

export interface Region {
  latitude: number;
  longitude: number;
  latitudeDelta: number;
  longitudeDelta: number;
}

export interface OptimizationResponse {
  routes: Route[];
  total_distance: number;
  total_passengers: number;
}
