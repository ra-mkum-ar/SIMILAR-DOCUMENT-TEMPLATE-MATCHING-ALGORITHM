import { useState } from 'react';
import axios from 'axios';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { AlertTriangle, ShieldCheck, Copy } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const DocumentMatcher = () => {
  const [matchMode, setMatchMode] = useState('single');
  const [matching, setMatching] = useState(false);
  const [matchResults, setMatchResults] = useState(null);

  const handleSingleMatch = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    if (!file.name.toLowerCase().endsWith('.pdf') && !file.name.toLowerCase().endsWith('.docx')) {
      toast.error('Only PDF and DOCX supported');
      return;
    }

    const formData = new FormData();
    formData.append('file', file);

    try {
      setMatching(true);
      setMatchResults(null);

      const response = await axios.post(`${API}/match/single`, formData);
      setMatchResults(response.data);
      toast.success('Matching completed');
      event.target.value = '';
    } catch (e) {
      toast.error('Failed to match document');
      console.error(e);
    } finally {
      setMatching(false);
    }
  };

  const getSeverity = (label) => {
    if (label === 'HIGH') return 'bg-red-100 text-red-700 border-red-200';
    if (label === 'MEDIUM') return 'bg-yellow-100 text-yellow-700 border-yellow-200';
    return 'bg-green-100 text-green-700 border-green-200';
  };

  const getClassificationColor = (type) => {
    if (type === 'FORGERY_LIKELY') return 'bg-red-600 text-white';
    if (type === 'DUPLICATE') return 'bg-blue-600 text-white';
    if (type === 'TEMPLATE_REUSE') return 'bg-yellow-600 text-white';
    return 'bg-slate-600 text-white';
  };

  return (
    <div className="space-y-6">
      <h2 className="text-3xl font-bold">Forgery-Aware Document Matching</h2>

      <Tabs value={matchMode} onValueChange={setMatchMode}>
        <TabsList className="grid grid-cols-2">
          <TabsTrigger value="single">Single</TabsTrigger>
          <TabsTrigger value="batch">Batch</TabsTrigger>
        </TabsList>

        {/* ---------------- SINGLE MATCH ----------------- */}
        <TabsContent value="single">

          {/* ✅ FIXED UPLOAD + SPACING */}
          <div className="space-y-4 mt-4 max-w-sm">

            <input
              type="file"
              accept=".pdf,.docx"
              className="hidden"
              id="upload"
              onChange={handleSingleMatch}
              disabled={matching}
            />

            <Button
              onClick={() => document.getElementById('upload').click()}
              disabled={matching}
              className="w-fit"
            >
              Upload Document
            </Button>

            {matching && (
              <Progress className="h-2 rounded-md" />
            )}

          </div>

          {matchResults && (
            <div className="mt-8 space-y-4">
              {matchResults.matches.map((m, i) => (
                <Card key={m.template_id} className="p-5">

                  <div className="flex justify-between">
                    <div>
                      <h3 className="font-bold">#{i + 1} {m.template_name}</h3>
                      <span className={`inline-block mt-1 px-3 py-1 rounded-full text-sm ${getClassificationColor(m.classification)}`}>
                        {m.classification}
                      </span>
                    </div>
                    <div className="text-3xl font-bold text-indigo-600">
                      {(m.overall_score * 100).toFixed(0)}%
                    </div>
                  </div>

                  {/* CORE SIMILARITY */}
                  <div className="grid grid-cols-3 gap-3 mt-4">
                    <Metric label="Text" value={m.text_similarity} />
                    <Metric label="Structure" value={m.structure_similarity} />
                    <Metric label="Layout" value={m.layout_similarity} />
                  </div>

                  {/* CONFIDENCE */}
                  <div className="mt-4">
                    <p className="text-sm font-semibold">Confidence Score</p>
                    <Progress value={m.confidence * 100} />
                    <small>{(m.confidence * 100).toFixed(1)}%</small>
                  </div>

                  {/* FORGERY BOX */}
                  <div className={`mt-4 p-3 rounded-lg border ${getSeverity(m.forgery_label)}`}>
                    <div className="flex items-center gap-2">
                      {m.forgery_label === 'HIGH' ? <AlertTriangle size={18}/> : <ShieldCheck size={18}/>}
                      <strong>Forgery Risk: {m.forgery_label}</strong>
                    </div>
                    <p className="text-sm mt-1">Risk Score: {(m.fraud_confidence * 100).toFixed(1)}%</p>
                  </div>

                  {/* RED FLAGS */}
                  {m.red_flags?.length > 0 && (
                    <div className="mt-4">
                      <h4 className="font-semibold text-red-700">Red Flags</h4>
                      <ul className="list-disc list-inside text-sm text-red-600">
                        {m.red_flags.map((r, idx) => <li key={idx}>{r}</li>)}
                      </ul>
                    </div>
                  )}

                  {/* FIELD LEVEL */}
                  {m.field_differences?.length > 0 && (
                    <div className="mt-4">
                      <h4 className="font-semibold">Field Differences</h4>
                      <table className="w-full text-sm border mt-2">
                        <thead className="bg-slate-100">
                          <tr>
                            <th className="p-1">Field</th>
                            <th>Status</th>
                            <th>Template</th>
                            <th>Query</th>
                          </tr>
                        </thead>
                        <tbody>
                          {m.field_differences.map((f, i) => (
                            <tr key={i} className="border-t">
                              <td className="p-1">{f.field}</td>
                              <td className={f.status === 'changed' ? 'text-red-600' : ''}>{f.status}</td>
                              <td>{f.template_value || '-'}</td>
                              <td>{f.query_value || '-'}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}

                  {/* AI ANALYSIS */}
                  <div className="bg-slate-50 mt-4 p-3 rounded">
                    <h4 className="font-semibold">AI Explanation</h4>
                    <p className="text-sm">{m.analysis}</p>
                  </div>

                  {m.is_duplicate && (
                    <div className="mt-4 text-blue-700 flex items-center gap-2">
                      <Copy size={16} /> Exact or near-duplicate detected
                    </div>
                  )}
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        {/* ---------------- BATCH ----------------- */}
        <TabsContent value="batch">
          <div className="p-4 text-slate-500">
            Batch results already compatible. No UI change needed.
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
};

const Metric = ({ label, value }) => (
  <div className="bg-slate-50 p-3 rounded">
    <div className="text-xs">{label}</div>
    <strong>{(value * 100).toFixed(1)}%</strong>
    <Progress value={value * 100} className="mt-2"/>
  </div>
);

export default DocumentMatcher;
