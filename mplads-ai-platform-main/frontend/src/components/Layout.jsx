import React, { useState } from 'react';
import { Outlet, useNavigate } from 'react-router-dom';
import Sidebar from './Sidebar';
import Navbar from './Navbar';

const Layout = () => {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [activeRole, setActiveRole] = useState('ADMIN');
  const [refreshKey, setRefreshKey] = useState(0);
  const [language, setLanguage] = useState('en');
  const navigate = useNavigate();

  const handleDatabaseReseeded = () => {
    setRefreshKey((prev) => prev + 1);
  };

  const handleSelectProject = (projectId) => {
    if (projectId) {
      navigate(`/audit?id=${projectId}`);
    }
  };

  return (
    <div className="min-h-screen text-slate-100 flex relative">
      <div className="fixed inset-0 cyber-grid pointer-events-none"></div>
      <Sidebar
        isCollapsed={isCollapsed}
        toggleSidebar={() => setIsCollapsed(!isCollapsed)}
        language={language}
      />

      <div
        className={`flex-1 flex flex-col transition-all duration-300 ${
          isCollapsed ? 'ml-20' : 'ml-64'
        }`}
      >
        <Navbar
          activeRole={activeRole}
          setActiveRole={setActiveRole}
          onDatabaseReseeded={handleDatabaseReseeded}
          onSelectProject={handleSelectProject}
          language={language}
          setLanguage={setLanguage}
        />

        <main className="flex-1 p-6 overflow-y-auto">
          <Outlet context={{ activeRole, refreshKey, language }} />
        </main>
      </div>
    </div>
  );
};

export default Layout;
