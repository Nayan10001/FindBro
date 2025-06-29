import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import HomePage from './pages/HomePage';
import ConnectionHomePage from './pages/ConnectionHomePage';
import ProjectsPage from './pages/ProjectsPage';
import StartupsPage from './pages/StartupsPage';
import './App.css';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/connect" element={<ConnectionHomePage />} />
        <Route path="/projects" element={<ProjectsPage />} />
        <Route path="/startups" element={<StartupsPage />} />
      </Routes>
    </Router>
  );
}

export default App;