import React, { useState, useEffect } from 'react';

const API_URL = 'http://127.0.0.1:8000';

// --- STYLES (Embedded for a clean, modern UI) ---
const styles = `
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700&display=swap');
  body { 
    font-family: 'Inter', sans-serif; 
    background-color: #f4f7f9; 
    margin: 0;
    color: #333;
  }
  .user-dashboard {
    display: flex;
    height: 100vh;
    width: 100%;
    overflow: hidden;
  }
  .history-panel {
    width: 350px;
    background: #ffffff;
    border-right: 1px solid #e0e0e0;
    padding: 20px;
    overflow-y: auto;
  }
  .history-panel h2 {
    font-size: 1.2rem;
    color: #2c3e50;
    margin-bottom: 20px;
  }
  .scan-item {
    padding: 15px;
    border-radius: 8px;
    margin-bottom: 10px;
    cursor: pointer;
    border: 1px solid #eee;
    transition: all 0.2s ease;
  }
  .scan-item.active {
    background-color: #ecf5ff;
    border-left: 4px solid #3498db;
  }
  .scan-item:hover {
    box-shadow: 0 4px 8px rgba(0,0,0,0.05);
    transform: translateY(-2px);
  }
  .scan-item p {
    margin: 0;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    font-size: 0.9rem;
    color: #555;
  }
  .scan-item-score {
    font-weight: bold;
    font-size: 1rem;
    margin-top: 5px;
  }
  .main-panel {
    flex-grow: 1;
    padding: 40px;
    display: flex;
    justify-content: center;
    align-items: center;
  }
  .detail-view {
    width: 100%;
    max-width: 700px;
    background: #fff;
    border-radius: 12px;
    padding: 30px;
    box-shadow: 0 5px 15px rgba(0,0,0,0.08);
  }
  .placeholder { text-align: center; color: #7f8c8d; }
  .score-display { text-align: center; margin-bottom: 25px; }
  .score-circle {
    width: 120px; height: 120px;
    border-radius: 50%;
    display: flex;
    justify-content: center;
    align-items: center;
    margin: auto;
    background-image: conic-gradient(var(--score-color) var(--score-percent), #e0e0e0 0);
  }
  .score-inner-circle {
    width: 100px; height: 100px;
    border-radius: 50%;
    background: white;
    display: flex;
    justify-content: center;
    align-items: center;
    font-size: 2.2rem;
    font-weight: 700;
  }
  .detail-section { margin-bottom: 20px; }
  .detail-section h3 {
    font-size: 1.1rem;
    color: #2c3e50;
    border-bottom: 2px solid #3498db;
    padding-bottom: 5px;
    margin-bottom: 15px;
  }
  .explanation p {
    font-size: 1rem;
    line-height: 1.6;
    color: #555;
  }
  .reasons-list { list-style: none; padding: 0; }
  .reasons-list li {
    background: #f9f9f9;
    padding: 10px;
    border-radius: 5px;
    margin-bottom: 8px;
    font-size: 0.9rem;
  }
  .action-buttons {
    margin-top: 30px;
    display: flex;
    gap: 15px;
  }
  .action-buttons button {
    flex-grow: 1;
    padding: 12px;
    border: none;
    border-radius: 6px;
    font-size: 1rem;
    font-weight: 500;
    cursor: pointer;
    transition: background-color 0.2s;
  }
  .btn-report { background-color: #e74c3c; color: white; }
  .btn-report:hover { background-color: #c0392b; }
  .btn-feedback { background-color: #2ecc71; color: white; }
  .btn-feedback:hover { background-color: #27ae60; }
`;

// --- The Main App Component ---
function App() {
  const [scans, setScans] = useState([]);
  const [selectedScan, setSelectedScan] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    try {
      const response = await fetch(`${API_URL}/history`);
      const data = await response.json();
      setScans(data);
    } catch (err) {
      console.error("Failed to fetch history", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleReport = async () => {
    if (!selectedScan) return;
    const comment = prompt("Please provide a brief reason for your report (optional):");
    try {
      await fetch(`${API_URL}/report`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ analysis_id: selectedScan._id, comment }),
      });
      alert("Report submitted successfully. Thank you for helping keep the web safe!");
    } catch (err) {
      alert("Failed to submit report.");
    }
  };

  const handleFeedback = async (isHelpful) => {
    if (!selectedScan) return;
    try {
      await fetch(`${API_URL}/feedback`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ analysis_id: selectedScan._id, is_helpful: isHelpful }),
      });
      alert("Thank you for your feedback!");
    } catch (err) {
      alert("Failed to submit feedback.");
    }
  };
  
  const getScoreColor = (score) => {
    if (score > 70) return '#2ecc71'; // green
    if (score > 40) return '#f39c12'; // orange
    return '#e74c3c'; // red
  };

  return (
    <>
      <style>{styles}</style>
      <div className="user-dashboard">
        <aside className="history-panel">
          <h2>Scan History</h2>
          {loading ? <p>Loading history...</p> : (
            scans.map(scan => (
              <div 
                key={scan._id} 
                className={`scan-item ${selectedScan?._id === scan._id ? 'active' : ''}`}
                onClick={() => setSelectedScan(scan)}
              >
                <p>{scan.request_text.substring(0, 40)}...</p>
                <p className="scan-item-score" style={{ color: getScoreColor(scan.result.score) }}>
                  Score: {scan.result.score}
                </p>
              </div>
            ))
          )}
        </aside>
        
        <main className="main-panel">
          {selectedScan ? (
            <div className="detail-view">
              <div className="score-display">
                <div 
                  className="score-circle" 
                  style={{'--score-color': getScoreColor(selectedScan.result.score), '--score-percent': `${selectedScan.result.score}%`}}
                >
                  <div className="score-inner-circle" style={{ color: getScoreColor(selectedScan.result.score) }}>
                    {selectedScan.result.score}
                  </div>
                </div>
              </div>

              <div className="detail-section explanation">
                <h3>Explanation</h3>
                <p>{selectedScan.result.explanation}</p>
              </div>

              {selectedScan.result.reasons.length > 0 && (
                <div className="detail-section">
                  <h3>Key Factors Detected</h3>
                  <ul className="reasons-list">
                    {selectedScan.result.reasons.map((reason, index) => (
                      <li key={index}>{reason}</li>
                    ))}
                  </ul>
                </div>
              )}

              <div className="action-buttons">
                <button className="btn-report" onClick={handleReport}>Report this Analysis</button>
                <button className="btn-feedback" onClick={() => handleFeedback(true)}>Analysis was Helpful</button>
              </div>
            </div>
          ) : (
            <div className="placeholder">
              <h2>Welcome to your Dashboard</h2>
              <p>Select a past scan from the history panel to see the detailed analysis.</p>
            </div>
          )}
        </main>
      </div>
    </>
  );
}

export default App;

