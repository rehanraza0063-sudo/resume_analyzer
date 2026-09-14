import React from "react";
import { Routes, Route } from "react-router-dom";
import { ResumeProvider, useResume } from "./context/ResumeContext.jsx";

import Navbar from "./components/Navbar.jsx";
import Footer from "./components/Footer.jsx";
import Toast from "./components/Toast.jsx";

import Home from "./pages/Home.jsx";
import Analyze from "./pages/Analyze.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import JobMatch from "./pages/JobMatch.jsx";
import SkillGap from "./pages/SkillGap.jsx";
import About from "./pages/About.jsx";

function ToastHost() {
  const { toast } = useResume();
  if (!toast) return null;
  return <Toast message={toast.message} type={toast.type} />;
}

export default function App() {
  return (
    <ResumeProvider>
      <Navbar />
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/analyze" element={<Analyze />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/job-match" element={<JobMatch />} />
        <Route path="/skill-gap" element={<SkillGap />} />
        <Route path="/about" element={<About />} />
      </Routes>
      <Footer />
      <ToastHost />
    </ResumeProvider>
  );
}
