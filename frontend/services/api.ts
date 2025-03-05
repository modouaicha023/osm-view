import axios from "axios";
import { RouteData } from "../types";

const API_URL = "http://192.168.253.184:8000";

export const fetchRoutes = async (): Promise<RouteData[]> => {
  try {
    const response = await axios.get(`${API_URL}/routes/1`);
    alert(response.data);
    return response.data;
  } catch (error) {
    console.error("Erreur lors de la récupération des trajets", error);
    return [];
  }
};
