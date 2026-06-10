"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { CheckCircle, AlertCircle, Clock, FileText, Upload } from "lucide-react";
import { useDropzone } from "react-dropzone";
import { useToast } from "@/components/ui/use-toast";

interface ComplianceItem {
  id: string;
  title: string;
  dueDate: string;
  status: "completed" | "pending" | "overdue" | "in_progress";
  type: "gst" | "tax" | "tds" | "audit" | "roc";
  progress: number;
}

const complianceItems: ComplianceItem[] = [
  { id: "1", title: "GSTR-1 Filing (June 2024)", dueDate: "2024-07-11", status: "pending", type: "gst", progress: 75 },
  { id: "2", title: "GSTR-3B Filing (June 2024)", dueDate: "2024-07-20", status: "pending", type: "gst", progress: 60 },
  { id: "3", title: "TDS Return Q1", dueDate: "2024-07-31", status: "in_progress", type: "tds", progress: 40 },
  { id: "4", title: "Tax Audit Preparation", dueDate: "2024-09-30", status: "pending", type: "audit", progress: 10 },
  { id: "5", title: "ROC Annual Filing", dueDate: "2024-10-30", status: "completed", type: "roc", progress: 100 },
];

export function ComplianceAutopilot() {
  const { toast } = useToast();
  const [uploading, setUploading] = useState(false);

  const onDrop = async (acceptedFiles: File[]) => {
    setUploading(true);
    try {
      // Upload to OCR pipeline
      const formData = new FormData();
      acceptedFiles.forEach((file) => formData.append("files", file));

      const response = await fetch("/api/v1/ocr/process", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) throw new Error("Upload failed");

      toast({
        title: "Documents uploaded",
        description: `${acceptedFiles.length} files sent for OCR processing`,
      });
    } catch (error) {
      toast({
        title: "Upload failed",
        description: "Please try again",
        variant: "destructive",
      });
    } finally {
      setUploading(false);
    }
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'image/*': ['.png', '.jpg', '.jpeg'],
    },
  });

  const getStatusIcon = (status: ComplianceItem["status"]) => {
    switch (status) {
      case "completed":
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case "overdue":
        return <AlertCircle className="h-5 w-5 text-red-500" />;
      case "in_progress":
        return <Clock className="h-5 w-5 text-blue-500" />;
      default:
        return <Clock className="h-5 w-5 text-yellow-500" />;
    }
  };

  const getStatusBadge = (status: ComplianceItem["status"]) => {
    const variants = {
      completed: "bg-green-100 text-green-800",
      pending: "bg-yellow-100 text-yellow-800",
      overdue: "bg-red-100 text-red-800",
      in_progress: "bg-blue-100 text-blue-800",
    };
    return variants[status];
  };

  return (
    <div className="space-y-6">
      {/* Upload Zone */}
      <Card>
        <CardHeader>
          <CardTitle>Document Upload</CardTitle>
        </CardHeader>
        <CardContent>
          <div
            {...getRootProps()}
            className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
              isDragActive ? "border-blue-500 bg-blue-50" : "border-gray-300 hover:border-gray-400"
            }`}
          >
            <input {...getInputProps()} />
            <Upload className="mx-auto h-12 w-12 text-gray-400" />
            <p className="mt-2 text-sm text-gray-600">
              {isDragActive ? "Drop files here" : "Drag & drop invoices, bank statements, or receipts"}
            </p>
            <p className="text-xs text-gray-400 mt-1">PDF, PNG, JPG up to 50MB</p>
          </div>
          {uploading && (
            <div className="mt-4">
              <Progress value={45} className="h-2" />
              <p className="text-sm text-gray-500 mt-1">Processing documents...</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Compliance Checklist */}
      <Card>
        <CardHeader>
          <CardTitle>Compliance Checklist</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {complianceItems.map((item) => (
              <div key={item.id} className="flex items-center justify-between p-4 border rounded-lg">
                <div className="flex items-center space-x-4">
                  {getStatusIcon(item.status)}
                  <div>
                    <p className="font-medium text-gray-900">{item.title}</p>
                    <p className="text-sm text-gray-500">Due: {item.dueDate}</p>
                  </div>
                </div>
                <div className="flex items-center space-x-4">
                  <div className="w-32">
                    <Progress value={item.progress} className="h-2" />
                  </div>
                  <Badge className={getStatusBadge(item.status)}>
                    {item.status.replace("_", " ")}
                  </Badge>
                  <Button variant="outline" size="sm">
                    <FileText className="h-4 w-4 mr-1" />
                    View
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* 1-Click CMA */}
      <Card>
        <CardHeader>
          <CardTitle>Credit Monitoring Arrangement (CMA)</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Generate bank-standard CMA report</p>
              <p className="text-xs text-gray-400 mt-1">Period: FY 2023-24</p>
            </div>
            <Button>
              <FileText className="h-4 w-4 mr-2" />
              Generate CMA Report
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
