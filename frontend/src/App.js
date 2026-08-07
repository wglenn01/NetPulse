import { useEffect } from 'react';
import '@/App.css';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Toaster } from '@/components/ui/sonner';
import { Layout } from '@/components/Layout';
import Overview from '@/pages/Overview';
import Topology from '@/pages/Topology';
import Devices from '@/pages/Devices';
import Alerts from '@/pages/Alerts';
import Dashboards from '@/pages/Dashboards';
import NocMode from '@/pages/NocMode';
import Settings from '@/pages/Settings';

const L = (C) => (
  <Layout>
    <C />
  </Layout>
);

function App() {
  useEffect(() => {
    document.documentElement.classList.add('dark');
  }, []);
  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={L(Overview)} />
          <Route path="/topology" element={L(Topology)} />
          <Route path="/devices" element={L(Devices)} />
          <Route path="/alerts" element={L(Alerts)} />
          <Route path="/dashboards" element={L(Dashboards)} />
          <Route path="/settings" element={L(Settings)} />
          <Route path="/tv" element={<NocMode />} />
        </Routes>
      </BrowserRouter>
      <Toaster position="top-right" richColors closeButton theme="dark" />
    </div>
  );
}

export default App;
