import React, { useState, useEffect } from 'react';



const API_URL = 'http://127.0.0.1:8000';

// --- STYLES ---
const styles = `
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700&display=swap');
  body { font-family: 'Inter', sans-serif; background-color: #f4f7f9; margin: 0; color: #333; }
  .user-dashboard { display: flex; height: 100vh; width: 100%; overflow: hidden; }
  .history-panel { width: 350px; background: #ffffff; border-right: 1px solid #e0e0e0; padding: 20px; overflow-y: auto; }
  .history-panel h2 { font-size: 1.2rem; color: #2c3e50; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center; }
  .refresh-btn { background: none; border: none; cursor: pointer; color: #3498db; font-size: 0.8rem; }
  
  .scan-item { padding: 15px; border-radius: 8px; margin-bottom: 10px; cursor: pointer; border: 1px solid #eee; transition: all 0.2s ease; }
  .scan-item.active { background-color: #ecf5ff; border-left: 4px solid #3498db; }
  .scan-item:hover { box-shadow: 0 4px 8px rgba(0,0,0,0.05); transform: translateY(-2px); }
  .scan-item p { margin: 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; font-size: 0.9rem; color: #555; }
  .scan-item-score { font-weight: bold; font-size: 1rem; margin-top: 5px; }

  .main-panel { flex-grow: 1; padding: 40px; display: flex; flex-direction: column; align-items: center; overflow-y: auto; }
  
  .input-section { width: 100%; max-width: 700px; margin-bottom: 30px; background: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }
  .input-section textarea { width: 100%; height: 80px; padding: 15px; border: 1px solid #ddd; border-radius: 8px; font-family: inherit; resize: none; box-sizing: border-box; margin-bottom: 10px; }
  .btn-analyze { width: 100%; padding: 12px; background: #3498db; color: white; border: none; border-radius: 8px; font-weight: bold; cursor: pointer; }
  .btn-analyze:disabled { background: #bdc3c7; }

  .detail-view { width: 100%; max-width: 700px; background: #fff; border-radius: 12px; padding: 30px; box-shadow: 0 5px 15px rgba(0,0,0,0.08); }
  .score-display { text-align: center; margin-bottom: 25px; }
  .score-circle { width: 120px; height: 120px; border-radius: 50%; display: flex; justify-content: center; align-items: center; margin: auto; background-image: conic-gradient(var(--score-color) var(--score-percent), #e0e0e0 0); }
  .score-inner-circle { width: 100px; height: 100px; border-radius: 50%; background: white; display: flex; justify-content: center; align-items: center; font-size: 2.2rem; font-weight: 700; }
  
  .loading-overlay { text-align: center; padding: 40px; }
  .spinner { border: 4px solid #f3f3f3; border-top: 4px solid #3498db; border-radius: 50%; width: 30px; height: 30px; animation: spin 2s linear infinite; margin: 10px auto; }
  @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }

  .detail-section { margin-bottom: 20px; }
  .detail-section h3 { font-size: 1.1rem; color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 5px; margin-bottom: 15px; }
`;

function App() {
  const [scans, setScans] = useState([]);
  const [selectedScan, setSelectedScan] = useState(null);
  const [inputText, setInputText] = useState("");
  const [isProcessing, setIsProcessing] = useState(false);
  const [historyLoading, setHistoryLoading] = useState(true);

  const fetchData = async () => {
    try {
      const response = await fetch(`${API_URL}/history`);
      const data = await response.json();
      setScans(data);
    } catch (err) { console.error("History fetch failed", err); }
    finally { setHistoryLoading(false); }
  };

  useEffect(() => { fetchData(); }, []);

  // --- ASYNC POLLING LOGIC ---
  const pollTaskStatus = async (taskId) => {
    const interval = setInterval(async () => {
      try {
        const response = await fetch(`${API_URL}/status/${taskId}`);
        const data = await response.json();

        if (data.status === 'completed') {
          clearInterval(interval);
          setIsProcessing(false);
          // Immediately refresh history to show the new scan
          await fetchData();
          // Auto-select the new scan result
          setSelectedScan({ request_text: inputText, result: data.result });
          setInputText("");
        } else if (data.status === 'failed') {
          clearInterval(interval);
          setIsProcessing(false);
          alert("AI Analysis failed: " + data.error);
        }
      } catch (err) {
        clearInterval(interval);
        setIsProcessing(false);
        console.error("Polling error", err);
      }
    }, 2000); // Check every 2 seconds
  };

  const handleAnalyze = async () => {
    if (!inputText.trim()) return;
    setIsProcessing(true);
    setSelectedScan(null);

    try {
      const response = await fetch(`${API_URL}/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: inputText }),
      });
      const data = await response.json();
      
      if (data.task_id) {
        pollTaskStatus(data.task_id);
      }
    } catch (err) {
      setIsProcessing(false);
      alert("Failed to start analysis");
    }
  };

  const getScoreColor = (score) => {
    if (score > 70) return '#2ecc71';
    if (score > 40) return '#f39c12';
    return '#e74c3c';
  };

  return (
    <>
      <style>{styles}</style>
      <div className="user-dashboard">
        <aside className="history-panel">
          <h2>History <button className="refresh-btn" onClick={fetchData}>Refresh</button></h2>
          {historyLoading ? <p>Loading history...</p> : (
            scans.map(scan => (
              <div 
                key={scan._id} 
                className={`scan-item ${selectedScan?._id === scan._id ? 'active' : ''}`}
                onClick={() => setSelectedScan(scan)}
              >
                <p>{scan.request_text.substring(0, 40)}...</p>
                <p className="scan-item-score" style={{ color: getScoreColor(scan.result?.score) }}>
                  Score: {scan.result?.score}
                </p>
              </div>
            ))
          )}
        </aside>
        
        <main className="main-panel">
          <section className="input-section">
            <textarea 
              placeholder="Paste text or claim to analyze..." 
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              disabled={isProcessing}
            />
            <button 
              className="btn-analyze" 
              onClick={handleAnalyze}
              disabled={isProcessing || !inputText}
            >
              {isProcessing ? "Analyzing with AI Workers..." : "Run Global Analysis"}
            </button>
          </section>

          {isProcessing && (
            <div className="loading-overlay">
              <div className="spinner"></div>
              <p>Your request is in the global queue. AI agents are processing...</p>
            </div>
          )}

          {selectedScan && (
            <div className="detail-view">
              <div className="score-display">
                <div className="score-circle" style={{'--score-color': getScoreColor(selectedScan.result.score), '--score-percent': `${selectedScan.result.score}%`}}>
                  <div className="score-inner-circle" style={{ color: getScoreColor(selectedScan.result.score) }}>
                    {selectedScan.result.score}
                  </div>
                </div>
              </div>
              <div className="detail-section">
                <h3>AI Explanation</h3>
                <p>{selectedScan.result.explanation}</p>
              </div>
              {selectedScan.result.reasons?.length > 0 && (
                <div className="detail-section">
                  <h3>Detected Markers</h3>
                  <ul style={{listStyle: 'none', padding: 0}}>
                    {selectedScan.result.reasons.map((r, i) => (
                      <li key={i} style={{background: '#f9f9f9', padding: '10px', borderRadius: '6px', marginBottom: '5px', fontSize: '0.9rem'}}>⚠️ {r}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </main>
      </div>
    </>
  );
}

export default App;

