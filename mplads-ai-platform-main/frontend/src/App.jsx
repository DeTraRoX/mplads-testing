import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import AuditTable from './pages/AuditTable';
import LiveAnalyzer from './pages/LiveAnalyzer';
import GISMap from './pages/GISMap';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="audit" element={<AuditTable />} />
          <Route path="analyzer" element={<LiveAnalyzer />} />
          <Route path="map" element={<GISMap />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
