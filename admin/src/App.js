import React, { useState, useEffect } from 'react';
import { Chart as ChartJS, ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement } from 'chart.js';
import { Doughnut, Bar } from 'react-chartjs-2';

// Chart.js components
ChartJS.register(ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement);

const API_URL = 'http://127.0.0.1:8000';

// --- STYLES --- 
const styles = `
  body { font-family: sans-serif; background-color: #f0f2f5; margin: 0; }
  .admin-dashboard { display: flex; }
  .sidebar { width: 220px; background: #2c3e50; color: white; height: 100vh; padding: 20px; }
  .sidebar h1 { font-size: 1.5em; margin-bottom: 30px; }
  .sidebar ul { list-style: none; padding: 0; }
  .sidebar li { padding: 15px; border-radius: 5px; cursor: pointer; }
  .sidebar li.active { background: #3498db; }
  .main-content { flex-grow: 1; padding: 40px; }
  .dashboard-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 30px; }
  .card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
  .card h3 { margin-top: 0; }
  table { width: 100%; border-collapse: collapse; }
  th, td { padding: 12px; border-bottom: 1px solid #ddd; text-align: left; }
  th { background: #f9f9f9; }
  .status { padding: 5px 10px; border-radius: 12px; color: white; font-size: 0.8em; }
  .status-submitted { background: #f39c12; }
  .status-escalated { background: #e74c3c; }
  .status-resolved { background: #2ecc71; }
  .action-buttons button { margin-right: 10px; padding: 8px 12px; border-radius: 5px; border: none; cursor: pointer; }
  .btn-escalate { background: #e74c3c; color: white; }
  .btn-resolve { background: #2ecc71; color: white; }
  .btn-back { background: #95a5a6; color: white; margin-bottom: 20px;}
`;

// --- COMPONENTS ---

function AnalyticsDashboard({ analytics }) {
  const statusData = {
    labels: ['Submitted', 'Escalated', 'Resolved'],
    datasets: [{
      data: [analytics.status_counts.submitted, analytics.status_counts.escalated, analytics.status_counts.resolved],
      backgroundColor: ['#f39c12', '#e74c3c', '#2ecc71'],
    }],
  };
  const dailyData = {
    labels: analytics.daily_reports.map(d => d._id),
    datasets: [{
      label: 'Reports per Day',
      data: analytics.daily_reports.map(d => d.count),
      backgroundColor: '#3498db',
    }]
  };
  return (
    <div>
      <h2>Analytics Overview</h2>
      <div className="dashboard-grid">
        <div className="card">
          <h3>Reports by Status</h3>
          <Doughnut data={statusData} />
        </div>
        <div className="card">
          <h3>Reports per Day</h3>
          <Bar data={dailyData} />
        </div>
      </div>
    </div>
  );
}

function ReportDetail({ report, onBack, onUpdate }) {
  const handleAction = async (newStatus) => {
    try {
      await fetch(`${API_URL}/reports/${report._id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: newStatus })
      });
      onUpdate(); // Refresh the list
      onBack(); // Go back to the list view
    } catch (err) {
      alert('Failed to update report status.');
    }
  };
  
  const handleOfficialReport = () => {
    const subject = `Misinformation Report: ${report.analysis.request_text.substring(0, 30)}...`;
    const body = `
      Hello Platform Safety Team,

      We are escalating the following content for review based on our analysis:
      
      Content snippet: "${report.analysis.request_text}"
      Detected Credibility Score: ${report.analysis.result.score}/100
      Key Reasons: ${report.analysis.result.reasons.join(', ')}
      
      User Comment: ${report.comment || 'N/A'}
      
      Please investigate this content for potential violation of your terms of service.
      
      Thank you,
      Project Inocula Moderation Team
    `;
    window.location.href = `mailto:safety@platform.com?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
  };
  
  return (
    <div className="card">
      <button className="btn-back" onClick={onBack}>← Back to Reports</button>
      <h2>Report Details</h2>
      <p><strong>Content:</strong> {report.analysis.request_text}</p>
      <p><strong>Score:</strong> {report.analysis.result.score}</p>
      <p><strong>Explanation:</strong> {report.analysis.result.explanation}</p>
      <p><strong>User Comment:</strong> {report.comment || 'N/A'}</p>
      <p><strong>Current Status:</strong> <span className={`status status-${report.status}`}>{report.status}</span></p>
      <div className="action-buttons">
        <button className="btn-escalate" onClick={handleOfficialReport}>Escalate to Platform</button>
        <button className="btn-resolve" onClick={() => handleAction('resolved')}>Mark as Resolved</button>
      </div>
    </div>
  );
}

function ReportsList({ reports, setSelectedReport }) {
  return (
    <div className="card">
      <h2>User Reports</h2>
      <table>
        <thead>
          <tr>
            <th>Content Snippet</th>
            <th>Score</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {reports.map(report => (
            <tr key={report._id} onClick={() => setSelectedReport(report)} style={{ cursor: 'pointer' }}>
              <td>{report.analysis.request_text.substring(0, 50)}...</td>
              <td>{report.analysis.result.score}</td>
              <td><span className={`status status-${report.status}`}>{report.status}</span></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function App() {
  const [view, setView] = useState('dashboard');
  const [reports, setReports] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [selectedReport, setSelectedReport] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [reportsRes, analyticsRes] = await Promise.all([
        fetch(`${API_URL}/reports`),
        fetch(`${API_URL}/analytics`)
      ]);
      const reportsData = await reportsRes.json();
      const analyticsData = await analyticsRes.json();
      setReports(reportsData);
      setAnalytics(analyticsData);
    } catch (err) {
      console.error("Failed to fetch data", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
      // Then, set up an interval to refetch every 10 seconds (10000 ms)
    const intervalId = setInterval(fetchData, 10000);

    // It stops the interval to prevent memory leaks.
    return () => clearInterval(intervalId);
  }, []); 
  
  
  const renderView = () => {
    if (loading) return <p>Loading...</p>;

    if (selectedReport) {
      return <ReportDetail report={selectedReport} onBack={() => setSelectedReport(null)} onUpdate={fetchData} />;
    }

    switch (view) {
      case 'dashboard':
        return analytics ? <AnalyticsDashboard analytics={analytics} /> : <p>Loading analytics...</p>;
      case 'reports':
        return <ReportsList reports={reports} setSelectedReport={setSelectedReport} />;
      default:
        return <p>Dashboard</p>;
    }
  };

  return (
    <>
      <style>{styles}</style>
      <div className="admin-dashboard">
        <aside className="sidebar">
          <h1>Inocula Admin</h1>
          <ul>
            <li className={view === 'dashboard' ? 'active' : ''} onClick={() => { setView('dashboard'); setSelectedReport(null); }}>Dashboard</li>
            <li className={view === 'reports' ? 'active' : ''} onClick={() => { setView('reports'); setSelectedReport(null); }}>Reports</li>
          </ul>
        </aside>
        <main className="main-content">
          {renderView()}
        </main>
      </div>
    </>
  );
}

export default App;
