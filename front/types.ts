export type RootStackParamList = {
  Home: undefined;
  Map: { startPoint?: LatLng };
  RouteResult: { routes: Route[] };
};

export interface LatLng {
  latitude: number;
  longitude: number;
}

export interface Route {
  driver_id: number;
  points: RoutePoint[];
}

export interface RoutePoint {
  lat: number;
  lon: number;
  name: string;
  arrival_time: string;
}
