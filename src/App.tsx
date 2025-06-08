import React from 'react';
import './index.css';

function App() {
  return (
    <div className="app-container">
      <div className="sidebar">
        <div className="logo-placeholder"></div>
        <nav className="navigation">
          <ul>
            <li>First tab</li>
            <li>Second tab</li>
            <li>Third tab</li>
            <li>Fourth tab</li>
            <li>Fifth tab</li>
          </ul>
        </nav>
      </div>
      <div className="main-content">
        {/* Content will go here based on routes */}
        <h1>Welcome to the Dashboard</h1>
        <p>This is where your main application content will reside.</p>
      </div>
    </div>
  );
}

export default App; 