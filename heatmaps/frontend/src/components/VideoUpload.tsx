import React, { useState } from 'react';
import { uploadCameraVideo } from '../services/api';

interface VideoUploadProps {
  storeId: string;
  onUploadComplete: () => void;
}

const VideoUpload: React.FC<VideoUploadProps> = ({ storeId, onUploadComplete }) => {
  const [cameraIdentifier, setCameraIdentifier] = useState('');
  const [cameraName, setCameraName] = useState('');
  const [videoFile, setVideoFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!videoFile) {
      setError('Please select a video file');
      return;
    }

    setUploading(true);
    setError('');

    try {
      await uploadCameraVideo(storeId, cameraIdentifier, cameraName, videoFile);
      setCameraIdentifier('');
      setCameraName('');
      setVideoFile(null);
      onUploadComplete();
    } catch (err) {
      setError('Failed to upload video. Please try again.');
      console.error(err);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div style={{ padding: '20px', maxWidth: '500px', margin: '20px auto', border: '1px solid #ddd', borderRadius: '8px' }}>
      <h3>Upload Camera Video</h3>
      <form onSubmit={handleSubmit}>
        <div style={{ marginBottom: '15px' }}>
          <label style={{ display: 'block', marginBottom: '5px' }}>
            Camera Identifier * (e.g., cam1, cam2)
          </label>
          <input
            type="text"
            value={cameraIdentifier}
            onChange={(e) => setCameraIdentifier(e.target.value)}
            required
            style={{ width: '100%', padding: '8px', fontSize: '14px' }}
          />
        </div>

        <div style={{ marginBottom: '15px' }}>
          <label style={{ display: 'block', marginBottom: '5px' }}>
            Camera Name *
          </label>
          <input
            type="text"
            value={cameraName}
            onChange={(e) => setCameraName(e.target.value)}
            required
            style={{ width: '100%', padding: '8px', fontSize: '14px' }}
          />
        </div>

        <div style={{ marginBottom: '15px' }}>
          <label style={{ display: 'block', marginBottom: '5px' }}>
            Video File * (MP4)
          </label>
          <input
            type="file"
            accept="video/mp4,video/avi"
            onChange={(e) => setVideoFile(e.target.files?.[0] || null)}
            required
            style={{ width: '100%', padding: '8px', fontSize: '14px' }}
          />
        </div>

        {error && (
          <div style={{ color: 'red', marginBottom: '15px' }}>{error}</div>
        )}

        <button
          type="submit"
          disabled={uploading}
          style={{
            padding: '10px 20px',
            fontSize: '16px',
            backgroundColor: '#28a745',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: uploading ? 'not-allowed' : 'pointer',
          }}
        >
          {uploading ? 'Uploading...' : 'Upload Video'}
        </button>
      </form>
    </div>
  );
};

export default VideoUpload;