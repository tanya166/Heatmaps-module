import React, { useState, useEffect } from 'react';
import { getDailyInsights } from '../services/api';
import { DailyInsights } from '../types';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

interface InsightsDashboardProps {
  storeId: string;
}

const InsightsDashboard: React.FC<InsightsDashboardProps> = ({ storeId }) => {
  const [insights, setInsights] = useState<DailyInsights | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    loadInsights();
  }, [storeId]);

  const loadInsights = async () => {
    setLoading(true);
    setError('');

    try {
      const data = await getDailyInsights(storeId);
      if (data && data.length > 0) {
        setInsights(data[0]); // Get the latest insights
      } else {
        setError('No insights available');
      }
    } catch (err) {
      setError('Failed to load insights. Please ensure videos have been processed.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div style={{ padding: '20px', textAlign: 'center' }}>
        <p>Loading insights...</p>
      </div>
    );
  }

  if (error || !insights) {
    return (
      <div style={{ padding: '20px', textAlign: 'center', color: 'red' }}>
        <p>{error || 'No insights available'}</p>
      </div>
    );
  }

  const chartData = insights.zone_insights.map((zone) => ({
    name: zone.zone_name,
    visits: zone.total_visits,
    avgDwell: parseFloat(zone.avg_dwell_time.toFixed(1)),
    density: parseFloat(zone.crowd_density.toFixed(2)),
  }));

  return (
    <div style={{ padding: '20px' }}>
      <h2>📊 Daily Insights Dashboard</h2>
      <p style={{ color: '#666', marginBottom: '30px' }}>
        Analysis Date: {new Date(insights.date).toLocaleDateString()}
      </p>

      {/* Summary Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '20px', marginBottom: '30px' }}>
        <div style={{ padding: '20px', backgroundColor: '#3498db', color: 'white', borderRadius: '8px' }}>
          <h3 style={{ margin: '0 0 10px 0', fontSize: '16px' }}>Total Unique Customers</h3>
          <p style={{ fontSize: '32px', fontWeight: 'bold', margin: 0 }}>{insights.total_unique_customers}</p>
        </div>

        <div style={{ padding: '20px', backgroundColor: '#2ecc71', color: 'white', borderRadius: '8px' }}>
          <h3 style={{ margin: '0 0 10px 0', fontSize: '16px' }}>Zones Analyzed</h3>
          <p style={{ fontSize: '32px', fontWeight: 'bold', margin: 0 }}>{insights.total_zones_analyzed}</p>
        </div>

        <div style={{ padding: '20px', backgroundColor: '#9b59b6', color: 'white', borderRadius: '8px' }}>
          <h3 style={{ margin: '0 0 10px 0', fontSize: '16px' }}>Avg Store Dwell Time</h3>
          <p style={{ fontSize: '32px', fontWeight: 'bold', margin: 0 }}>{insights.avg_store_dwell_time.toFixed(1)}s</p>
        </div>

        <div style={{ padding: '20px', backgroundColor: '#e74c3c', color: 'white', borderRadius: '8px' }}>
          <h3 style={{ margin: '0 0 10px 0', fontSize: '16px' }}>Peak Hour</h3>
          <p style={{ fontSize: '32px', fontWeight: 'bold', margin: 0 }}>
            {insights.peak_hour}:00
          </p>
          <p style={{ fontSize: '14px', margin: '5px 0 0 0' }}>
            {insights.peak_hour_customers} customers
          </p>
        </div>
      </div>

      {/* Hottest and Coldest Zones */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', marginBottom: '30px' }}>
        <div style={{ padding: '20px', border: '2px solid #e74c3c', borderRadius: '8px', backgroundColor: '#ffebee' }}>
          <h3 style={{ color: '#e74c3c', marginTop: 0 }}>🔥 Hottest Zone</h3>
          <h4 style={{ margin: '10px 0' }}>{insights.hottest_zone.zone_name}</h4>
          <div style={{ fontSize: '14px' }}>
            <p><strong>Total Visits:</strong> {insights.hottest_zone.visits}</p>
            <p><strong>Avg Dwell Time:</strong> {insights.hottest_zone.avg_dwell_time.toFixed(1)}s</p>
            <p><strong>Crowd Density:</strong> {insights.hottest_zone.crowd_density.toFixed(2)} visits/hour</p>
          </div>
          <div style={{ marginTop: '15px', padding: '10px', backgroundColor: '#ffcdd2', borderRadius: '4px' }}>
            <strong>💡 Insight:</strong> High engagement zone. Consider expanding product selection or using for promotions.
          </div>
        </div>

        <div style={{ padding: '20px', border: '2px solid #3498db', borderRadius: '8px', backgroundColor: '#e3f2fd' }}>
          <h3 style={{ color: '#3498db', marginTop: 0 }}>❄️ Coldest Zone</h3>
          <h4 style={{ margin: '10px 0' }}>{insights.coldest_zone.zone_name}</h4>
          <div style={{ fontSize: '14px' }}>
            <p><strong>Total Visits:</strong> {insights.coldest_zone.visits}</p>
            <p><strong>Avg Dwell Time:</strong> {insights.coldest_zone.avg_dwell_time.toFixed(1)}s</p>
            <p><strong>Crowd Density:</strong> {insights.coldest_zone.crowd_density.toFixed(2)} visits/hour</p>
          </div>
          <div style={{ marginTop: '15px', padding: '10px', backgroundColor: '#bbdefb', borderRadius: '4px' }}>
            <strong>💡 Insight:</strong> Low traffic area. Consider improving visibility, signage, or relocating products.
          </div>
        </div>
      </div>

      {/* Visits Chart */}
      <div style={{ marginBottom: '30px' }}>
        <h3>Zone Visits Comparison</h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" angle={-45} textAnchor="end" height={100} />
            <YAxis />
            <Tooltip />
            <Legend />
            <Bar dataKey="visits" fill="#3498db" name="Total Visits" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Dwell Time Chart */}
      <div style={{ marginBottom: '30px' }}>
        <h3>Average Dwell Time by Zone</h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" angle={-45} textAnchor="end" height={100} />
            <YAxis />
            <Tooltip />
            <Legend />
            <Bar dataKey="avgDwell" fill="#2ecc71" name="Avg Dwell Time (s)" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Crowd Density Chart */}
      <div style={{ marginBottom: '30px' }}>
        <h3>Crowd Density by Zone</h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" angle={-45} textAnchor="end" height={100} />
            <YAxis />
            <Tooltip />
            <Legend />
            <Bar dataKey="density" fill="#e74c3c" name="Crowd Density (visits/hour)" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Detailed Zone Table */}
      <div>
        <h3>Zone-wise Detailed Insights</h3>
        <table style={{ width: '100%', borderCollapse: 'collapse', marginTop: '20px' }}>
          <thead>
            <tr style={{ backgroundColor: '#f8f9fa' }}>
              <th style={{ padding: '12px', border: '1px solid #ddd', textAlign: 'left' }}>Zone Name</th>
              <th style={{ padding: '12px', border: '1px solid #ddd', textAlign: 'center' }}>Total Visits</th>
              <th style={{ padding: '12px', border: '1px solid #ddd', textAlign: 'center' }}>Unique Visitors</th>
              <th style={{ padding: '12px', border: '1px solid #ddd', textAlign: 'center' }}>Avg Dwell (s)</th>
              <th style={{ padding: '12px', border: '1px solid #ddd', textAlign: 'center' }}>Crowd Density</th>
              <th style={{ padding: '12px', border: '1px solid #ddd', textAlign: 'center' }}>Engagement %</th>
              <th style={{ padding: '12px', border: '1px solid #ddd', textAlign: 'center' }}>Peak Hour</th>
            </tr>
          </thead>
          <tbody>
            {insights.zone_insights.map((zone) => (
              <tr key={zone.zone_id}>
                <td style={{ padding: '12px', border: '1px solid #ddd' }}>{zone.zone_name}</td>
                <td style={{ padding: '12px', border: '1px solid #ddd', textAlign: 'center' }}>{zone.total_visits}</td>
                <td style={{ padding: '12px', border: '1px solid #ddd', textAlign: 'center' }}>{zone.unique_visitors}</td>
                <td style={{ padding: '12px', border: '1px solid #ddd', textAlign: 'center' }}>{zone.avg_dwell_time.toFixed(1)}</td>
                <td style={{ padding: '12px', border: '1px solid #ddd', textAlign: 'center' }}>{zone.crowd_density.toFixed(2)}</td>
                <td style={{ padding: '12px', border: '1px solid #ddd', textAlign: 'center' }}>{zone.engagement_rate.toFixed(1)}%</td>
                <td style={{ padding: '12px', border: '1px solid #ddd', textAlign: 'center' }}>{zone.peak_hour}:00</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Key Recommendations */}
      <div style={{ marginTop: '40px', padding: '20px', backgroundColor: '#fff3cd', borderRadius: '8px', border: '1px solid #ffc107' }}>
        <h3 style={{ marginTop: 0, color: '#856404' }}>💡 Key Recommendations</h3>
        <ul style={{ lineHeight: '1.8' }}>
          <li>
            <strong>Peak Hour Staffing:</strong> Ensure adequate staff during {insights.peak_hour}:00 - {insights.peak_hour + 1}:00 
            when {insights.peak_hour_customers} customers are active.
          </li>
          <li>
            <strong>High Engagement Zones:</strong> {insights.hottest_zone.zone_name} shows strong customer interest. 
            Consider expanding this product category or using it for high-margin items.
          </li>
          <li>
            <strong>Low Traffic Areas:</strong> {insights.coldest_zone.zone_name} needs attention. 
            Improve signage, relocate popular products here, or consider space reallocation.
          </li>
          <li>
            <strong>Store Layout:</strong> Average dwell time of {insights.avg_store_dwell_time.toFixed(1)}s suggests 
            {insights.avg_store_dwell_time > 10 ? ' good engagement - maintain current layout.' : ' quick browsing - consider improving product visibility.'}
          </li>
        </ul>
      </div>
    </div>
  );
};

export default InsightsDashboard;