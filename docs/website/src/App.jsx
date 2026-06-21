import React from 'react'
import { HashRouter, Routes, Route } from 'react-router-dom'
import LandingPage from './pages/Landing'
import DocsPage from './pages/Docs'

function App() {
  return (
    <HashRouter>
      <Routes>
        <Route path="/docs/*" element={<DocsPage />} />
        <Route path="*" element={<LandingPage />} />
      </Routes>
    </HashRouter>
  )
}

export default App
