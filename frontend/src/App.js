import { useState } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import TemplateManager from "@/components/TemplateManager";
import DocumentMatcher from "@/components/DocumentMatcher";
import MatchHistory from "@/components/MatchHistory";
import { Toaster } from "@/components/ui/sonner";

const Home = () => {
  const [activeTab, setActiveTab] = useState("templates");

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-5xl lg:text-6xl font-bold text-slate-900 mb-3" style={{ fontFamily: 'Space Grotesk, sans-serif' }}>
            Document Matcher
          </h1>
          <p className="text-lg text-slate-600" style={{ fontFamily: 'Inter, sans-serif' }}>
            AI-powered document template matching with intelligent similarity analysis
          </p>
        </div>

        {/* Navigation Tabs */}
        <div className="bg-white rounded-xl shadow-sm mb-6 p-2 flex gap-2">
          <button
            data-testid="templates-tab"
            onClick={() => setActiveTab("templates")}
            className={`flex-1 py-3 px-6 rounded-lg font-medium transition-all ${
              activeTab === "templates"
                ? "bg-indigo-600 text-white shadow-md"
                : "text-slate-600 hover:bg-slate-50"
            }`}
          >
            📁 Template Manager
          </button>
          <button
            data-testid="matcher-tab"
            onClick={() => setActiveTab("matcher")}
            className={`flex-1 py-3 px-6 rounded-lg font-medium transition-all ${
              activeTab === "matcher"
                ? "bg-indigo-600 text-white shadow-md"
                : "text-slate-600 hover:bg-slate-50"
            }
            `}
          >
            🔍 Document Matcher
          </button>
          <button
            data-testid="history-tab"
            onClick={() => setActiveTab("history")}
            className={`flex-1 py-3 px-6 rounded-lg font-medium transition-all ${
              activeTab === "history"
                ? "bg-indigo-600 text-white shadow-md"
                : "text-slate-600 hover:bg-slate-50"
            }`}
          >
            📜 Match History
          </button>
        </div>

        {/* Content */}
        <div className="bg-white rounded-xl shadow-lg p-6 min-h-[600px]">
          {activeTab === "templates" && <TemplateManager />}
          {activeTab === "matcher" && <DocumentMatcher />}
          {activeTab === "history" && <MatchHistory />}
        </div>
      </div>
      <Toaster position="top-right" />
    </div>
  );
};

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Home />} />
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;