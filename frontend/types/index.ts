export interface RoutePoint {
  lat: number;
  lon: number;
  name: string;
  passengers: number;
}

export interface RouteData {
  id: number;
  driver_id: number;
  stop_number: number;
  lat: number;
  lon: number;
  passengers: number;
}
