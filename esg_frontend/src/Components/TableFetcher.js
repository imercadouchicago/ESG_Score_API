import React, { useState } from 'react';

const TableFetcher = () => {
  const [tableName, setTableName] = useState('');
  const [tableData, setTableData] = useState(null);
  const [error, setError] = useState(null);

  const fetchTableData = async () => {
    try {
      const response = await fetch(`/esg_api/${tableName}`);
      
      if (!response.ok) {
        throw new Error('Failed to fetch table data');
      }
      
      const data = await response.json();
      setTableData(data);
      setError(null);
    } catch (err) {
      setError(err.message);
      setTableData(null);
    }
  };

  return (
    <div className="p-4 max-w-xl mx-auto">
      <h2 className="text-2xl font-bold mb-4">Fetch Table Data</h2>
      
      <div className="flex mb-4">
        <select 
          value={tableName}
          onChange={(e) => setTableName(e.target.value)}
          className="border p-2 mr-2 flex-grow"
        >
          <option value="">Select a Table</option>
          <option value="csrhub_table">CSRHub Table</option>
          <option value="lseg_table">LSEG Table</option>
          <option value="msci_table">MSCI Table</option>
          <option value="spglobal_table">S&P Global Table</option>
          <option value="yahoo_table">Yahoo Table</option>
        </select>
        <button 
          onClick={fetchTableData}
          className="bg-blue-500 text-white p-2 rounded"
          disabled={!tableName}
        >
          Fetch Table
        </button>
      </div>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      )}

      {tableData && (
        <div className="bg-white shadow-md rounded p-4 overflow-x-auto">
          <h3 className="text-xl font-semibold mb-2">{tableName} Data</h3>
          <table className="w-full border-collapse">
            <thead>
              <tr className="bg-gray-200">
                {Object.keys(tableData[0] || {}).map((header) => (
                  <th key={header} className="border p-2">{header}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {tableData.map((row, index) => (
                <tr key={index} className="hover:bg-gray-100">
                  {Object.values(row).map((value, colIndex) => (
                    <td key={colIndex} className="border p-2">
                      {value !== null ? String(value) : 'N/A'}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default TableFetcher;