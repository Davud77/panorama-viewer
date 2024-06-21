import React, { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Home from './components/Home';
import UploadPage from './components/UploadPage';
import MapPage from './components/MapPage';
import LoginPage from './components/LoginPage';
import ProfilePage from './components/ProfilePage';
import './assets/css/styles.css';
import { useAuth } from './contexts/AuthContext';

function App() {
  const { isAuthenticated, login } = useAuth();

  useEffect(() => {
    const auth = localStorage.getItem('auth') === 'true';
    if (auth) {
      login();
    }
  }, [login]);

  return (
    <Router>
      <Routes>
        <Route path="/" element={isAuthenticated ? <Home /> : <Navigate replace to="/login" />} />
        <Route path="/login" element={isAuthenticated ? <Navigate replace to="/" /> : <LoginPage />} />
        <Route path="/upload" element={isAuthenticated ? <UploadPage /> : <Navigate replace to="/login" />} />
        <Route path="/map" element={isAuthenticated ? <MapPage /> : <Navigate replace to="/login" />} />
        <Route path="/profile" element={isAuthenticated ? <ProfilePage /> : <Navigate replace to="/login" />} />
      </Routes>
    </Router>
  );
}

export default App;
