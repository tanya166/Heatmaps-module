import axios from 'axios';
import { 
  Store, Camera, Zone, HourlyHeatmap, DailyHeatmap, 
  DailyInsights, ProcessingStatus 
} from '../types';

const API_BASE_URL = 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
});

// Store APIs
export const createStore = async (name: string, location?: string): Promise<{ id: string }> => {
  const formData = new FormData();
  formData.append('name', name);
  if (location) formData.append('location', location);
  
  const response = await api.post('/stores', formData);
  return response.data;
};

export const listStores = async (): Promise<Store[]> => {
  const response = await api.get('/stores');
  return response.data.stores;
};

export const getStore = async (storeId: string): Promise<Store> => {
  const response = await api.get(`/stores/${storeId}`);
  return response.data;
};

// Camera APIs
export const uploadCameraVideo = async (
  storeId: string,
  cameraIdentifier: string,
  name: string,
  videoFile: File
): Promise<{ id: string }> => {
  const formData = new FormData();
  formData.append('camera_identifier', cameraIdentifier);
  formData.append('name', name);
  formData.append('video', videoFile);
  
  const response = await api.post(`/stores/${storeId}/cameras`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

export const listCameras = async (storeId: string): Promise<Camera[]> => {
  const response = await api.get(`/stores/${storeId}/cameras`);
  return response.data.cameras;
};

// Zone APIs
export const createZone = async (
  cameraId: string,
  zoneIdentifier: string,
  name: string,
  polygon: number[][],
  zoneType: string,
  color: string = '#FF5733',
  minimumDwellThreshold: number = 5
): Promise<{ id: string }> => {
  const formData = new FormData();
  formData.append('zone_identifier', zoneIdentifier);
  formData.append('name', name);
  formData.append('polygon', JSON.stringify(polygon));
  formData.append('zone_type', zoneType);
  formData.append('color', color);
  formData.append('minimum_dwell_threshold', minimumDwellThreshold.toString());
  
  const response = await api.post(`/cameras/${cameraId}/zones`, formData);
  return response.data;
};

export const listZones = async (cameraId: string): Promise<Zone[]> => {
  const response = await api.get(`/cameras/${cameraId}/zones`);
  return response.data.zones;
};

export const deleteZone = async (zoneId: string): Promise<void> => {
  await api.delete(`/zones/${zoneId}`);
};

// Processing APIs
export const startProcessing = async (storeId: string): Promise<void> => {
  await api.post(`/stores/${storeId}/process`);
};

export const getProcessingStatus = async (storeId: string): Promise<ProcessingStatus> => {
  const response = await api.get(`/stores/${storeId}/processing-status`);
  return response.data;
};

// Heatmap APIs
export const getHourlyHeatmaps = async (storeId: string): Promise<HourlyHeatmap[]> => {
  const response = await api.get(`/stores/${storeId}/heatmaps/hourly`);
  return response.data.heatmaps;
};

export const getDailyHeatmaps = async (storeId: string): Promise<DailyHeatmap[]> => {
  const response = await api.get(`/stores/${storeId}/heatmaps/daily`);
  return response.data.heatmaps;
};

// Insights APIs
export const getDailyInsights = async (storeId: string): Promise<DailyInsights[]> => {
  const response = await api.get(`/stores/${storeId}/insights`);
  return response.data.insights;
};