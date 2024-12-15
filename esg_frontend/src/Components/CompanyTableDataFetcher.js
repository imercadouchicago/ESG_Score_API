import React, { useState } from 'react';

const CompanyTableDataFetcher = () => {
  const [tableName, setTableName] = useState('');
  const [ticker, setTicker] = useState('');
  const [companyData, setCompanyData] = useState(null);
  const [error, setError] = useState(null);

  const fetchCompanyTableData = async () => {
    try {
      const response = await fetch(`/esg_api/${tableName}/${ticker}`);
      
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
    <div className="p-4 max-w-xl mx-auto">
      <h2 className="text-2xl font-bold mb-4">Fetch Company Data from Specific Table</h2>
      
      <div className="space-y-4">
        <div className="flex space-x-2">
          <select 
            value={tableName}
            onChange={(e) => setTableName(e.target.value)}
            className="border p-2 flex-grow"
          >
            <option value="">Select a Table</option>
            <option value="csrhub_table">CSRHub Table</option>
            <option value="lseg_table">LSEG Table</option>
            <option value="msci_table">MSCI Table</option>
            <option value="spglobal_table">S&P Global Table</option>
            <option value="yahoo_table">Yahoo Table</option>
          </select>
          <input 
            type="text" 
            value={ticker}
            onChange={(e) => setTicker(e.target.value.toUpperCase())}
            placeholder="Company Ticker"
            className="border p-2 flex-grow"
          />
          <button 
            onClick={fetchCompanyTableData}
            className="bg-blue-500 text-white p-2 rounded"
            disabled={!tableName || !ticker}
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
            <h3 className="text-xl font-semibold mb-2">{ticker} Data in {tableName}</h3>
            <div className="space-y-2">
              {companyData.map((entry, index) => (
                <div 
                  key={index} 
                  className="bg-gray-100 p-3 rounded"
                >
                  {Object.entries(entry).map(([key, value]) => (
                    <div key={key} className="flex">
                      <span className="font-medium mr-2">{key}:</span>
                      <span>{value !== null ? String(value) : 'N/A'}</span>
                    </div>
                  ))}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default CompanyTableDataFetcher;