import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/layout/Layout';
import Dashboard from './pages/Dashboard';
import AnalyzeCustomer from './pages/AnalyzeCustomer';
import RecoveryCases from './pages/RecoveryCases';
import RecoveryCaseDetail from './pages/RecoveryCaseDetail';
import Analytics from './pages/Analytics';
import Settings from './pages/Settings';
import Activity from './pages/Activity';
import Customers from './pages/Customers';
import CustomerDetail from './pages/CustomerDetail';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="analyze" element={<AnalyzeCustomer />} />
          <Route path="cases" element={<RecoveryCases />} />
          <Route path="cases/:id" element={<RecoveryCaseDetail />} />
          <Route path="customers" element={<Customers />} />
          <Route path="customers/:id" element={<CustomerDetail />} />
          <Route path="analytics" element={<Analytics />} />
          <Route path="settings" element={<Settings />} />
          <Route path="activity" element={<Activity />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
