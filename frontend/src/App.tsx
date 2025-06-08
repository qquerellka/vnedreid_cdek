import React from 'react';
import { Outlet } from 'react-router-dom';
import Navigation from './components/Navigation';
import './App.css';

const App: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-50">
      <Navigation />
      <main>
        <Outlet />
      </main>
    </div>
  );
};

export default App;
