"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { CheckCircle, Circle, Clock, Globe, FileText } from "lucide-react";

interface ComplianceStep {
  id: string;
  title: string;
  description: string;
  status: "completed" | "in_progress" | "pending";
  estimatedDays: number;
  documents: string[];
}

const subsidiarySteps: ComplianceStep[] = [
  {
    id: "1",
    title: "Reserve Company Name",
    description: "File RUN (Reserve Unique Name) with MCA",
    status: "completed",
    estimatedDays: 2,
    documents: ["Board Resolution", "Name Approval Request"],
  },
  {
    id: "2",
    title: "Obtain DIN for Directors",
    description: "Digital Signature and Director Identification Number",
    status: "completed",
    estimatedDays: 5,
    documents: ["Passport Copy", "Address Proof", "Photograph"],
  },
  {
    id: "3",
    title: "FEMA Compliance",
    description: "File FC-GPR with RBI for foreign investment",
    status: "in_progress",
    estimatedDays: 30,
    documents: ["FC-GPR Form", "Share Allotment Certificate", "FIRC"],
  },
  {
    id: "4",
    title: "GST Registration",
    description: "Obtain GSTIN for Indian operations",
    status: "pending",
    estimatedDays: 7,
    documents: ["Incorporation Certificate", "Address Proof", "Bank Statement"],
  },
  {
    id: "5",
    title: "DTAA Advisory",
    description: "Structure taxation under India-Singapore DTAA",
    status: "pending",
    estimatedDays: 14,
    documents: ["Tax Residency Certificate", "Parent Company Financials"],
  },
];

const dtaaArticles = [
  { article: "Article 5", title: "Permanent Establishment", relevance: "High", summary: "Defines when a foreign company has a taxable presence in India" },
  { article: "Article 10", title: "Dividends", relevance: "High", summary: "Maximum 15% withholding tax on dividends if shareholder holds <10% capital" },
  { article: "Article 12", title: "Royalties & Fees for Technical Services", relevance: "Medium", summary: "10% withholding tax on FTS, reduced from standard 20% under domestic law" },
  { article: "Article 13", title: "Capital Gains", relevance: "High", summary: "Gains from alienation of shares taxed only in resident country" },
];

export function CrossBorderNavigator() {
  const completedSteps = subsidiarySteps.filter((s) => s.status === "completed").length;
  const progress = (completedSteps / subsidiarySteps.length) * 100;

  return (
    <div className="space-y-6">
      {/* Progress Overview */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Globe className="h-5 w-5" />
            <span>Subsidiary Setup Progress</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex justify-between text-sm">
              <span>{completedSteps} of {subsidiarySteps.length} steps completed</span>
              <span>{Math.round(progress)}%</span>
            </div>
            <Progress value={progress} className="h-2" />
          </div>
        </CardContent>
      </Card>

      {/* Step-by-Step Workflow */}
      <Card>
        <CardHeader>
          <CardTitle>Compliance Timeline</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-6">
            {subsidiarySteps.map((step, index) => (
              <div key={step.id} className="relative pl-8">
                {index < subsidiarySteps.length - 1 && (
                  <div className="absolute left-3 top-8 bottom-0 w-0.5 bg-gray-200" />
                )}
                <div className="absolute left-0 top-1">
                  {step.status === "completed" ? (
                    <CheckCircle className="h-6 w-6 text-green-500" />
                  ) : step.status === "in_progress" ? (
                    <Clock className="h-6 w-6 text-blue-500" />
                  ) : (
                    <Circle className="h-6 w-6 text-gray-300" />
                  )}
                </div>
                <div className="border rounded-lg p-4">
                  <div className="flex items-center justify-between">
                    <h3 className="font-medium">{step.title}</h3>
                    <Badge variant={step.status === "completed" ? "default" : step.status === "in_progress" ? "secondary" : "outline"}>
                      {step.status.replace("_", " ")}
                    </Badge>
                  </div>
                  <p className="text-sm text-gray-500 mt-1">{step.description}</p>
                  <p className="text-xs text-gray-400 mt-2">Estimated: {step.estimatedDays} days</p>
                  <div className="mt-3 flex flex-wrap gap-2">
                    {step.documents.map((doc) => (
                      <Badge key={doc} variant="outline" className="text-xs">
                        <FileText className="h-3 w-3 mr-1" />
                        {doc}
                      </Badge>
                    ))}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* DTAA Articles */}
      <Card>
        <CardHeader>
          <CardTitle>India-Singapore DTAA Articles</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {dtaaArticles.map((article) => (
              <div key={article.article} className="border rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <h3 className="font-medium">{article.article}: {article.title}</h3>
                  <Badge variant={article.relevance === "High" ? "default" : "secondary"}>
                    {article.relevance} Relevance
                  </Badge>
                </div>
                <p className="text-sm text-gray-600 mt-2">{article.summary}</p>
                <Button variant="link" className="p-0 h-auto mt-2 text-sm">
                  View full text →
                </Button>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
