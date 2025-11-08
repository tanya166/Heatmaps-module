import React, { useState, useRef, useEffect } from 'react';
import { createZone, listCameras } from '../services/api';
import { Camera } from '../types';

interface ZoneDrawerProps {
  storeId: string;
  onZoneCreated: () => void;
}

const ZoneDrawer: React.FC<ZoneDrawerProps> = ({ storeId, onZoneCreated }) => {
  const [cameras, setCameras] = useState<Camera[]>([]);
  const [selectedCamera, setSelectedCamera] = useState<string>('');
  const [zoneName, setZoneName] = useState('');
  const [zoneType, setZoneType] = useState('shelf');
  const [threshold, setThreshold] = useState(5);
  const [polygon, setPolygon] = useState<number[][]>([]);
  const [drawing, setDrawing] = useState(false);
  const [error, setError] = useState('');
  const canvasRef = useRef<HTMLCanvasElement>(null);
  
  // Canvas dimensions
  const CANVAS_WIDTH = 640;
  const CANVAS_HEIGHT = 480;

  useEffect(() => {
    loadCameras();
  }, [storeId]);

  const loadCameras = async () => {
    try {
      const cams = await listCameras(storeId);
      setCameras(cams);
      if (cams.length > 0) {
        setSelectedCamera(cams[0]._id);
      }
    } catch (err) {
      console.error('Failed to load cameras', err);
    }
  };

  const handleCanvasClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!drawing) return;

    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    setPolygon([...polygon, [x, y]]);
  };

  const handleStartDrawing = () => {
    setDrawing(true);
    setPolygon([]);
  };

  const handleFinishDrawing = () => {
    if (polygon.length < 3) {
      setError('Please draw at least 3 points to form a zone');
      return;
    }
    setDrawing(false);
  };

  const handleSubmit = async () => {
    if (!selectedCamera || !zoneName || polygon.length < 3) {
      setError('Please complete all fields and draw a zone');
      return;
    }

    try {
      // Get the selected camera's video resolution
      const selectedCam = cameras.find(cam => cam._id === selectedCamera);
      
      if (!selectedCam) {
        setError('Selected camera not found');
        return;
      }

      // Get actual video dimensions (use resolution from camera metadata)
      const videoWidth = selectedCam.resolution_width || CANVAS_WIDTH;
      const videoHeight = selectedCam.resolution_height || CANVAS_HEIGHT;

      // Calculate scaling factors
      const scaleX = videoWidth / CANVAS_WIDTH;
      const scaleY = videoHeight / CANVAS_HEIGHT;

      // Scale polygon coordinates to match actual video resolution
      const scaledPolygon = polygon.map(([x, y]) => [
        Math.round(x * scaleX),
        Math.round(y * scaleY)
      ]);

      console.log('Original polygon:', polygon);
      console.log('Scaled polygon:', scaledPolygon);
      console.log(`Scaling: Canvas(${CANVAS_WIDTH}x${CANVAS_HEIGHT}) -> Video(${videoWidth}x${videoHeight})`);

      const zoneIdentifier = zoneName.toLowerCase().replace(/\s+/g, '_');
      
      await createZone(
        selectedCamera,
        zoneIdentifier,
        zoneName,
        scaledPolygon,  // Use scaled polygon instead of original
        zoneType,
        '#FF5733',
        threshold
      );
      
      setZoneName('');
      setPolygon([]);
      setError('');
      onZoneCreated();
      alert('Zone created successfully! Coordinates have been scaled to match video resolution.');
    } catch (err) {
      setError('Failed to create zone');
      console.error(err);
    }
  };

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Draw polygon
    if (polygon.length > 0) {
      ctx.beginPath();
      ctx.moveTo(polygon[0][0], polygon[0][1]);
      for (let i = 1; i < polygon.length; i++) {
        ctx.lineTo(polygon[i][0], polygon[i][1]);
      }
      if (!drawing) {
        ctx.closePath();
      }
      ctx.strokeStyle = '#FF5733';
      ctx.lineWidth = 2;
      ctx.stroke();
      ctx.fillStyle = 'rgba(255, 87, 51, 0.2)';
      ctx.fill();

      // Draw points
      polygon.forEach(([x, y]) => {
        ctx.beginPath();
        ctx.arc(x, y, 5, 0, 2 * Math.PI);
        ctx.fillStyle = '#FF5733';
        ctx.fill();
      });
    }
  }, [polygon, drawing]);

  // Get selected camera resolution info
  const getSelectedCameraInfo = () => {
    const selectedCam = cameras.find(cam => cam._id === selectedCamera);
    if (!selectedCam) return null;
    
    return {
      width: selectedCam.resolution_width || CANVAS_WIDTH,
      height: selectedCam.resolution_height || CANVAS_HEIGHT,
      fps: selectedCam.fps || 'Unknown'
    };
  };

  const cameraInfo = getSelectedCameraInfo();

  return (
    <div style={{ padding: '20px', maxWidth: '800px', margin: '20px auto' }}>
      <h3>Define Zones</h3>
      
      <div style={{ marginBottom: '15px' }}>
        <label style={{ display: 'block', marginBottom: '5px' }}>
          Select Camera
        </label>
        <select
          value={selectedCamera}
          onChange={(e) => {
            setSelectedCamera(e.target.value);
            setPolygon([]); // Clear polygon when changing camera
            setDrawing(false);
          }}
          style={{ width: '100%', padding: '8px', fontSize: '14px' }}
        >
          {cameras.map((cam) => (
            <option key={cam._id} value={cam._id}>
              {cam.name}
            </option>
          ))}
        </select>
        
        {/* Display camera resolution info */}
        {cameraInfo && (
          <div style={{ 
            marginTop: '5px', 
            padding: '8px', 
            backgroundColor: '#e3f2fd', 
            borderRadius: '4px',
            fontSize: '12px'
          }}>
            <strong>Camera Info:</strong> Resolution: {cameraInfo.width}x{cameraInfo.height}, 
            FPS: {cameraInfo.fps}
            {(cameraInfo.width !== CANVAS_WIDTH || cameraInfo.height !== CANVAS_HEIGHT) && (
              <div style={{ color: '#1976d2', marginTop: '4px' }}>
                ⚠️ Coordinates will be automatically scaled from canvas ({CANVAS_WIDTH}x{CANVAS_HEIGHT}) 
                to video resolution ({cameraInfo.width}x{cameraInfo.height})
              </div>
            )}
          </div>
        )}
      </div>

      <div style={{ marginBottom: '15px' }}>
        <label style={{ display: 'block', marginBottom: '5px' }}>
          Zone Name
        </label>
        <input
          type="text"
          value={zoneName}
          onChange={(e) => setZoneName(e.target.value)}
          placeholder="e.g., Electronics Shelf"
          style={{ width: '100%', padding: '8px', fontSize: '14px' }}
        />
      </div>

      <div style={{ marginBottom: '15px' }}>
        <label style={{ display: 'block', marginBottom: '5px' }}>
          Zone Type
        </label>
        <select
          value={zoneType}
          onChange={(e) => setZoneType(e.target.value)}
          style={{ width: '100%', padding: '8px', fontSize: '14px' }}
        >
          <option value="shelf">Shelf</option>
          <option value="counter">Counter</option>
          <option value="entrance">Entrance</option>
          <option value="aisle">Aisle</option>
        </select>
      </div>

      <div style={{ marginBottom: '15px' }}>
        <label style={{ display: 'block', marginBottom: '5px' }}>
          Minimum Dwell Time (seconds)
        </label>
        <input
          type="number"
          value={threshold}
          onChange={(e) => setThreshold(Number(e.target.value))}
          min="1"
          style={{ width: '100%', padding: '8px', fontSize: '14px' }}
        />
      </div>

      <div style={{ marginBottom: '15px' }}>
        <canvas
          ref={canvasRef}
          width={CANVAS_WIDTH}
          height={CANVAS_HEIGHT}
          onClick={handleCanvasClick}
          style={{
            border: '2px solid #ddd',
            cursor: drawing ? 'crosshair' : 'default',
            backgroundColor: '#f5f5f5',
            display: 'block',
          }}
        />
        <div style={{ fontSize: '12px', color: '#666', marginTop: '5px' }}>
          Drawing canvas: {CANVAS_WIDTH}x{CANVAS_HEIGHT} pixels
        </div>
      </div>

      <div style={{ marginBottom: '15px', display: 'flex', gap: '10px' }}>
        {!drawing ? (
          <button
            onClick={handleStartDrawing}
            style={{
              padding: '10px 20px',
              backgroundColor: '#007bff',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
            }}
          >
            Start Drawing Zone
          </button>
        ) : (
          <>
            <button
              onClick={handleFinishDrawing}
              style={{
                padding: '10px 20px',
                backgroundColor: '#28a745',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
              }}
            >
              Finish Drawing
            </button>
            <button
              onClick={() => {
                setPolygon([]);
                setDrawing(false);
              }}
              style={{
                padding: '10px 20px',
                backgroundColor: '#dc3545',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
              }}
            >
              Cancel
            </button>
          </>
        )}
      </div>

      {polygon.length >= 3 && !drawing && (
        <button
          onClick={handleSubmit}
          style={{
            padding: '10px 20px',
            backgroundColor: '#28a745',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
          }}
        >
          Save Zone ({polygon.length} points)
        </button>
      )}

      {error && (
        <div style={{ color: 'red', marginTop: '15px' }}>{error}</div>
      )}

      <div style={{ marginTop: '20px', fontSize: '14px', color: '#666' }}>
        <p><strong>Instructions:</strong></p>
        <ul>
          <li>Click "Start Drawing Zone" to begin</li>
          <li>Click on the canvas to add points (minimum 3 points)</li>
          <li>Points will form a polygon zone</li>
          <li>Click "Finish Drawing" when done</li>
          <li>Coordinates will be automatically scaled to match video resolution</li>
          <li>Click "Save Zone" to save</li>
        </ul>
      </div>
    </div>
  );
};

export default ZoneDrawer;