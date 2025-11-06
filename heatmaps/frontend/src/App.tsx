import React, { useState } from 'react';
import StoreSetup from './components/StoreSetup';
import VideoUpload from './components/VideoUpload';
import ZoneDrawer from './components/ZoneDrawer';
import ProcessingStatus from './components/ProcessingStatus';
import HeatmapView from './components/HeatmapView';
import InsightsDashboard from './components/InsightsDashboard';

type Step = 'setup' | 'upload' | 'zones' | 'process' | 'results';

function App() {
  const [currentStep, setCurrentStep] = useState<Step>('setup');
  const [storeId, setStoreId] = useState<string>('');

  const handleStoreCreated = (id: string) => {
    setStoreId(id);
    setCurrentStep('upload');
  };

  const handleUploadComplete = () => {
    // Stay on upload page, user can upload multiple videos
  };

  const handleZoneCreated = () => {
    // Stay on zone page, user can create multiple zones
  };

  const handleProcessingComplete = () => {
    setCurrentStep('results');
  };

  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#f5f5f5' }}>
      {/* Header */}
      <div style={{ backgroundColor: '#2c3e50', color: 'white', padding: '20px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}>
        <h1 style={{ margin: 0 }}>🏪 Retail Heatmap System</h1>
        <p style={{ margin: '5px 0 0 0', opacity: 0.8 }}>Analyze customer behavior with AI-powered insights</p>
      </div>

      {/* Navigation Steps */}
      {storeId && (
        <div style={{ backgroundColor: 'white', padding: '15px 20px', borderBottom: '1px solid #ddd' }}>
          <div style={{ display: 'flex', gap: '10px' }}>
            <button
              onClick={() => setCurrentStep('upload')}
              style={{
                padding: '8px 16px',
                backgroundColor: currentStep === 'upload' ? '#007bff' : '#e9ecef',
                color: currentStep === 'upload' ? 'white' : '#495057',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
              }}
            >
              1. Upload Videos
            </button>
            <button
              onClick={() => setCurrentStep('zones')}
              style={{
                padding: '8px 16px',
                backgroundColor: currentStep === 'zones' ? '#007bff' : '#e9ecef',
                color: currentStep === 'zones' ? 'white' : '#495057',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
              }}
            >
              2. Define Zones
            </button>
            <button
              onClick={() => setCurrentStep('process')}
              style={{
                padding: '8px 16px',
                backgroundColor: currentStep === 'process' ? '#007bff' : '#e9ecef',
                color: currentStep === 'process' ? 'white' : '#495057',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
              }}
            >
              3. Process
            </button>
            <button
              onClick={() => setCurrentStep('results')}
              style={{
                padding: '8px 16px',
                backgroundColor: currentStep === 'results' ? '#007bff' : '#e9ecef',
                color: currentStep === 'results' ? 'white' : '#495057',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
              }}
            >
              4. View Results
            </button>
          </div>
        </div>
      )}

      {/* Main Content */}
      <div style={{ padding: '20px' }}>
        {currentStep === 'setup' && (
          <StoreSetup onStoreCreated={handleStoreCreated} />
        )}

        {currentStep === 'upload' && storeId && (
          <div>
            <VideoUpload storeId={storeId} onUploadComplete={handleUploadComplete} />
            <div style={{ textAlign: 'center', marginTop: '20px' }}>
              <button
                onClick={() => setCurrentStep('zones')}
                style={{
                  padding: '12px 24px',
                  fontSize: '16px',
                  backgroundColor: '#28a745',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer',
                }}
              >
                Continue to Define Zones →
              </button>
            </div>
          </div>
        )}

        {currentStep === 'zones' && storeId && (
          <div>
            <ZoneDrawer storeId={storeId} onZoneCreated={handleZoneCreated} />
            <div style={{ textAlign: 'center', marginTop: '20px' }}>
              <button
                onClick={() => setCurrentStep('process')}
                style={{
                  padding: '12px 24px',
                  fontSize: '16px',
                  backgroundColor: '#28a745',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer',
                }}
              >
                Continue to Processing →
              </button>
            </div>
          </div>
        )}

        {currentStep === 'process' && storeId && (
          <ProcessingStatus storeId={storeId} onProcessingComplete={handleProcessingComplete} />
        )}

        {currentStep === 'results' && storeId && (
          <div>
            <div style={{ marginBottom: '40px' }}>
              <InsightsDashboard storeId={storeId} />
            </div>
            <div style={{ borderTop: '2px solid #ddd', paddingTop: '40px' }}>
              <HeatmapView storeId={storeId} />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;