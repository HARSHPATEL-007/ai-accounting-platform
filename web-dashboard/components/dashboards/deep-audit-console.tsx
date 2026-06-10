"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Search, FileText, AlertTriangle, CheckCircle, MessageSquare } from "lucide-react";
import ReactMarkdown from "react-markdown";

interface AuditEntry {
  id: string;
  timestamp: string;
  user: string;
  action: string;
  resource: string;
  status: "success" | "warning" | "error";
  details: string;
}

const sampleEntries: AuditEntry[] = [
  { id: "1", timestamp: "2024-06-15 10:30:00", user: "ca@largecorp.in", action: "AI_QUERY", resource: "ESG Report 2023", status: "success", details: "Retrieved 15 pages from sustainability report" },
  { id: "2", timestamp: "2024-06-15 11:15:00", user: "auditor@largecorp.in", action: "ANOMALY_DETECTED", resource: "Ledger Q2", status: "warning", details: "Duplicate invoice detected: INV-2024-0042" },
  { id: "3", timestamp: "2024-06-15 14:00:00", user: "admin@largecorp.in", action: "M&A_SIMULATION", resource: "Acquisition Model", status: "success", details: "Scenario analysis completed: 3 outcomes generated" },
];

export function DeepAuditConsole() {
  const [query, setQuery] = useState("");
  const [chatResponse, setChatResponse] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleChatQuery = async () => {
    if (!query.trim()) return;
    setIsLoading(true);

    // In production: call AI Orchestrator with audit-specific context
    setTimeout(() => {
      setChatResponse(`**Analysis of Q2 Ledger:**\n\nI found 3 anomalies in the Q2 ledger data:\n\n1. **Duplicate Invoice**: INV-2024-0042 appears twice (₹45,000 each)\n2. **GST Mismatch**: Vendor GSTIN 27AABCM5678B1Z3 has inconsistent HSN codes\n3. **Timing Anomaly**: 12 transactions posted outside business hours (2:00-5:00 AM)\n\n*Confidence: High | Sources: Ledger Q2, Invoice Registry*\n\n---\n\n**Disclaimer:** This AI-generated response is for informational purposes only and does not constitute professional financial or legal advice. Please consult a licensed Chartered Accountant before making decisions.`);
      setIsLoading(false);
    }, 2000);
  };

  return (
    <div className="space-y-6">
      {/* Chat with Data */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <MessageSquare className="h-5 w-5" />
            <span>Chat with Your Data</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex space-x-2">
            <Input
              placeholder="Ask about ESG reports, transfer pricing, or audit findings..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="flex-1"
            />
            <Button onClick={handleChatQuery} disabled={isLoading}>
              <Search className="h-4 w-4 mr-2" />
              {isLoading ? "Analyzing..." : "Analyze"}
            </Button>
          </div>

          {chatResponse && (
            <div className="mt-4 p-4 bg-gray-50 rounded-lg prose prose-sm max-w-none">
              <ReactMarkdown>{chatResponse}</ReactMarkdown>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Audit Trail */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <FileText className="h-5 w-5" />
            <span>Immutable Audit Trail</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ScrollArea className="h-[400px]">
            <div className="space-y-3">
              {sampleEntries.map((entry) => (
                <div key={entry.id} className="flex items-start space-x-3 p-3 border rounded-lg">
                  {entry.status === "success" ? (
                    <CheckCircle className="h-5 w-5 text-green-500 mt-0.5" />
                  ) : entry.status === "warning" ? (
                    <AlertTriangle className="h-5 w-5 text-yellow-500 mt-0.5" />
                  ) : (
                    <AlertTriangle className="h-5 w-5 text-red-500 mt-0.5" />
                  )}
                  <div className="flex-1">
                    <div className="flex items-center justify-between">
                      <p className="font-medium text-sm">{entry.action}</p>
                      <Badge variant={entry.status === "success" ? "default" : "destructive"}>
                        {entry.status}
                      </Badge>
                    </div>
                    <p className="text-xs text-gray-500 mt-1">{entry.user} • {entry.timestamp}</p>
                    <p className="text-sm text-gray-700 mt-1">{entry.details}</p>
                    <p className="text-xs text-gray-400 mt-1">Resource: {entry.resource}</p>
                  </div>
                </div>
              ))}
            </div>
          </ScrollArea>
        </CardContent>
      </Card>
    </div>
  );
}
