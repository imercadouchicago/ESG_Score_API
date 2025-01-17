import React from 'react';
import { BrowserRouter as Router, Route, Routes, Link } from 'react-router-dom';
import ESGDataFetcher from './Components/ESGDataFetcher';
import TableFetcher from './Components/TableFetcher';
import CompanyTableDataFetcher from './Components/CompanyTableDataFetcher';

function App() {
  return (
    <Router>
      <div className="App">
        <nav className="bg-gray-800 p-4">
          <ul className="flex space-x-4">
            <li>
              <Link 
                to="/" 
                className="text-white hover:text-blue-300 px-3"
              >
                All ESG Scores for Company
              </Link>
            </li>
            <li>
              <Link 
                to="/table-fetcher" 
                className="text-white hover:text-blue-300 px-3"
              >
                S&P 500 Data for Each ESG Source
              </Link>
            </li>
            <li>
              <Link 
                to="/company-table" 
                className="text-white hover:text-blue-300 px-3"
              >
                Company Search for Each ESG Source
              </Link>
            </li>
          </ul>
        </nav>

        <Routes>
          <Route path="/" element={<ESGDataFetcher />} />
          <Route path="/table-fetcher" element={<TableFetcher />} />
          <Route path="/company-table" element={<CompanyTableDataFetcher />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;