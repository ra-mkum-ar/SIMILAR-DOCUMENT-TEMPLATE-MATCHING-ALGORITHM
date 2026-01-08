import { useState, useEffect } from 'react';
import axios from 'axios';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const TemplateManager = () => {
  const [templates, setTemplates] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState(null);

  useEffect(() => { fetchTemplates(); }, []);

  const fetchTemplates = async () => {
    try {
      setLoading(true);
      const res = await axios.get(`${API}/templates`);
      setTemplates(Array.isArray(res.data) ? res.data : []);
    } catch {
      toast.error('Failed to fetch templates');
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    if (!file.name.match(/\.(pdf|docx)$/i)) {
      toast.error('Upload PDF or DOCX only');
      return;
    }

    const fd = new FormData();
    fd.append('file', file);

    try {
      setUploading(true);
      await axios.post(`${API}/templates/upload`, fd, {
        onUploadProgress: (e) =>
          setUploadProgress(Math.round((e.loaded * 100) / e.total)),
      });
      toast.success('Template uploaded successfully');
      fetchTemplates();
    } catch {
      toast.error('Upload failed');
    } finally {
      setUploading(false);
      setUploadProgress(0);
      e.target.value = '';
    }
  };

  const handleDelete = async (id, name) => {
    if (!window.confirm(`Delete "${name}"?`)) return;
    try {
      await axios.delete(`${API}/templates/${id}`);
      toast.success('Template deleted');
      fetchTemplates();
    } catch {
      toast.error('Delete failed');
    }
  };

  const ai = (t, k) => t?.structure_data?.ai_analysis?.[k];
  const arr = v => Array.isArray(v) ? v : [];

  const embeddingStatus = (t) =>
    t.embedding_status === 'indexed'
      ? ['Indexed', 'bg-green-100 text-green-700']
      : ['Pending', 'bg-yellow-100 text-yellow-700'];

  const risk = (t) => {
    if (t.forgery_risk === 'high') return ['High Risk', 'bg-red-100 text-red-700'];
    if (t.forgery_risk === 'medium') return ['Medium', 'bg-yellow-100 text-yellow-700'];
    return ['Safe', 'bg-green-100 text-green-700'];
  };

  const confidence = (t) =>
    Math.max(35, Math.round(100 - (t.forgery_score || 20)));

  return (
    <div className="space-y-6">

      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-3xl font-bold">Template Library</h2>
          <p className="text-slate-500">AI-powered template engine</p>
        </div>
        <div className="text-indigo-600 text-2xl font-bold">{templates.length}</div>
      </div>

      {/* Upload Section */}
      <div className="space-y-4">   {/* ✅ FIXED SPACING HERE */}

        <div
          className="upload-area cursor-pointer bg-indigo-50 p-4 rounded border hover:bg-indigo-100 transition"
          onClick={() => document.getElementById('upload').click()}
        >
          <input id="upload" type="file" accept=".pdf,.docx" onChange={handleFileUpload} hidden />
          <p className="text-center font-semibold">Upload Template</p>
          <p className="text-xs text-gray-500 text-center">PDF or DOCX format only</p>
        </div>

        {uploading && <Progress value={uploadProgress} className="h-2" />}

      </div>

      {/* Grid */}
      {loading ? (
        <p className="text-center">Loading...</p>
      ) : templates.length === 0 ? (
        <p className="text-center">No templates uploaded</p>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {templates.map((t) => {

            const [embedLabel, embedColor] = embeddingStatus(t);
            const [riskLabel, riskColor] = risk(t);
            const trust = confidence(t);

            return (
              <Card key={t.id} className="p-4 space-y-3 shadow relative">

                {/* Forgery Banner */}
                {t.forgery_risk === 'high' && (
                  <div className="bg-red-600 text-white text-xs px-2 py-1 rounded">
                    ⚠ Forgery suspected
                  </div>
                )}

                {/* Title */}
                <div className="flex justify-between">
                  <h3 className="font-semibold truncate">{t.name}</h3>
                  <Button
                    size="sm"
                    variant="ghost"
                    className="text-red-600"
                    onClick={() => handleDelete(t.id, t.name)}
                  >
                    🗑
                  </Button>
                </div>

                {/* Badges */}
                <div className="flex gap-2 flex-wrap text-xs">
                  <span className="bg-indigo-100 text-indigo-700 px-2 rounded">
                    {ai(t, 'document_type') || 'Unknown'}
                  </span>
                  <span className="bg-blue-100 text-blue-700 px-2 rounded">
                    {ai(t, 'structure_pattern') || 'Layout'}
                  </span>
                  <span className={`${embedColor} px-2 rounded`}>{embedLabel}</span>
                  <span className={`${riskColor} px-2 rounded`}>{riskLabel}</span>
                </div>

                {/* Confidence */}
                <div>
                  <div className="flex justify-between text-xs">
                    <span>Confidence</span>
                    <span>{trust}%</span>
                  </div>
                  <Progress value={trust} className="h-1" />
                </div>

                {/* Summary */}
                <p className="text-sm text-slate-600">
                  {ai(t, 'summary')?.trim() || 'AI not generated'}
                </p>

                {/* Toggle */}
                <button
                  className="text-indigo-600 text-xs hover:underline"
                  onClick={() => setExpanded(expanded === t.id ? null : t.id)}
                >
                  {expanded === t.id ? "Hide AI Details" : "Explain"}
                </button>

                {/* Expand */}
                {expanded === t.id && (
                  <div className="bg-slate-50 p-2 rounded text-xs space-y-2">
                    <p><b>Themes:</b> {arr(ai(t, 'content_themes')).join(", ") || 'N/A'}</p>
                    <p><b>Writing:</b> {ai(t, 'writing_style') || 'N/A'}</p>
                    <p><b>Pattern:</b> {ai(t, 'structure_pattern') || 'N/A'}</p>
                  </div>
                )}

                {/* Footer */}
                <div className="text-xs text-slate-500 flex justify-between border-t pt-2">
                  <span>{(t.file_size / 1024).toFixed(1)} KB</span>
                  <span>{new Date(t.upload_date).toLocaleDateString()}</span>
                </div>

              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default TemplateManager;
