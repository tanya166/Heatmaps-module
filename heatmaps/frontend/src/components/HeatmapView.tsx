import React, { useState, useEffect } from 'react';
import { getDailyHeatmaps, getHourlyHeatmaps, listCameras } from '../services/api';
import { DailyHeatmap, HourlyHeatmap, Camera } from '../types';

interface HeatmapViewProps {
  storeId: string;
}

const HeatmapView: React.FC<HeatmapViewProps> = ({ storeId }) => {
  const [viewType, setViewType] = useState<'hourly' | 'daily'>('daily');
  const [dailyHeatmaps, setDailyHeatmaps] = useState<DailyHeatmap[]>([]);
  const [hourlyHeatmaps, setHourlyHeatmaps] = useState<HourlyHeatmap[]>([]);
  const [cameras, setCameras] = useState<Camera[]>([]);
  const [selectedCamera, setSelectedCamera] = useState<string>('all');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    loadData();
  }, [storeId, viewType]);

  const loadData = async () => {
    setLoading(true);
    setError('');

    try {
      const cams = await listCameras(storeId);
      setCameras(cams);

      if (viewType === 'daily') {
        const heatmaps = await getDailyHeatmaps(storeId);
        setDailyHeatmaps(heatmaps);
      } else {
        const heatmaps = await getHourlyHeatmaps(storeId);
        setHourlyHeatmaps(heatmaps);
      }
    } catch (err) {
      setError('Failed to load heatmaps. Please ensure videos have been processed.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const getColorIntensity = (density: number, maxDensity: number): string => {
    const intensity = maxDensity > 0 ? density / maxDensity : 0;
    
    if (intensity < 0.2) return '#3498db'; // Blue - Cold
    if (intensity < 0.4) return '#2ecc71'; // Green
    if (intensity < 0.6) return '#f39c12'; // Orange
    if (intensity < 0.8) return '#e74c3c'; // Red
    return '#c0392b'; // Dark Red - Hot
  };

  const filteredDailyHeatmaps = selectedCamera === 'all' 
    ? dailyHeatmaps 
    : dailyHeatmaps.filter(h => h.camera_id === selectedCamera);

  const filteredHourlyHeatmaps = selectedCamera === 'all'
    ? hourlyHeatmaps
    : hourlyHeatmaps.filter(h => h.camera_id === selectedCamera);

  const maxDensity = viewType === 'daily'
    ? Math.max(...filteredDailyHeatmaps.map(h => h.crowd_density), 1)
    : Math.max(...filteredHourlyHeatmaps.map(h => h.crowd_density), 1);

  if (loading) {
    return (
      <div style={{ padding: '20px', textAlign: 'center' }}>
        <p>Loading heatmaps...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ padding: '20px', textAlign: 'center', color: 'red' }}>
        <p>{error}</p>
      </div>
    );
  }

  return (
    <div style={{ padding: '20px' }}>
      <h2>Heatmap Visualization</h2>

      <div style={{ marginBottom: '20px', display: 'flex', gap: '20px', alignItems: 'center' }}>
        <div>
          <label style={{ marginRight: '10px' }}>View Type:</label>
          <select
            value={viewType}
            onChange={(e) => setViewType(e.target.value as 'hourly' | 'daily')}
            style={{ padding: '8px', fontSize: '14px' }}
          >
            <option value="daily">Daily Summary</option>
            <option value="hourly">Hourly Breakdown</option>
          </select>
        </div>

        <div>
          <label style={{ marginRight: '10px' }}>Camera:</label>
          <select
            value={selectedCamera}
            onChange={(e) => setSelectedCamera(e.target.value)}
            style={{ padding: '8px', fontSize: '14px' }}
          >
            <option value="all">All Cameras</option>
            {cameras.map((cam) => (
              <option key={cam._id} value={cam._id}>
                {cam.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      {viewType === 'daily' && (
        <div>
          <h3>Daily Heatmap Summary</h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '20px' }}>
            {filteredDailyHeatmaps.map((heatmap) => (
              <div
                key={heatmap._id}
                style={{
                  border: '1px solid #ddd',
                  borderRadius: '8px',
                  padding: '15px',
                  backgroundColor: getColorIntensity(heatmap.crowd_density, maxDensity),
                  color: heatmap.crowd_density / maxDensity > 0.5 ? 'white' : 'black',
                }}
              >
                <h4 style={{ marginTop: 0 }}>{heatmap.zone_name}</h4>
                <div style={{ fontSize: '14px' }}>
                  <p><strong>Total Visits:</strong> {heatmap.total_visits}</p>
                  <p><strong>Unique Visitors:</strong> {heatmap.unique_visitors}</p>
                  <p><strong>Avg Dwell Time:</strong> {heatmap.avg_dwell_time.toFixed(1)}s</p>
                  <p><strong>Crowd Density:</strong> {heatmap.crowd_density.toFixed(2)} visits/hour</p>
                  <p><strong>Engagement Rate:</strong> {heatmap.engagement_rate.toFixed(1)}%</p>
                  <p><strong>Peak Hour:</strong> {heatmap.peak_hour}:00</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {viewType === 'hourly' && (
        <div>
          <h3>Hourly Heatmap Breakdown</h3>
          {Array.from(new Set(filteredHourlyHeatmaps.map(h => h.zone_name))).map((zoneName) => {
            const zoneHeatmaps = filteredHourlyHeatmaps.filter(h => h.zone_name === zoneName);
            
            return (
              <div key={zoneName} style={{ marginBottom: '30px' }}>
                <h4>{zoneName}</h4>
                <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
                  {zoneHeatmaps.map((heatmap) => {
                    const hour = new Date(heatmap.hour_start).getHours();
                    return (
                      <div
                        key={heatmap._id}
                        style={{
                          width: '120px',
                          padding: '10px',
                          border: '1px solid #ddd',
                          borderRadius: '4px',
                          backgroundColor: getColorIntensity(heatmap.crowd_density, maxDensity),
                          color: heatmap.crowd_density / maxDensity > 0.5 ? 'white' : 'black',
                          textAlign: 'center',
                        }}
                      >
                        <div style={{ fontWeight: 'bold', marginBottom: '5px' }}>
                          {hour}:00 - {hour + 1}:00
                        </div>
                        <div style={{ fontSize: '12px' }}>
                          <div>{heatmap.visit_count} visits</div>
                          <div>{heatmap.avg_dwell_time.toFixed(1)}s avg</div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </div>
      )}

      <div style={{ marginTop: '30px', padding: '15px', backgroundColor: '#f8f9fa', borderRadius: '8px' }}>
        <h4>Color Legend</h4>
        <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
            <div style={{ width: '30px', height: '30px', backgroundColor: '#3498db' }} />
            <span>Low Traffic</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
            <div style={{ width: '30px', height: '30px', backgroundColor: '#2ecc71' }} />
            <span>Medium-Low</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
            <div style={{ width: '30px', height: '30px', backgroundColor: '#f39c12' }} />
            <span>Medium</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
            <div style={{ width: '30px', height: '30px', backgroundColor: '#e74c3c' }} />
            <span>High</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
            <div style={{ width: '30px', height: '30px', backgroundColor: '#c0392b' }} />
            <span>Very High</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default HeatmapView;