import React, { useState, useEffect, useCallback } from 'react';
import { getProcessingStatus, startProcessing } from '../services/api';
import { ProcessingStatus as Status } from '../types';

interface ProcessingStatusProps {
  storeId: string;
  onProcessingComplete: () => void;
}

const ProcessingStatus: React.FC<ProcessingStatusProps> = ({ storeId, onProcessingComplete }) => {
  const [status, setStatus] = useState<Status | null>(null);
  const [polling, setPolling] = useState(false);

  const checkStatus = useCallback(async () => {
    try {
      const currentStatus = await getProcessingStatus(storeId);
      setStatus(currentStatus);

      if (currentStatus.status === 'processing') {
        setPolling(true);
      } else if (currentStatus.status === 'completed') {
        setPolling(false);
        onProcessingComplete();
      } else if (currentStatus.status === 'error') {
        setPolling(false);
      }
    } catch (err) {
      console.error('Failed to get processing status', err);
    }
  }, [storeId, onProcessingComplete]);

  useEffect(() => {
    checkStatus();
  }, [checkStatus]);

  useEffect(() => {
    if (!polling) return;

    const interval = setInterval(() => {
      checkStatus();
    }, 2000);

    return () => clearInterval(interval);
  }, [polling, checkStatus]);

  const handleStartProcessing = async () => {
    try {
      await startProcessing(storeId);
      setPolling(true);
    } catch (err) {
      alert('Failed to start processing');
      console.error(err);
    }
  };

  if (!status || status.status === 'not_started') {
    return (
      <div style={{ padding: '20px', textAlign: 'center' }}>
        <h3>Ready to Process Videos</h3>
        <p>Click the button below to start processing all uploaded videos and generate heatmaps.</p>
        <button
          onClick={handleStartProcessing}
          style={{
            padding: '15px 30px',
            fontSize: '18px',
            backgroundColor: '#007bff',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
            marginTop: '20px',
          }}
        >
          Start Processing
        </button>
      </div>
    );
  }

  if (status.status === 'processing') {
    return (
      <div style={{ padding: '20px' }}>
        <h3>Processing Videos...</h3>
        <p>{status.message}</p>
        {status.progress && (
          <div style={{ marginTop: '20px' }}>
            {Object.entries(status.progress).map(([cameraId, data]) => (
              <div key={cameraId} style={{ marginBottom: '15px' }}>
                <div style={{ marginBottom: '5px' }}>
                  <strong>{data.name}</strong>: {data.progress.toFixed(1)}%
                </div>
                <div style={{ width: '100%', backgroundColor: '#e0e0e0', borderRadius: '4px', height: '20px' }}>
                  <div
                    style={{
                      width: `${data.progress}%`,
                      backgroundColor: '#007bff',
                      height: '100%',
                      borderRadius: '4px',
                      transition: 'width 0.3s ease',
                    }}
                  />
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  }

  if (status.status === 'completed') {
    return (
      <div style={{ padding: '20px', textAlign: 'center', backgroundColor: '#d4edda', borderRadius: '8px' }}>
        <h3 style={{ color: '#155724' }}>✅ Processing Complete!</h3>
        <p>{status.message}</p>
        {status.result && (
          <div style={{ marginTop: '20px', textAlign: 'left', display: 'inline-block' }}>
            <p><strong>Results:</strong></p>
            <ul>
              <li>Hourly Heatmaps Generated: {status.result.hourly_heatmaps}</li>
              <li>Daily Heatmaps Generated: {status.result.daily_heatmaps}</li>
              <li>Insights Generated: {status.result.insights_generated}</li>
            </ul>
          </div>
        )}
      </div>
    );
  }

  if (status.status === 'error') {
    return (
      <div style={{ padding: '20px', textAlign: 'center', backgroundColor: '#f8d7da', borderRadius: '8px' }}>
        <h3 style={{ color: '#721c24' }}>❌ Processing Failed</h3>
        <p>{status.message}</p>
        <button
          onClick={handleStartProcessing}
          style={{
            padding: '10px 20px',
            fontSize: '16px',
            backgroundColor: '#dc3545',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
            marginTop: '20px',
          }}
        >
          Retry Processing
        </button>
      </div>
    );
  }

  return null;
};

export default ProcessingStatus;