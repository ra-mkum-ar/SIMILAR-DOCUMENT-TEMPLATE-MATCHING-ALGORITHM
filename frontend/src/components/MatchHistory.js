import { useState, useEffect } from 'react';
import axios from 'axios';
import { toast } from 'sonner';
import { Card } from '@/components/ui/card';
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion';
import { Progress } from '@/components/ui/progress';
import { AlertTriangle, ShieldCheck, Copy } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const MatchHistory = () => {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/match/history`);
      setHistory(response.data);
    } catch (error) {
      toast.error('Failed to fetch history');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const riskColor = (risk) => {
    if (risk === 'HIGH') return 'bg-red-100 text-red-700 border-red-200';
    if (risk === 'MEDIUM') return 'bg-yellow-100 text-yellow-700 border-yellow-200';
    return 'bg-green-100 text-green-700 border-green-200';
  };

  const classificationColor = (type) => {
    if (type === 'FORGERY_LIKELY') return 'bg-red-600 text-white';
    if (type === 'DUPLICATE') return 'bg-blue-600 text-white';
    if (type === 'TEMPLATE_REUSE') return 'bg-yellow-600 text-white';
    return 'bg-slate-600 text-white';
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-3xl font-bold text-slate-900">Match History</h2>
          <p className="text-slate-600 mt-1">Forgery-aware match history</p>
        </div>
        <div className="text-right">
          <div className="text-2xl font-bold text-indigo-600">{history.length}</div>
          <div className="text-sm text-slate-500">Records</div>
        </div>
      </div>

      {loading ? (
        <div className="text-center py-12">Loading history...</div>
      ) : history.length === 0 ? (
        <div className="text-center py-12 text-slate-500">
          No history found.
        </div>
      ) : (
        <Accordion type="single" collapsible className="space-y-3">
          {history.map((record, index) => (
            <AccordionItem value={record.id} key={record.id} className="border rounded-lg">
              <AccordionTrigger className="px-5">
                <div className="flex justify-between w-full">
                  <div>
                    <div className="font-semibold">{record.query_doc_name}</div>
                    <div className="text-xs text-slate-500">
                      {formatDate(record.created_at)}
                    </div>
                  </div>
                  <div className="text-sm text-slate-600">
                    {record.matched_templates.length} results
                  </div>
                </div>
              </AccordionTrigger>

              <AccordionContent className="px-5 pb-5">
                {record.matched_templates.map((match, idx) => (
                  <Card key={idx} className="p-4 mb-3">

                    {/* HEADER */}
                    <div className="flex justify-between">
                      <h4 className="font-semibold">
                        #{idx + 1} {match.template_name}
                      </h4>
                      <strong>{(match.overall_score * 100).toFixed(0)}%</strong>
                    </div>

                    {/* CLASSIFICATION */}
                    <div className={`inline-block mt-2 px-3 py-1 rounded-full text-sm ${classificationColor(match.classification)}`}>
                      {match.classification}
                    </div>

                    {/* METRICS */}
                    <div className="grid grid-cols-3 gap-3 mt-3">
                      <Metric label="Text" value={match.text_similarity} />
                      <Metric label="Structure" value={match.structure_similarity} />
                      <Metric label="Layout" value={match.layout_similarity} />
                    </div>

                    {/* CONFIDENCE */}
                    <div className="mt-3">
                      <small>Confidence Score</small>
                      <Progress value={match.confidence * 100} />
                      <small>{(match.confidence * 100).toFixed(1)}%</small>
                    </div>

                    {/* FORGERY STATUS */}
                    <div className={`mt-3 p-2 rounded border ${riskColor(match.forgery_label)}`}>
                      <div className="flex items-center gap-2">
                        {match.forgery_label === 'HIGH' ? <AlertTriangle size={16}/> : <ShieldCheck size={16}/>}
                        <strong>Forgery Risk: {match.forgery_label}</strong>
                      </div>
                      <div className="text-sm">
                        Fraud Probability: {(match.fraud_confidence * 100).toFixed(1)}%
                      </div>
                    </div>

                    {/* DUPLICATE FLAG */}
                    {match.is_duplicate && (
                      <div className="mt-2 text-blue-700 text-sm flex items-center gap-1">
                        <Copy size={14}/> Duplicate detected
                      </div>
                    )}

                    {/* RED FLAGS */}
                    {match.red_flags?.length > 0 && (
                      <div className="mt-3 text-red-600">
                        <strong>Red Flags</strong>
                        <ul className="list-disc ml-5 text-sm">
                          {match.red_flags.map((f,i) => <li key={i}>{f}</li>)}
                        </ul>
                      </div>
                    )}

                    {/* AI ANALYSIS */}
                    <div className="bg-slate-50 mt-3 p-2 rounded text-sm">
                      {match.analysis}
                    </div>

                  </Card>
                ))}
              </AccordionContent>
            </AccordionItem>
          ))}
        </Accordion>
      )}
    </div>
  );
};

const Metric = ({ label, value }) => (
  <div className="bg-slate-50 p-2 rounded text-center">
    <small>{label}</small>
    <div className="font-bold">{(value * 100).toFixed(0)}%</div>
    <Progress value={value * 100} className="h-1"/>
  </div>
);

export default MatchHistory;
