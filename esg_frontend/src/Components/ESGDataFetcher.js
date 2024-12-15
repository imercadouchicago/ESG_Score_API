import React, { useState } from 'react';

const ESGDataFetcher = () => {
  const [companyData, setCompanyData] = useState(null);
  const [ticker, setTicker] = useState('');
  const [error, setError] = useState(null);

  const fetchCompanyData = async () => {
    try {
      // Fetching data from all tables for a specific ticker
      const response = await fetch(`/esg_api/all_tables/${ticker}`);
      
      if (!response.ok) {
        throw new Error('Failed to fetch company data');
      }
      
      const data = await response.json();
      setCompanyData(data);
      setError(null);
    } catch (err) {
      setError(err.message);
      setCompanyData(null);
    }
  };

  return (
    <div className="p-4 max-w-md mx-auto">
      <h2 className="text-2xl font-bold mb-4">ESG Company Scores</h2>
      
      <div className="flex mb-4">
        <input 
          type="text" 
          value={ticker}
          onChange={(e) => setTicker(e.target.value.toUpperCase())}
          placeholder="Enter Company Ticker"
          className="border p-2 mr-2 flex-grow"
        />
        <button 
          onClick={fetchCompanyData}
          className="bg-blue-500 text-white p-2 rounded"
        >
          Fetch Data
        </button>
      </div>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      )}

      {companyData && (
        <div className="bg-white shadow-md rounded p-4">
          <h3 className="text-xl font-semibold mb-2">{ticker} ESG Scores</h3>
          {Object.entries(companyData).map(([source, scores]) => (
            <div key={source} className="mb-3">
              <h4 className="font-medium">{source}</h4>
              <pre className="bg-gray-100 p-2 rounded text-sm">
                {JSON.stringify(scores, null, 2)}
              </pre>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default ESGDataFetcher;